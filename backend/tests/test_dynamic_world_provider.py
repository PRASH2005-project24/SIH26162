import asyncio
from types import SimpleNamespace

import pytest

from backend.gis.dynamic_world_provider import DynamicWorldProvider


@pytest.fixture
def provider():
    return object.__new__(DynamicWorldProvider)


def test_parse_complete_dynamic_world_sample(provider):
    sample = {
        "label": [6],
        "water": [0.02],
        "trees": [0.05],
        "grass": [0.08],
        "flooded_vegetation": [0.01],
        "crops": [0.03],
        "shrub_and_scrub": [0.04],
        "built": [0.68],
        "bare": [0.07],
        "snow_and_ice": [0.02],
    }

    label, probabilities = provider._parse_dw_results(sample)

    assert label == "built"
    assert len(probabilities) == 9
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert provider._has_usable_land_cover({
        "land_cover_label": label,
        "class_probabilities": probabilities,
    })


@pytest.mark.parametrize(
    "sample",
    [
        {},
        {"water": [0.2]},
        {"label": [6], "water": [0.2]},
        {"label": [99], "water": [0.2]},
    ],
)
def test_parse_rejects_incomplete_or_invalid_samples(provider, sample):
    assert provider._parse_dw_results(sample) == (None, {})


def test_valid_cache_hit_is_not_reported_as_fresh_live(provider):
    probabilities = {
        "water": 1 / 9,
        "trees": 1 / 9,
        "grass": 1 / 9,
        "flooded_vegetation": 1 / 9,
        "crops": 1 / 9,
        "shrub_scrub": 1 / 9,
        "built": 1 / 9,
        "bare": 1 / 9,
        "snow_ice": 1 / 9,
    }
    provider.db = object()
    provider.config = SimpleNamespace(DEMO_MODE=False)

    async def get_cached_result(cache_key, query_type):
        return {
            "land_cover_label": "built",
            "class_probabilities": probabilities,
            "coverage_state": "live",
        }

    provider._get_cache = get_cached_result
    result = asyncio.run(
        provider.get_land_cover(18.52, 73.85, "2026-07-14T10:30:00Z")
    )

    assert result["coverage_state"] == "cached"
    assert result["source_coverage_state"] == "live"