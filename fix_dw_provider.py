#!/usr/bin/env python3
"""
Fix for Dynamic World provider - correct Earth Engine sampling method
"""

# Let's look at the correct way to sample a point in Earth Engine
# Based on Earth Engine documentation, we should use sample() or reduceRegion()

fix_content = '''
    async def _query_dynamic_world(
        self,
        event_lat: float,
        event_lon: float,
        acquisition_date: str,
        buffer_km: float = 0.5
    ) -> Dict[str, Any]:
        """
        Query Dynamic World dataset via Earth Engine.
        """
        import ee

        try:
            # Parse acquisition date
            acq_dt = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))

            # Create point geometry
            point = ee.Geometry.Point([event_lon, event_lat])

            # Buffer for analysis
            buffer_m = buffer_km * 1000
            buffered_point = point.buffer(buffer_m)

            # Query Dynamic World
            dw = ee.ImageCollection(DYNAMIC_WORLD_DATASET)

            # Filter by date (within 30 days of acquisition)
            start_date = (acq_dt - timedelta(days=15)).strftime("%Y-%m-%d")
            end_date = (acq_dt + timedelta(days=15)).strftime("%Y-%m-%d")

            dw_filtered = (
                dw
                .filterDate(start_date, end_date)
                .filterBounds(buffered_point)
                .first()
            )

            if dw_filtered is None:
                logger.warning(
                    f"No Dynamic World data available for {event_lat},{event_lon} "
                    f"near {acquisition_date}"
                )
                return {
                    "source": "google_dynamic_world",
                    "land_cover_label": None,
                    "class_probabilities": {},
                    "coverage_state": "coverage_unknown",
                    "provider_version": "1.0.0"
                }

            # Sample classification at point using reduceRegion (correct method)
            # We'll sample the classification band and probability bands
            sample = dw_filtered.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=10,  # 10m scale
                bestEffort=True
            )

            # Extract results
            results = sample.getInfo()

            # Parse results and extract dominant class
            label, probs = self._parse_dw_results(results)

            # Get image date
            image_date = ee.Image(dw_filtered).date().format('YYYY-MM-dd').getInfo()

            return {
                "source": "google_dynamic_world",
                "land_cover_label": label,
                "class_probabilities": probs,
                "image_date": image_date,
                "acquisition_date": acquisition_date,
                "query_date": datetime.utcnow().isoformat(),
                "coverage_state": "live",
                "provider_version": "1.0.0",
                "dataset_id": DYNAMIC_WORLD_DATASET
            }

        except Exception as e:
            logger.error(f"Error in Dynamic World query: {e}")
            raise
'''

print("Fixed _query_dynamic_world method:")
print(fix_content)

# Also need to fix _parse_dw_results to handle the new format
print("\nThe _parse_dw_results method may also need adjustment based on the new format.")