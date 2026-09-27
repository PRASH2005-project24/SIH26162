"""
Copernicus Data Space Ecosystem (CDSE) / Sentinel Hub Sentinel-2 Service.
Provides on-demand optical true-color imagery previews (10m L2A) with disk caching and OAuth2 token management.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx

from backend.config import Config

logger = logging.getLogger(__name__)

TOKEN_ENDPOINT = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_ENDPOINT = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Evalscript for True-Color RGB using Sentinel-2 L2A Bands 4 (Red), 3 (Green), 2 (Blue) with gain boost
TRUE_COLOR_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ['B04', 'B03', 'B02'],
    output: { bands: 3 }
  };
}
function evaluatePixel(sample) {
  let gain = 3.2;
  return [
    Math.min(1.0, Math.max(0.0, sample.B04 * gain)),
    Math.min(1.0, Math.max(0.0, sample.B03 * gain)),
    Math.min(1.0, Math.max(0.0, sample.B02 * gain))
  ];
}
"""

MIN_VALID_IMAGE_SIZE_BYTES = 7000  # Below 7KB is typically an empty/solid black tile


class SentinelService:
    """Service to fetch and cache Sentinel-2 optical preview images."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # Setup local disk cache directory
        storage_base = Path(self.config.STORAGE_LOCAL_PATH)
        self.cache_dir = storage_base / "sentinel_previews"
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create preview cache dir: {e}")

    @property
    def is_configured(self) -> bool:
        """Check if CDSE credentials are configured."""
        return bool(self.config.CDSE_CLIENT_ID and self.config.CDSE_CLIENT_SECRET)

    async def get_access_token(self) -> Optional[str]:
        """Fetch or reuse cached CDSE OAuth2 Bearer token."""
        if not self.is_configured:
            logger.debug("CDSE credentials not configured.")
            return None

        # Reuse valid token if not expired (with 60s safety buffer)
        if self._access_token and time.time() < (self._token_expires_at - 60):
            return self._access_token

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.config.CDSE_CLIENT_ID,
                    "client_secret": self.config.CDSE_CLIENT_SECRET,
                }
                resp = await client.post(TOKEN_ENDPOINT, data=data)
                if resp.status_code == 200:
                    token_data = resp.json()
                    self._access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 1800)
                    self._token_expires_at = time.time() + float(expires_in)
                    logger.info(f"Obtained new CDSE access token, valid for {expires_in}s")
                    return self._access_token
                else:
                    logger.error(f"Failed to fetch CDSE token: {resp.status_code} {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"Error requesting CDSE token: {e}", exc_info=True)
            return None

    def _get_cached_image(self, event_id: str) -> Optional[bytes]:
        """Check if image exists in disk cache and is not an empty/black tile."""
        cache_file = self.cache_dir / f"{event_id}.jpg"
        if cache_file.exists():
            size = cache_file.stat().st_size
            if size >= MIN_VALID_IMAGE_SIZE_BYTES:
                try:
                    return cache_file.read_bytes()
                except Exception as e:
                    logger.warning(f"Failed to read cached image {cache_file}: {e}")
            else:
                # Remove corrupted / solid-black tile so it is re-fetched properly
                try:
                    cache_file.unlink(missing_ok=True)
                except Exception:
                    pass
        return None

    def _save_to_cache(self, event_id: str, data: bytes) -> None:
        """Save image bytes to disk cache if it is a valid image."""
        if len(data) < MIN_VALID_IMAGE_SIZE_BYTES:
            return  # Do not cache empty/black tiles

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / f"{event_id}.jpg"
            cache_file.write_bytes(data)
            logger.info(f"Cached Sentinel-2 preview for event {event_id} ({len(data)} bytes)")
        except Exception as e:
            logger.warning(f"Failed to cache preview for event {event_id}: {e}")

    async def _execute_process_request(self, token: str, payload: dict) -> Optional[bytes]:
        """Execute single Process API request to Sentinel Hub."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "image/jpeg"
                }
                resp = await client.post(PROCESS_ENDPOINT, json=payload, headers=headers)
                if resp.status_code == 200 and len(resp.content) >= MIN_VALID_IMAGE_SIZE_BYTES:
                    return resp.content
                elif resp.status_code == 400 and "cloud" in resp.text.lower():
                    # Relax cloud coverage if rejected
                    payload["input"]["data"][0]["dataFilter"]["maxCloudCoverage"] = 80
                    resp2 = await client.post(PROCESS_ENDPOINT, json=payload, headers=headers)
                    if resp2.status_code == 200 and len(resp2.content) >= MIN_VALID_IMAGE_SIZE_BYTES:
                        return resp2.content
                return None
        except Exception as e:
            logger.warning(f"Process API request failed: {e}")
            return None

    async def get_preview_image(
        self,
        event_id: str,
        lat: float,
        lon: float,
        acq_time: Optional[datetime | str] = None,
        bbox_delta: float = 0.02,
    ) -> Optional[bytes]:
        """
        Fetch a Sentinel-2 true color preview image for a location.
        First checks local cache, then queries Copernicus Sentinel Hub Process API.
        """
        # 1. Check disk cache
        cached = self._get_cached_image(event_id)
        if cached:
            return cached

        # 2. Check credentials and get token
        token = await self.get_access_token()
        if not token:
            return None

        # 3. Compute bounding box around target coordinate (~4.4 km width)
        min_lon = lon - bbox_delta
        min_lat = lat - bbox_delta
        max_lon = lon + bbox_delta
        max_lat = lat + bbox_delta

        # 4. Compute date range:
        # Sentinel-2 archive is up to the current real year (2024).
        # Clamping future simulated years (e.g. 2026) to 2024 to map to actual satellite orbits.
        target_dt: datetime
        if isinstance(acq_time, str):
            try:
                target_dt = datetime.fromisoformat(acq_time.replace("Z", "+00:00"))
            except Exception:
                target_dt = datetime.now(timezone.utc)
        elif isinstance(acq_time, datetime):
            target_dt = acq_time if acq_time.tzinfo else acq_time.replace(tzinfo=timezone.utc)
        else:
            target_dt = datetime.now(timezone.utc)

        # Map future years (e.g. 2026) to 2024 real-world imagery archive
        if target_dt.year > 2024:
            target_dt = target_dt.replace(year=2024)

        from_date = (target_dt - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
        to_date = (target_dt + timedelta(days=15)).strftime("%Y-%m-%dT23:59:59Z")

        # 5. Build primary request payload
        payload = {
            "input": {
                "bounds": {
                    "bbox": [min_lon, min_lat, max_lon, max_lat]
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": from_date,
                                "to": to_date
                            },
                            "maxCloudCoverage": 50
                        }
                    }
                ]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {"type": "image/jpeg"}
                    }
                ]
            },
            "evalscript": TRUE_COLOR_EVALSCRIPT
        }

        # 6. First attempt: target window
        image_bytes = await self._execute_process_request(token, payload)

        # 7. Fallback attempt: if no clear pass or black tile, query broad clear-season window (May-July 2024)
        if not image_bytes or len(image_bytes) < MIN_VALID_IMAGE_SIZE_BYTES:
            logger.info(f"Retrying Sentinel-2 preview for {event_id} with clear-sky season window...")
            payload["input"]["data"][0]["dataFilter"]["timeRange"] = {
                "from": "2024-04-15T00:00:00Z",
                "to": "2024-07-15T23:59:59Z"
            }
            payload["input"]["data"][0]["dataFilter"]["maxCloudCoverage"] = 60
            image_bytes = await self._execute_process_request(token, payload)

        # 8. Cache and return
        if image_bytes and len(image_bytes) >= MIN_VALID_IMAGE_SIZE_BYTES:
            self._save_to_cache(event_id, image_bytes)
            return image_bytes

        return None


# Global singleton instance
_sentinel_service: Optional[SentinelService] = None

def get_sentinel_service() -> SentinelService:
    """Get or create singleton SentinelService."""
    global _sentinel_service
    if _sentinel_service is None:
        _sentinel_service = SentinelService()
    return _sentinel_service
