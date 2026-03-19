"""
FastAPI Server for KrishiIntel AI
Provides REST API for invoice processing, decision support, and portfolio intelligence
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import BaseModel
import tempfile
import os
import shutil

from config import API_TITLE, API_DESCRIPTION, API_VERSION
from model_manager import model_manager
from inference import InferenceProcessor
from decision import generate_decision_support
from rag_engine import InvoiceKnowledgeBase
from utils.normalization import normalize_fields
from report_generator import generate_report_html

# ─── Request models for new endpoints ───────────────────────────────────────

class DecisionSupportRequest(BaseModel):
    asset_cost: float
    horse_power: Optional[float] = None
    model_name: Optional[str] = None

class ChatRequest(BaseModel):
    query: str

class ReportRequest(BaseModel):
    fields: dict
    decision_support: Optional[dict] = None
    doc_id: Optional[str] = "invoice"

# ─── RAG engine singleton ───────────────────────────────────────────────────
rag_engine = InvoiceKnowledgeBase()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - loads models on startup"""
    print("🚀 Starting KrishiIntel AI API...")
    print("=" * 60)
    
    # Load models on startup
    try:
        model_manager.load_models()
        print("=" * 60)
        print("✅ Extraction pipeline ready!")
    except Exception as e:
        print(f"⚠️  Model loading skipped (OK for dev): {str(e)}")
    
    # Initialize RAG engine (separate from model loading)
    try:
        rag_engine.initialize()
        print("✅ RAG engine ready!")
    except Exception as e:
        print(f"⚠️  RAG engine init skipped: {str(e)}")
    
    print("=" * 60)
    print("✅ API is ready to accept requests!")
    print("=" * 60)
    
    yield
    
    # Cleanup on shutdown
    print("🛑 Shutting down API...")


# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files if they exist
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    print(f"📂 Serving frontend from: {frontend_dist}")


@app.get("/")
async def root():
    """Root endpoint - Serve frontend or API information"""
    frontend_index = os.path.join(os.path.dirname(__file__), "frontend", "dist", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    
    # Fallback to API information
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "models_loaded": model_manager.is_loaded(),
        "endpoints": {
            "health": "/health",
            "process": "/process-invoice (POST)",
            "extract": "/extract (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": model_manager.is_loaded()
    }


@app.post("/extract")
async def extract_invoice(
    file: UploadFile = File(..., description="Invoice image file (JPG, PNG, JPEG)"),
    doc_id: Optional[str] = Form(None, description="Optional document identifier"),
    enhance_image: Optional[bool] = Form(False, description="Apply OpenCV enhancement preprocessing"),
    reasoning_mode: Optional[str] = Form("simple", description="VLM reasoning mode: 'simple' or 'reason'")
):
    """
    Extract information from invoice image
    
    **Parameters:**
    - **file**: Invoice image file (required)
    - **doc_id**: Optional document identifier (auto-generated from filename if not provided)
    
    **Returns:**
    - JSON with extracted fields, confidence scores, and metadata
    
    **Example Response:**
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
    """
    
    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPG, PNG, JPEG)"
        )
    
    # Validate file extension as fallback
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPG, PNG, JPEG, GIF, BMP, TIFF, WEBP)"
            )
    
    # Check if models are loaded
    if not model_manager.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please wait for server initialization."
        )
    
    # Save uploaded file to temporary location
    import time
    request_start = time.time()
    temp_file = None
    try:
        # Create temporary file
        io_start = time.time()
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_file = temp.name
            # Write uploaded file content
            shutil.copyfileobj(file.file, temp)
        io_time = round(time.time() - io_start, 3)
        
        # Use filename as doc_id if not provided
        if doc_id is None:
            doc_id = os.path.splitext(file.filename)[0]
        
        # Process invoice
        result = InferenceProcessor.process_invoice(temp_file, doc_id, enhance_image, reasoning_mode)
        
        # Add total request time (includes file I/O)
        result['total_request_time_sec'] = round(time.time() - request_start, 2)
        result['file_io_time_sec'] = io_time
        
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing invoice: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        
        # Close uploaded file
        file.file.close()


