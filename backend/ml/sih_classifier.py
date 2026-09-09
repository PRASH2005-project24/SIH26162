"""
SIH Classification Post-Processing Module

Maps frozen Stage 2 model's 3-class output to 5 SIH operational categories:
- Industrial Fire
- Wildfire/Natural Fire
- Agricultural Fire
- Persistent Thermal Source
- Unknown/Other

Applies correct priority:
1. Persistent Thermal Source (based on persistence calculation)
2. Valid high-confidence ML source (mapped from 3 classes)
3. Unknown/Other (low confidence or ambiguous cases)

Preserves original ML probabilities for the 3 classes only.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.api.events import PersistenceResponse

logger = logging.getLogger(__name__)

# Mapping from frozen model classes to SIH categories (first three)
# Based on verification document: need to confirm label ordering from training
MODEL_TO_SIH_MAPPING = {
    "industrial": "Industrial Fire",
    "agricultural": "Agricultural Fire",
    "wildfire": "Wildfire / Natural Fire"
}

# Reverse mapping for convenience
SIH_TO_MODEL_MAPPING = {v: k for k, v in MODEL_TO_SIH_MAPPING.items()}

def map_to_sih_category(
    ml_prediction: Dict[str, Any],
    persistence_info: Optional["PersistenceResponse"] = None,
    low_confidence_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Map frozen model's 3-class prediction to 5 SIH categories.

    Args:
        ml_prediction: Dictionary containing:
            - category: str (one of "industrial", "agricultural", "wildfire")
            - confidence: float (0-1)
            - probabilities: Dict[str, float] (3-class probabilities)
            - model_type: str (optional)
        persistence_info: PersistenceResponse object (optional)
        low_confidence_threshold: Threshold below which prediction is considered uncertain

    Returns:
        Dictionary with SIH classification:
            - sih_category: str (one of 5 SIH categories)
            - sih_confidence: float (confidence in SIH category)
            - ml_category: str (original ML category)
            - ml_confidence: float (original ML confidence)
            - ml_probabilities: Dict[str, float] (original 3-class probabilities)
            - is_persistent: bool (whether event is persistent)
    """
    # Extract ML prediction components
    ml_category = ml_prediction.get("category", "unknown")
    ml_confidence = ml_prediction.get("confidence", 0.0)
    ml_probabilities = ml_prediction.get("probabilities", {})
    model_type = ml_prediction.get("model_type", "Unknown")

    # Determine if event is persistent
    is_persistent = False
    if persistence_info:
        is_persistent = persistence_info.is_persistent

    # Initialize result
    result = {
        "sih_category": "Unknown / Other",  # Default
        "sih_confidence": 0.0,
        "ml_category": ml_category,
        "ml_confidence": ml_confidence,
        "ml_probabilities": ml_probabilities,
        "model_type": model_type,
        "is_persistent": is_persistent
    }

    # Priority 1: Persistent Thermal Source
    if is_persistent:
        result["sih_category"] = "Persistent Thermal Source"
        # For persistent sources, confidence combines ML confidence with persistence certainty
        # We'll use ML confidence as the base, but could be adjusted based on persistence strength
        result["sih_confidence"] = ml_confidence
        return result

    # Priority 2: Map ML category to SIH category (if confidence is sufficient)
    if ml_confidence >= low_confidence_threshold and ml_category in MODEL_TO_SIH_MAPPING:
        result["sih_category"] = MODEL_TO_SIH_MAPPING[ml_category]
        result["sih_confidence"] = ml_confidence
        return result

    # Priority 3: Unknown/Other (default case)
    # This covers:
    # - Low confidence predictions (< low_confidence_threshold)
    # - Persistent sources (handled above)
    # - Any other edge cases
    result["sih_category"] = "Unknown / Other"
    # For Unknown/Other, we can compute confidence as 1 - max_probability
    # or use a fixed low value. Using 1 - max_probability makes sense.
    if ml_probabilities:
        max_prob = max(ml_probabilities.values())
        result["sih_confidence"] = 1.0 - max_prob
    else:
        result["sih_confidence"] = 1.0 - ml_confidence if ml_confidence > 0 else 0.5

    return result

def get_sih_category_labels() -> list:
    """
    Get the list of SIH category labels in order.

    Returns:
        List of SIH category strings
    """
    return [
        "Industrial Fire",
        "Wildfire / Natural Fire",
        "Agricultural Fire",
        "Persistent Thermal Source",
        "Unknown / Other"
    ]

def is_valid_sih_category(category: str) -> bool:
    """
    Check if a string is a valid SIH category.

    Args:
        category: Category string to check

    Returns:
        True if valid SIH category, False otherwise
    """
    return category in get_sih_category_labels()