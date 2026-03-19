"""
Normalization Layer for Invoice Fields
Cleans, deduplicates, and fuzzy-matches extracted invoice text
to known tractor brands and model names.
"""

import re
from typing import Dict, Optional

try:
    from rapidfuzz import fuzz, process as rf_process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    print("⚠️  rapidfuzz not installed — fuzzy matching disabled. Install with: pip install rapidfuzz")


# ─── Known brand & model reference lists ────────────────────────────────────
KNOWN_BRANDS = [
    "John Deere", "Mahindra", "Eicher", "TAFE", "Sonalika",
    "Swaraj", "New Holland", "Kubota", "Escorts", "Massey Ferguson",
    "Preet", "Force Motors", "Indo Farm", "ACE", "Captain",
    "Farmtrac", "Powertrac", "Digitrac", "VST Tillers",
]

KNOWN_MODELS = [
    # Mahindra
    "Mahindra 575 DI", "Mahindra 475 DI", "Mahindra Arjun NOVO 605 DI-i",
    "Mahindra JIVO 245 DI", "Mahindra 265 DI", "Mahindra 585 DI",
    "Mahindra Arjun 555 DI", "Mahindra Yuvo 415 DI",
    # John Deere
    "John Deere 5310", "John Deere 5210", "John Deere 5050 D",
    "John Deere 5405", "John Deere 5075E",
    # Sonalika
    "Sonalika DI 750 III", "Sonalika DI 745 III", "Sonalika GT 22",
    "Sonalika DI 60", "Sonalika Tiger",
    # Swaraj
    "Swaraj 744 FE", "Swaraj 855 FE", "Swaraj 963 FE",
    "Swaraj 735 FE", "Swaraj 843 XM",
    # Eicher
    "Eicher 242", "Eicher 380", "Eicher 557",
    "Eicher 548", "Eicher 551",
    # New Holland
    "New Holland 3630 TX Plus", "New Holland 3230 NX",
    # TAFE
    "TAFE 45 DI", "TAFE 5900",
    # Massey Ferguson
    "Massey Ferguson 1035 DI", "Massey Ferguson 7250 DI",
    # Escorts / Farmtrac / Powertrac
    "Farmtrac 60 Powermaxx", "Powertrac 439 Plus",
    "Escorts 335",
    # Kubota
    "Kubota MU4501",
]

# Common OCR error corrections
OCR_CORRECTIONS: Dict[str, str] = {
    "jhon": "john",
    "deer": "deere",
    "dere": "deere",
    "mahindre": "mahindra",
    "mahindrs": "mahindra",
    "mahindr": "mahindra",
    "eichar": "eicher",
    "eichre": "eicher",
    "sonalike": "sonalika",
    "sonalilka": "sonalika",
    "swarai": "swaraj",
    "swraj": "swaraj",
    "tefe": "tafe",
    "massu": "massey",
    "fergusen": "ferguson",
    "farguson": "ferguson",
    "hollamd": "holland",
    "hollend": "holland",
    "kuboto": "kubota",
    "farmtrec": "farmtrac",
    "povertrac": "powertrac",
    "powrtrac": "powertrac",
    "escorte": "escorts",
}


def _clean_text(text: Optional[str]) -> Optional[str]:
    """Basic text cleanup: lowercase, strip, collapse whitespace, remove repeated words."""
    if not text:
        return None
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)

    # Remove consecutive duplicate words  ("john john" → "john")
    words = text.split()
    deduped = [words[0]] if words else []
    for w in words[1:]:
        if w != deduped[-1]:
            deduped.append(w)
    text = " ".join(deduped)

    return text if len(text) > 1 else None


def _apply_ocr_corrections(text: str) -> str:
    """Fix common OCR misreads at word level."""
    words = text.split()
    corrected = [OCR_CORRECTIONS.get(w, w) for w in words]
    return " ".join(corrected)


def _fuzzy_match_brand(text: str, threshold: int = 70) -> Optional[str]:
    """Return the best-matching known brand if score ≥ threshold."""
    if not HAS_RAPIDFUZZ or not text:
        return None
    result = rf_process.extractOne(text, [b.lower() for b in KNOWN_BRANDS], scorer=fuzz.token_sort_ratio)
    if result and result[1] >= threshold:
        idx = [b.lower() for b in KNOWN_BRANDS].index(result[0])
        return KNOWN_BRANDS[idx]
    return None


def _fuzzy_match_model(text: str, threshold: int = 65) -> Optional[str]:
    """Return the best-matching known model if score ≥ threshold."""
    if not HAS_RAPIDFUZZ or not text:
        return None
    result = rf_process.extractOne(text, [m.lower() for m in KNOWN_MODELS], scorer=fuzz.token_sort_ratio)
    if result and result[1] >= threshold:
        idx = [m.lower() for m in KNOWN_MODELS].index(result[0])
        return KNOWN_MODELS[idx]
    return None


def normalize_dealer_name(name: Optional[str]) -> Optional[str]:
    """Clean and correct a dealer name string."""
    cleaned = _clean_text(name)
    if not cleaned:
        return name  # Return original if nothing to clean
    corrected = _apply_ocr_corrections(cleaned)
    # Title-case the corrected string
    return corrected.title()


def normalize_model_name(model: Optional[str]) -> Optional[str]:
    """Clean, correct, and fuzzy-match a model name string."""
    cleaned = _clean_text(model)
    if not cleaned:
        return model
    corrected = _apply_ocr_corrections(cleaned)
    # Try fuzzy match to known models
    matched = _fuzzy_match_model(corrected)
    if matched:
        return matched
    return corrected.title()


def normalize_fields(fields: Dict) -> Dict:
    """
    Normalize extracted invoice fields in-place and return.
    Standardizes dealer_name and model_name.
    Leaves numeric fields (horse_power, asset_cost) untouched.
    """
    if not fields:
        return fields

    normalized = dict(fields)  # shallow copy

    if "dealer_name" in normalized and normalized["dealer_name"]:
        normalized["dealer_name"] = normalize_dealer_name(normalized["dealer_name"])

    if "model_name" in normalized and normalized["model_name"]:
        normalized["model_name"] = normalize_model_name(normalized["model_name"])

    return normalized
