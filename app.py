"""
FastAPI Server for KrishiIntel AI
Provides REST API for invoice processing, decision support, portfolio intelligence,
PDF generation, and EMI calculation.

Production-grade: global error handling, structured responses, never crashes.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List
from pydantic import BaseModel
import tempfile
import os
import shutil
import traceback

from config import API_TITLE, API_DESCRIPTION, API_VERSION
from model_manager import model_manager
from inference import InferenceProcessor
from decision import generate_decision_support, compute_emi_smart, compute_emi_manual
from rag_engine import InvoiceKnowledgeBase
from utils.normalization import normalize_fields
from report_generator import generate_report_html
from pdf_generator import generate_single_pdf, generate_batch_pdf
import torch
import config

# ─── Request models ─────────────────────────────────────────────────────────

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

class EMISmartRequest(BaseModel):
    asset_cost: float

class EMIManualRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_months: int

class PortfolioAddRequest(BaseModel):
    doc_id: str
    dealer_name: Optional[str] = None
    model_name: Optional[str] = None
    horse_power: Optional[float] = None
    asset_cost: Optional[float] = None
    region: Optional[str] = None
    invoice_date: Optional[str] = None
    confidence: Optional[float] = None

class BatchReportPDFRequest(BaseModel):
    invoices: List[dict]  # each: { fields: {}, decision_support: {}, doc_id: str }

# ─── RAG engine singleton ───────────────────────────────────────────────────
rag_engine = InvoiceKnowledgeBase()


def _error_response(message: str, status_code: int = 500) -> JSONResponse:
    """Standard error response that never crashes."""
    return JSONResponse(
        status_code=status_code,
        content={
            "answer": message,
            "sources": [],
            "query_type": "error",
        }
    )


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


# ─── Global exception handler ───────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch ALL unhandled exceptions — never crash the server."""
    print(f"🔥 Unhandled exception on {request.url.path}: {exc}")
    traceback.print_exc()
    return _error_response(
        f"An internal error occurred. Please try again or contact support.",
        status_code=500,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard error format."""
    return _error_response(str(exc.detail), status_code=exc.status_code)


# ─── Root & Health ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint - Serve frontend or API information"""
    try:
        frontend_index = os.path.join(os.path.dirname(__file__), "frontend", "dist", "index.html")
        if os.path.exists(frontend_index):
            return FileResponse(frontend_index)

        return {
            "name": API_TITLE,
            "version": API_VERSION,
            "status": "running",
            "models_loaded": model_manager.is_loaded(),
            "endpoints": {
                "health": "/health",
                "process": "/process-invoice (POST)",
                "extract": "/extract (POST)",
                "chat": "/chat (POST)",
                "emi_smart": "/emi/smart (POST)",
                "emi_manual": "/emi/manual (POST)",
                "generate_pdf": "/generate-report-pdf (POST)",
                "docs": "/docs"
            }
        }
    except Exception as e:
        return _error_response(f"Root endpoint error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "models_loaded": model_manager.is_loaded(),
            "rag_ready": rag_engine.is_ready,
        }
    except Exception as e:
        return _error_response(f"Health check error: {str(e)}")


@app.get("/system-status")
async def system_status():
    """
    Get real-time system intelligence telemetry.
    Detects GPU name, VRAM usage, and active quantization.
    """
    try:
        gpu_active = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_active else "CPU Mode"
        
        vram_total = 0
        vram_used = 0
        if gpu_active:
            props = torch.cuda.get_device_properties(0)
            vram_total = round(props.total_memory / (1024**3), 1)
            vram_used = round(torch.cuda.memory_reserved(0) / (1024**3), 1)

        # Get quantization info from config
        q_config = config.QUANTIZATION_CONFIG
        q_bits = "4-bit" if q_config.get("load_in_4bit") else "8-bit" if q_config.get("load_in_8bit") else "None"
        q_type = q_config.get("bnb_4bit_quant_type", "NF4").upper()

        return {
            "gpu_active": gpu_active,
            "gpu_name": gpu_name,
            "vram_total": vram_total,
            "vram_used": vram_used,
            "quantization": f"{q_bits} {q_type}",
            "model_id": config.VLM_MODEL_ID.split("/")[-1],
            "status": "active" if model_manager.is_loaded() else "initializing"
        }
    except Exception as e:
        return {
            "gpu_active": False,
            "gpu_name": "Detection Failed",
            "vram_total": 0,
            "vram_used": 0,
            "quantization": "Unknown",
            "model_id": config.VLM_MODEL_ID.split("/")[-1],
            "status": "error",
            "error": str(e)
        }


# ─── Invoice Extraction ─────────────────────────────────────────────────────

@app.post("/extract")
async def extract_invoice(
    file: UploadFile = File(..., description="Invoice image file (JPG, PNG, JPEG)"),
    doc_id: Optional[str] = Form(None, description="Optional document identifier"),
    enhance_image: Optional[bool] = Form(False, description="Apply OpenCV enhancement preprocessing"),
    reasoning_mode: Optional[str] = Form("simple", description="VLM reasoning mode: 'simple' or 'reason'")
):
    """Extract information from invoice image"""

    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPG, PNG, JPEG)")

    # Validate file extension as fallback
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            raise HTTPException(status_code=400, detail="File must be an image (JPG, PNG, JPEG, GIF, BMP, TIFF, WEBP)")

    # Check if models are loaded
    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="Models not loaded. Please wait for server initialization.")

    import time
    request_start = time.time()
    temp_file = None
    try:
        io_start = time.time()
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_file = temp.name
            shutil.copyfileobj(file.file, temp)
        io_time = round(time.time() - io_start, 3)

        if doc_id is None:
            doc_id = os.path.splitext(file.filename)[0]

        result = InferenceProcessor.process_invoice(temp_file, doc_id, enhance_image, reasoning_mode)

        # Ingest into RAG knowledge base (non-blocking, fail-safe)
        try:
            fields = result.get("fields", {})
            normalized = normalize_fields(fields)
            rag_engine.ingest_invoice({
                "doc_id": doc_id,
                "dealer_name": normalized.get("dealer_name"),
                "model_name": normalized.get("model_name"),
                "horse_power": normalized.get("horse_power"),
                "asset_cost": normalized.get("asset_cost"),
                "region": normalized.get("region"),
                "invoice_date": normalized.get("invoice_date"),
                "confidence": result.get("confidence", 0),
            })
        except Exception:
            pass  # RAG ingestion is best-effort

        result['total_request_time_sec'] = round(time.time() - request_start, 2)
        result['file_io_time_sec'] = io_time

        return JSONResponse(content=result, media_type="application/json; charset=utf-8")

    except HTTPException:
        raise
    except Exception as e:
        return _error_response(f"Error processing invoice: {str(e)}")

    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        file.file.close()


