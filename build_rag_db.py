"""
Offline RAG Database Builder for KrishiIntel AI
Processes all invoice images from data/ using the extraction pipeline
and builds data/invoices_db.json for the RAG knowledge base.

This script is meant to run OFFLINE (manually, before starting the server).
It is NEVER called by the FastAPI app or rag_engine.

Usage:
    python build_rag_db.py
    python build_rag_db.py --data-dir data/ --output data/invoices_db.json
"""

import json
import os
import sys
import glob
import time
import argparse
from typing import List, Dict


def build_rag_db(data_dir: str = "data", output_path: str = None) -> str:
    """
    Process all invoice images in data_dir using the extraction pipeline
    and save results to invoices_db.json.

    Requires YOLO + Qwen2.5-VL models (GPU recommended).
    """
    if output_path is None:
        output_path = os.path.join(data_dir, "invoices_db.json")

    # Find all image files
    image_extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp")
    image_files: List[str] = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(data_dir, ext)))

    if not image_files:
        print(f"⚠️  No image files found in {data_dir}")
        print("   Creating empty invoice DB...")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return output_path

    print(f"📂 Found {len(image_files)} invoice images in {data_dir}")

    # Check if output already exists — offer to extend or overwrite
    existing: List[Dict] = []
    existing_ids: set = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_ids = {inv.get("doc_id") for inv in existing}
        print(f"📄 Existing DB has {len(existing)} records")

        # Filter out already-processed images
        image_files = [
            f for f in image_files
            if os.path.splitext(os.path.basename(f))[0] not in existing_ids
        ]
        if not image_files:
            print("✅ All images already processed. Nothing to do.")
            return output_path
        print(f"🆕 {len(image_files)} new images to process")

    # Load models
    from model_manager import model_manager
    from inference import InferenceProcessor
    from utils.normalization import normalize_fields

    if not model_manager.is_loaded():
        print("🔧 Loading models...")
        model_manager.load_models()

    print(f"🚀 Starting extraction pipeline...")

    invoices: List[Dict] = list(existing)  # Start with existing records
    errors: List[Dict] = []
    total = len(image_files)

    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        doc_id = os.path.splitext(filename)[0]

        print(f"  [{i}/{total}] Processing {filename}...", end=" ")
        start = time.time()

        try:
            result = InferenceProcessor.process_invoice(image_path, doc_id)
            fields = result.get("fields", {})
            fields = normalize_fields(fields)

            invoice = {
                "doc_id": doc_id,
                "dealer_name": fields.get("dealer_name"),
                "model_name": fields.get("model_name"),
                "horse_power": fields.get("horse_power"),
                "asset_cost": fields.get("asset_cost"),
                "region": fields.get("region"),
                "invoice_date": fields.get("invoice_date"),
                "confidence": result.get("confidence", 0),
            }
            invoices.append(invoice)

            elapsed = time.time() - start
            print(f"✅ ({elapsed:.1f}s)")

        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ ({elapsed:.1f}s) {str(e)[:80]}")
            errors.append({"file": filename, "error": str(e)})

    # Save results
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ Total invoices in DB: {len(invoices)} ({total - len(errors)} new + {len(existing)} existing)")
    if errors:
        print(f"❌ {len(errors)} errors:")
        for err in errors[:5]:
            print(f"   • {err['file']}: {err['error'][:60]}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
    print(f"📄 Saved to {output_path}")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build RAG invoice database from raw images (run offline)"
    )
    parser.add_argument(
        "--data-dir", default="data",
        help="Directory containing invoice images (default: data/)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output JSON file path (default: data/invoices_db.json)"
    )
    args = parser.parse_args()

    build_rag_db(data_dir=args.data_dir, output_path=args.output)
