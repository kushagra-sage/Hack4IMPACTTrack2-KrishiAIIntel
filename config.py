"""
Configuration settings for Invoice Information Extractor API
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "utils" / "models"

# Model paths
YOLO_MODEL_PATH = MODELS_DIR / "best.pt"

# VLM Model Configuration
VLM_MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"

# Quantization settings
QUANTIZATION_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": True
}

# Image processing settings
MAX_IMAGE_SIZE = 800  # Maximum dimension for resizing

# Detection thresholds
YOLO_CONFIDENCE_THRESHOLD = 0.25

# Validation ranges
HP_VALID_RANGE = (20, 120)
ASSET_COST_VALID_RANGE = (100_000, 3_000_000)

# Cost calculation
COST_PER_GPU_HOUR = 0.6  # USD

# API settings
API_TITLE = "Invoice Information Extractor API"
API_DESCRIPTION = """
Extract structured information from Indian tractor invoices using AI.

**Features:**
- Extracts dealer name, model name, horse power, and asset cost
- Detects signatures and stamps with bounding boxes
- Provides confidence scores and cost estimates
"""
API_VERSION = "1.0.0"

# ─── Groq LLM Configuration ────────────────────────────────────────────────
GROQ_MODEL = "llama3-70b-8192"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT_SECONDS = 10