@app.post("/process-invoice")
async def process_invoice(
    file: UploadFile = File(..., description="Invoice image file"),
    enhance_image: Optional[bool] = Form(False, description="Apply OpenCV enhancement preprocessing"),
    reasoning_mode: Optional[str] = Form("simple", description="VLM reasoning mode: 'simple' or 'reason'")
):
    """Process a single invoice and return extracted information (frontend format)"""

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="Models not loaded. Please wait for server initialization.")

    temp_file = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_file = temp.name
            shutil.copyfileobj(file.file, temp)

        doc_id = os.path.splitext(file.filename)[0] if file.filename else "invoice"
        result = InferenceProcessor.process_invoice(temp_file, doc_id, enhance_image, reasoning_mode)

        fields = result.get("fields", {})
        signature_info = fields.get("signature", {})
        stamp_info = fields.get("stamp", {})

        # Ingest into RAG knowledge base (non-blocking, fail-safe)
        try:
            normalized = normalize_fields(fields)
            rag_engine.ingest_invoice({
                "doc_id": result.get("doc_id", doc_id),
                "dealer_name": normalized.get("dealer_name"),
                "model_name": normalized.get("model_name"),
                "horse_power": normalized.get("horse_power"),
                "asset_cost": normalized.get("asset_cost"),
                "region": normalized.get("region"),
                "invoice_date": normalized.get("invoice_date"),
                "confidence": result.get("confidence", 0),
            })
        except Exception:
            pass

        # Build text representation
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

        signature_coords = []
        if signature_info.get("present") and signature_info.get("bbox"):
            bbox = signature_info["bbox"]
            signature_coords = [[bbox[0], bbox[1], bbox[2], bbox[3]]]

        stamp_coords = []
        if stamp_info.get("present") and stamp_info.get("bbox"):
            bbox = stamp_info["bbox"]
            stamp_coords = [[bbox[0], bbox[1], bbox[2], bbox[3]]]

        return JSONResponse(content={
            "extracted_text": extracted_text,
            "signature_coords": signature_coords,
            "stamp_coords": stamp_coords,
            "doc_id": result.get("doc_id", doc_id),
            "processing_time": result.get("processing_time_sec", 0),
            "confidence": result.get("confidence", 0),
            "cost_estimate_usd": result.get("cost_estimate_usd", 0),
            "fields": fields,
            "timing_breakdown": result.get("timing_breakdown", {})
        }, media_type="application/json; charset=utf-8")

    except HTTPException:
        raise
    except Exception as e:
        return _error_response(f"Error processing invoice: {str(e)}")

    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        file.file.close()


