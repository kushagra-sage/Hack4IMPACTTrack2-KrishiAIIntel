---
title: Tractor Invoice Information Extractor
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Invoice Information Extractor API

Extract structured information from Indian tractor invoices using AI-powered REST API.

## What It Does

Combines **YOLO** (signature/stamp detection) + **Qwen2.5-VL** (text extraction) to extract:
- Dealer name
- Model name  
- Horse power
- Asset cost
- Signature presence & location
- Stamp presence & location

## Architecture

### Production (Hugging Face Deployment)
- **FastAPI server** with REST endpoints
- **Models loaded on startup** and cached in memory
- **YOLO model** stored locally in `utils/models/best.pt`
- **Qwen2.5-VL** downloaded from Hugging Face on first run (not stored locally)

### Key Components
- `app.py` - FastAPI server with endpoints
- `model_manager.py` - Handles model loading and caching
- `inference.py` - Processing pipeline and validation
- `config.py` - Configuration settings
- `executable.py` - Legacy CLI interface (deprecated)

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:** Python 3.10+, CUDA GPU (8GB+ VRAM)

## Running the Server

### Local Development
```bash
python app.py
```

Server runs on `http://localhost:7860`

### Production (Hugging Face Spaces)
```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

## API Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true
}
```

### 2. Extract Single Invoice
```bash
POST /extract
```

**Parameters:**
- `file` (required): Image file (JPG, PNG, JPEG)
- `doc_id` (optional): Document identifier

**Example (cURL):**
```bash
curl -X POST "http://localhost:7860/extract" \
  -F "file=@invoice_001.png" \
  -F "doc_id=invoice_001"
```



**Response:**
```json
{
  "doc_id": "invoice_001",
  "fields": {
    "dealer_name": "ABC Tractors Pvt Ltd",
    "model_name": "Mahindra 575 DI",
    "horse_power": 50,
    "asset_cost": 525000,
    "signature": {"present": true, "bbox": [100, 200, 300, 250]},
    "stamp": {"present": true, "bbox": [400, 500, 500, 550]}
  },
  "confidence": 0.89,
  "processing_time_sec": 3.8,
  "cost_estimate_usd": 0.000528,
  "warnings": null
}
```

### 3. Extract Multiple Invoices (Batch)
```bash
POST /extract_batch
```

**Parameters:**
- `files` (required): Array of image files

## Output Format

Results saved to `sample_output/result.json`:

```json
{
  "doc_id": "invoice_001",
  "fields": {
    "dealer_name": "ABC Tractors Pvt Ltd",
    "model_name": "Mahindra 575 DI",
    "horse_power": 50,
    "asset_cost": 525000,
    "signature": {"present": true, "bbox": [100, 200, 300, 250]},
    "stamp": {"present": true, "bbox": [400, 500, 500, 550]}
  },
  "confidence": 0.89,
  "processing_time_sec": 3.8,
  "cost_estimate_usd": 0.000528
}
```


Range: 0.0 to 1.0 (higher is better)

## Cost Calculation

**Formula:**
```
cost_usd = (0.5 * processing_time_sec) / 3600
```

Assumes **$0.60 per GPU hour**

**Typical costs:**
- Per invoice: ~$0.002 

## Models

- **YOLO:** Signature/stamp detection (`best.pt`)
- **Qwen2.5-VL-7B:** Text extraction (4-bit quantized)

## GPU Requirements

- **Minimum:** 10 GB VRAM

## Project Structure

```
INVOICE_INFO_EXTRACTOR/
├── app.py                 # FastAPI server (main entry point)
├── model_manager.py       # Model loading and caching
├── inference.py           # Processing pipeline and validation
├── config.py              # Configuration settings
├── requirements.txt       
├── README.md             
├── executable.py          # Legacy CLI (deprecated)
├── utils/
│   └── models/
│       └── best.pt        # YOLO model (stored locally)
└── sample_output/
    └── result.json        # Sample output
```

## Performance

- **Processing time:** ~8 seconds per invoice
- **Cost per invoice:** ~$0.002 (GPU time)
- **GPU Memory:** 8GB minimum