@app.post("/process-invoice")
async def process_invoice(
    file: UploadFile = File(..., description="Invoice image file"),
    enhance_image: Optional[bool] = Form(False, description="Apply OpenCV enhancement preprocessing"),
    reasoning_mode: Optional[str] = Form("simple", description="VLM reasoning mode: 'simple' or 'reason'")
):
    """
    Process a single invoice and return extracted information
    Simplified endpoint for frontend integration
    
    **Parameters:**
    - **file**: Invoice image file (required)
    - **enhance_image**: Apply OpenCV enhancement preprocessing (optional)
    - **reasoning_mode**: VLM reasoning mode: 'simple' for single-step, 'reason' for Chain of Thought (optional)
    
    **Returns:**
    - JSON with extracted_text, signature_coords, stamp_coords
    """
    
    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    # Check if models are loaded
    if not model_manager.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please wait for server initialization."
        )
    
    temp_file = None
    try:
        # Save uploaded file to temporary location
        suffix = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_file = temp.name
            shutil.copyfileobj(file.file, temp)
        
        # Use filename as doc_id
        doc_id = os.path.splitext(file.filename)[0] if file.filename else "invoice"
        
        # Process invoice
        result = InferenceProcessor.process_invoice(temp_file, doc_id, enhance_image, reasoning_mode)
        
        # Extract fields from result
        fields = result.get("fields", {})
        signature_info = fields.get("signature", {})
        stamp_info = fields.get("stamp", {})
        
        # Build text representation of extracted fields
        extracted_text_parts = []
        if fields.get("dealer_name"):
            extracted_text_parts.append(f"Dealer Name: {fields['dealer_name']}")
        if fields.get("model_name"):
            extracted_text_parts.append(f"Model Name: {fields['model_name']}")
        if fields.get("horse_power"):
            extracted_text_parts.append(f"Horse Power: {fields['horse_power']}")
        if fields.get("asset_cost"):
            extracted_text_parts.append(f"Asset Cost: {fields['asset_cost']}")
        
        extracted_text = "\n".join(extracted_text_parts) if extracted_text_parts else "No structured data extracted"
        
        # Get coordinates
        signature_coords = []
        if signature_info.get("present") and signature_info.get("bbox"):
            bbox = signature_info["bbox"]
            # Convert [x1, y1, x2, y2] format
            signature_coords = [[bbox[0], bbox[1], bbox[2], bbox[3]]]
        
        stamp_coords = []
        if stamp_info.get("present") and stamp_info.get("bbox"):
            bbox = stamp_info["bbox"]
            # Convert [x1, y1, x2, y2] format
            stamp_coords = [[bbox[0], bbox[1], bbox[2], bbox[3]]]
        
        # Return simplified response matching frontend expectations
        return JSONResponse(content={
            "extracted_text": extracted_text,
            "signature_coords": signature_coords,
            "stamp_coords": stamp_coords,
            "doc_id": result.get("doc_id", doc_id),
            "processing_time": result.get("processing_time_sec", 0),
            "confidence": result.get("confidence", 0),
            "cost_estimate_usd": result.get("cost_estimate_usd", 0),
            "fields": fields,  # Include raw fields for reference
            "timing_breakdown": result.get("timing_breakdown", {})  # Include timing info (with reasoning output if present)
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing invoice: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        
        # Close uploaded file
        file.file.close()


@app.post("/extract_batch")
async def extract_batch(
    files: list[UploadFile] = File(..., description="Multiple invoice images")
):
    """
    Extract information from multiple invoice images
    
    **Parameters:**
    - **files**: List of invoice image files
    
    **Returns:**
    - JSON array with results for each invoice
    """
    
    if not model_manager.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please wait for server initialization."
        )
    
    results = []
    temp_files = []
    
    try:
        for file in files:
            # Validate file type
            if not file.content_type.startswith("image/"):
                results.append({
                    "filename": file.filename,
                    "error": "File must be an image"
                })
                continue
            
            # Save to temp file
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp_file = temp.name
                temp_files.append(temp_file)
                shutil.copyfileobj(file.file, temp)
            
            # Process
            try:
                doc_id = os.path.splitext(file.filename)[0]
                result = InferenceProcessor.process_invoice(temp_file, doc_id)
                results.append(result)
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return JSONResponse(content={"results": results}, media_type="application/json; charset=utf-8")
        
    finally:
        # Cleanup
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        for file in files:
            file.file.close()


# ─── NEW ENDPOINTS: Decision Support & Portfolio Intelligence ───────────────

@app.post("/decision-support")
async def decision_support(request: DecisionSupportRequest):
    """
    Generate loan decision support from invoice fields.
    Returns EMI options, recommended plan, eligibility, and reasoning.
    """
    fields = {
        "asset_cost": request.asset_cost,
        "horse_power": request.horse_power,
        "model_name": request.model_name,
    }
    # Normalize fields before decision support
    fields = normalize_fields(fields)
    result = generate_decision_support(fields)
    return JSONResponse(content=result)


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Portfolio intelligence chat endpoint.
    Routes to SQL aggregation or RAG retrieval + Gemini generation.
    """
    if not rag_engine.is_ready:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    result = rag_engine.query(request.query)
    return JSONResponse(content=result)


@app.get("/portfolio/stats")
async def portfolio_stats():
    """
    Return portfolio summary statistics for the dashboard.
    """
    if not rag_engine.is_ready:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    stats = rag_engine.get_portfolio_stats()
    return JSONResponse(content=stats)


@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    """
    Generate a downloadable HTML invoice analysis report.
    Returns the HTML content as a response.
    """
    html = generate_report_html(
        fields=request.fields,
        decision_support=request.decision_support,
        doc_id=request.doc_id,
    )
    return JSONResponse(content={"html": html, "doc_id": request.doc_id})


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=7860,  # Hugging Face Spaces default port
        reload=False
    )