# ─── Batch Processing (Fixed: structured JSON, per-file status) ──────────────

@app.post("/extract_batch")
async def extract_batch(
    files: list[UploadFile] = File(..., description="Multiple invoice images")
):
    """
    Extract information from multiple invoice images.
    Returns structured JSON with success/failure status per file.
    """
    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="Models not loaded. Please wait for server initialization.")

    results = []
    temp_files = []
    total = len(files)
    processed = 0
    succeeded = 0
    failed = 0

    try:
        for file in files:
            processed += 1
            entry = {
                "filename": file.filename,
                "index": processed,
                "total": total,
            }

            # Validate file type
            if file.content_type and not file.content_type.startswith("image/"):
                entry["status"] = "failed"
                entry["error"] = "File must be an image"
                entry["data"] = None
                failed += 1
                results.append(entry)
                continue

            # Save to temp file
            try:
                suffix = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                    temp_file = temp.name
                    temp_files.append(temp_file)
                    # Reset pointer to start before copying
                    await file.seek(0)
                    shutil.copyfileobj(file.file, temp)

                doc_id = os.path.splitext(file.filename)[0] if file.filename else "invoice"
                result = InferenceProcessor.process_invoice(temp_file, doc_id)

                # Ingest into RAG (best-effort)
                try:
                    fields = result.get("fields", {})
                    normalized = normalize_fields(fields)
                    rag_engine.ingest_invoice({
                        "doc_id": doc_id,
                        "dealer_name": normalized.get("dealer_name"),
                        "model_name": normalized.get("model_name"),
                        "horse_power": normalized.get("horse_power"),
                        "asset_cost": normalized.get("asset_cost"),
                        "region": normalized.get("region"),
                        "invoice_date": normalized.get("invoice_date"),
                        "confidence": result.get("confidence", 0),
                    })
                except Exception:
                    pass

                entry["status"] = "success"
                entry["data"] = result
                entry["error"] = None
                succeeded += 1

            except Exception as e:
                entry["status"] = "failed"
                entry["error"] = str(e)
                entry["data"] = None
                failed += 1

            results.append(entry)

        return JSONResponse(content={
            "results": results,
            "summary": {
                "total": total,
                "succeeded": succeeded,
                "failed": failed,
            },
            "progress": {
                "completed": processed,
                "total": total,
                "percentage": round((processed / total * 100) if total > 0 else 0, 1),
            }
        }, media_type="application/json; charset=utf-8")

    except Exception as e:
        return _error_response(f"Batch processing error: {str(e)}")

    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
        for file in files:
            file.file.close()


# ─── Decision Support & EMI ──────────────────────────────────────────────────

@app.post("/decision-support")
async def decision_support(request: DecisionSupportRequest):
    """Generate loan decision support from invoice fields."""
    try:
        fields = {
            "asset_cost": request.asset_cost,
            "horse_power": request.horse_power,
            "model_name": request.model_name,
        }
        fields = normalize_fields(fields)
        result = generate_decision_support(fields)
        return JSONResponse(content=result)
    except Exception as e:
        return _error_response(f"Decision support error: {str(e)}")


@app.post("/emi/smart")
async def emi_smart(request: EMISmartRequest):
    """
    Smart EMI calculation — auto-selects interest rate and tenure based on asset cost.
    Returns EMI value, total payable, explanation, and all options.
    """
    try:
        result = compute_emi_smart(request.asset_cost)
        return JSONResponse(content=result)
    except Exception as e:
        return _error_response(f"EMI Smart calculation error: {str(e)}")


