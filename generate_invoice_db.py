"""
Invoice Database Generator for KrishiIntel AI
Processes real invoice images from data/ using the existing extraction pipeline
and stores results in data/invoices_db.json.

Usage:
    python generate_invoice_db.py
    python generate_invoice_db.py --data-dir data/ --output data/invoices_db.json
"""

import json
import os
import sys
import glob
import time
import argparse
from typing import List, Dict


def generate_invoice_db(data_dir: str = "data", output_path: str = None) -> str:
    """
    Process all invoice images in data_dir using the extraction pipeline
    and save results to invoices_db.json.

    This requires YOLO + Qwen2.5-VL models to be loaded (GPU needed).
    """
    if output_path is None:
        output_path = os.path.join(data_dir, "invoices_db.json")

    # Check if output already exists
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"📄 Invoice DB already exists with {len(existing)} records at {output_path}")
        return output_path

    # Find all image files
    image_extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp")
    image_files: List[str] = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(data_dir, ext)))

    if not image_files:
        print(f"⚠️  No image files found in {data_dir}")
        print("   Creating empty invoice DB for RAG engine...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return output_path

    print(f"📂 Found {len(image_files)} invoice images in {data_dir}")
    print(f"🚀 Starting extraction pipeline...")

    # Load models
    from model_manager import model_manager
    from inference import InferenceProcessor
    from utils.normalization import normalize_fields

    if not model_manager.is_loaded():
        print("🔧 Loading models...")
        model_manager.load_models()

    invoices: List[Dict] = []
    errors: List[Dict] = []
    total = len(image_files)

    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        doc_id = os.path.splitext(filename)[0]

        print(f"  [{i}/{total}] Processing {filename}...", end=" ")
        start = time.time()

        try:
            # Use existing extraction pipeline
            result = InferenceProcessor.process_invoice(image_path, doc_id)
            fields = result.get("fields", {})

            # Normalize extracted fields
            fields = normalize_fields(fields)

            # Build invoice record
            invoice = {
                "doc_id": doc_id,
                "dealer_name": fields.get("dealer_name"),
                "model_name": fields.get("model_name"),
                "horse_power": fields.get("horse_power"),
                "asset_cost": fields.get("asset_cost"),
                "confidence": result.get("confidence", 0),
                "signature_present": fields.get("signature", {}).get("present", False),
                "stamp_present": fields.get("stamp", {}).get("present", False),
                "source_file": filename,
            }
            invoices.append(invoice)

            elapsed = time.time() - start
            print(f"✅ ({elapsed:.1f}s)")

        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ ({elapsed:.1f}s) {str(e)[:60]}")
            errors.append({"file": filename, "error": str(e)})

    # Save results
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ Processed {len(invoices)}/{total} invoices successfully")
    if errors:
        print(f"❌ {len(errors)} errors")
    print(f"📄 Saved to {output_path}")

    return output_path


def ensure_invoice_db(output_path: str = None) -> str:
    """
    Ensure invoice DB exists. If not, try to generate it.
    Falls back to an empty DB if extraction is not possible (no GPU, no models).
    """
    if output_path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base, "data", "invoices_db.json")

    if os.path.exists(output_path):
        return output_path

    print(f"📄 Invoice DB not found at {output_path}")
    try:
        return generate_invoice_db(output_path=output_path)
    except Exception as e:
        print(f"⚠️  Could not generate invoice DB: {e}")
        print("   Creating empty DB — run `python generate_invoice_db.py` to populate it")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate invoice database from raw images")
    parser.add_argument("--data-dir", default="data", help="Directory containing invoice images")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    args = parser.parse_args()

    generate_invoice_db(data_dir=args.data_dir, output_path=args.output)