@app.post("/emi/manual")
async def emi_manual(request: EMIManualRequest):
    """
    Manual EMI calculation — user specifies principal, rate, and tenure.
    Returns EMI value, total payable, and explanation.
    """
    try:
        result = compute_emi_manual(request.principal, request.annual_rate, request.tenure_months)
        return JSONResponse(content=result)
    except Exception as e:
        return _error_response(f"EMI Manual calculation error: {str(e)}")


# ─── Chat & Portfolio Intelligence ───────────────────────────────────────────

@app.post("/chat")
async def chat(request: ChatRequest):
    """Portfolio intelligence chat endpoint with RAG."""
    try:
        if not rag_engine.is_ready:
            return _error_response("RAG engine not initialized. Please wait for startup.", 503)

        result = rag_engine.query(request.query)
        return JSONResponse(content=result)
    except Exception as e:
        return _error_response(f"Chat error: {str(e)}")


@app.get("/portfolio/stats")
async def portfolio_stats():
    """Return portfolio summary statistics for the dashboard."""
    try:
        if not rag_engine.is_ready:
            return _error_response("RAG engine not initialized. Please wait for startup.", 503)

        stats = rag_engine.get_portfolio_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        return _error_response(f"Portfolio stats error: {str(e)}")


@app.post("/add-to-portfolio")
async def add_to_portfolio(request: PortfolioAddRequest):
    """
    Add an extracted invoice to the portfolio.
    Saves to JSON, updates FAISS index, SQLite DB.
    New invoice is immediately available for all future queries.
    """
    try:
        if not rag_engine.is_ready:
            return _error_response("RAG engine not initialized. Please wait for startup.", 503)

        invoice_data = {
            "doc_id": request.doc_id,
            "dealer_name": request.dealer_name,
            "model_name": request.model_name,
            "horse_power": request.horse_power,
            "asset_cost": request.asset_cost,
            "region": request.region,
            "invoice_date": request.invoice_date,
            "confidence": request.confidence,
        }

        success = rag_engine.ingest_invoice(invoice_data)

        if success:
            stats = rag_engine.get_portfolio_stats()
            return JSONResponse(content={
                "status": "success",
                "message": f"Invoice '{request.doc_id}' added to portfolio.",
                "portfolio_stats": stats,
            })
        else:
            return _error_response("Failed to add invoice to portfolio.", 400)

    except Exception as e:
        return _error_response(f"Portfolio add error: {str(e)}")


# ─── Report Generation ──────────────────────────────────────────────────────

@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    """Generate a downloadable HTML invoice analysis report."""
    try:
        html = generate_report_html(
            fields=request.fields,
            decision_support=request.decision_support,
            doc_id=request.doc_id,
        )
        return JSONResponse(content={"html": html, "doc_id": request.doc_id})
    except Exception as e:
        return _error_response(f"Report generation error: {str(e)}")


@app.post("/generate-report-pdf")
async def generate_report_pdf(request: ReportRequest):
    """
    Generate a downloadable PDF invoice analysis report.
    Returns the PDF file as a binary response.
    """
    try:
        pdf_bytes = generate_single_pdf(
            fields=request.fields,
            decision_support=request.decision_support,
            doc_id=request.doc_id,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=KrishiIntel_Report_{request.doc_id}.pdf",
            },
        )
    except RuntimeError as e:
        return _error_response(str(e), 501)
    except Exception as e:
        return _error_response(f"PDF generation error: {str(e)}")


@app.post("/generate-batch-report-pdf")
async def generate_batch_report_pdf(request: BatchReportPDFRequest):
    """
    Generate a merged PDF containing reports for multiple invoices.
    Each invoice gets its own page(s) in the merged PDF.
    """
    try:
        pdf_bytes = generate_batch_pdf(request.invoices)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=KrishiIntel_Batch_Report.pdf",
            },
        )
    except RuntimeError as e:
        return _error_response(str(e), 501)
    except ValueError as e:
        return _error_response(str(e), 400)
    except Exception as e:
        return _error_response(f"Batch PDF generation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Run server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=7860,  # Hugging Face Spaces default port
        reload=False
    )
