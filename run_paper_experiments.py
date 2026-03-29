import json
import os
import time
import random
import re
from typing import Dict, List, Tuple, Optional

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    from scipy.stats import wilcoxon
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Import project modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference import InferenceProcessor
from utils.normalization import normalize_fields
import config


def load_ground_truth(json_path: str, limit: Optional[int] = None) -> List[Dict]:
    """Load ground truth from existing invoices_db.json"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter out entries with too many nulls to ensure we have actual labels
    valid_data = [d for d in data if d.get('dealer_name') and d.get('model_name')]
    # Sort by doc_id to ensure deterministic order if resuming
    valid_data.sort(key=lambda x: x['doc_id'])
    
    if limit is not None:
        return valid_data[:limit]
    return valid_data


def run_tesseract_baseline(image_path: str) -> Dict:
    """Run Tesseract OCR and use regex for extraction"""
    if not HAS_TESSERACT:
        return {"dealer_name": None, "model_name": None, "horse_power": None, "asset_cost": None}
    
    try:
        # Pytesseract needs the path on Windows sometimes, we'll try default first
        text = pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        print(f"Tesseract failed: {e}")
        return {"dealer_name": None, "model_name": None, "horse_power": None, "asset_cost": None}
    
    # Simple regex extraction (this is meant to be a naive baseline)
    hp_match = re.search(r'(\d{2,3})\s*(?:HP|H\.P|H\.P\.|hp)', text, re.IGNORECASE)
    cost_match = re.search(r'(?:Rs|INR|₹|Total)[\.\s]*([\d,]+)', text, re.IGNORECASE)
    
    hp = int(hp_match.group(1)) if hp_match else None
    
    cost = None
    if cost_match:
        try:
            cost_str = cost_match.group(1).replace(',', '')
            cost = int(cost_str)
        except:
            pass
            
    # For text fields, OCR+Regex is very poor without NLP. We just return None.
    return {
        "dealer_name": None, # Too hard for simple regex
        "model_name": None,
        "horse_power": hp,
        "asset_cost": cost
    }


def calculate_f1(pred, gt, is_text=True):
    """Calculate simple F1 score based on exact match or fuzzy match"""
    if not gt:
        return 1.0 if not pred else 0.0
    if not pred:
        return 0.0
        
    if is_text:
        # Lowercase exact match (since normalization handles fuzzy)
        pred_str = str(pred).lower().strip()
        gt_str = str(gt).lower().strip()
        return 1.0 if pred_str == gt_str else 0.0
    else:
        # Numeric match (allow 5% tolerance for cost)
        try:
            p, g = float(pred), float(gt)
            if p == g: return 1.0
            if abs(p - g) / max(g, 1) <= 0.05: return 1.0
            return 0.0
        except:
            return 0.0


def load_checkpoint(filepath: str = "evaluation_checkpoint.json") -> Tuple[int, Dict]:
    """Load progress from checkpoint file"""
    if os.path.exists(filepath):
        print(f"🔄 Resuming from checkpoint: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
            return checkpoint["last_index"], checkpoint["results"]
    return -1, {
        "tesseract": {"dealer_name": [], "model_name": [], "horse_power": [], "asset_cost": []},
        "qwen_de": {"dealer_name": [], "model_name": [], "horse_power": [], "asset_cost": []},
        "qwen_cot": {"dealer_name": [], "model_name": [], "horse_power": [], "asset_cost": []}
    }


def save_checkpoint(last_index: int, results: Dict, filepath: str = "evaluation_checkpoint.json"):
    """Save progress to checkpoint file"""
    checkpoint = {
        "last_index": last_index,
        "results": results,
        "timestamp": time.time()
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=4)
    # Also save a backup during the run
    with open("evaluation_results_backup.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)


def run_experiments():
    print("🚀 Starting KrishiIntel AI Full Research Evaluation with Checkpoints...")
    gt_path = os.path.join("data", "invoices_db.json")
    if not os.path.exists(gt_path):
        print("Ground truth not found.")
        return
        
    # Load all data
    gt_data = load_ground_truth(gt_path)
    total_invoices = len(gt_data)
    
    # Load checkpoint
    last_index, results = load_checkpoint()
    
    print(f"Processing total of {total_invoices} invoices...")
    
    print("\n⏳ Warming up VLM Model...")
    from model_manager import get_model_manager
    mm = get_model_manager()
    mm.ensure_model_loaded()
    
    start_time = time.time()
    
    for i in range(last_index + 1, total_invoices):
        gt_item = gt_data[i]
        doc_id = gt_item['doc_id']
        image_path = os.path.join("data", f"{doc_id}.png")
        if not os.path.exists(image_path):
            image_path = os.path.join("data", f"{doc_id}.jpg")
            
        if not os.path.exists(image_path):
            print(f"Skipping {doc_id}, image not found.")
            # Still update results list with zeros to maintain alignment for Wilcoxon
            for method in results:
                for field in results[method]:
                    results[method][field].append(0.0)
            save_checkpoint(i, results)
            continue
            
        print(f"\n[{i+1}/{total_invoices}] Evaluating {doc_id}...")
        
        # 1. Tesseract Baseline
        tess_res = run_tesseract_baseline(image_path)
        
        # 2. Qwen DE (Simple)
        qwen_de_res = InferenceProcessor.process_invoice(
            image_path=image_path, 
            doc_id=doc_id, 
            reasoning_mode="simple"
        )
        de_fields = qwen_de_res.get('fields', {})
        
        # 3. Qwen CoT (Reason)
        qwen_cot_res = InferenceProcessor.process_invoice(
            image_path=image_path, 
            doc_id=doc_id, 
            reasoning_mode="reason"
        )
        cot_fields = qwen_cot_res.get('fields', {})
        
        # Calculate F1s
        for field in ["dealer_name", "model_name", "horse_power", "asset_cost"]:
            gt_val = gt_item.get(field)
            is_text = field in ["dealer_name", "model_name"]
            
            results["tesseract"][field].append(calculate_f1(tess_res.get(field), gt_val, is_text))
            results["qwen_de"][field].append(calculate_f1(de_fields.get(field), gt_val, is_text))
            results["qwen_cot"][field].append(calculate_f1(cot_fields.get(field), gt_val, is_text))
            
        # Save checkpoint after every invoice for Colab stability
        save_checkpoint(i, results)
        
        # Print ETA
        elapsed = time.time() - start_time
        avg_time = elapsed / (i - last_index) if (i - last_index) > 0 else 0
        rem = total_invoices - (i + 1)
        eta_min = (rem * avg_time) / 60
        print(f"  [Checkpoint Saved] ETA: {eta_min:.1f} minutes | Progress: {((i+1)/total_invoices)*100:.1f}%")
            
    # Aggregate and Print Table
    print("\n" + "="*80)
    print("📊 FULL DATASET EXPERIMENTAL RESULTS (F1 Scores)")
    print("="*80)
    
    header = f"| Method | Dealer Name | Model Name | Horse Power | Asset Cost | Agg. F1 |"
    sep = f"|---|---|---|---|---|---|"
    print(header)
    print(sep)
    
    agg_scores = {}
    for method in ["tesseract", "qwen_de", "qwen_cot"]:
        field_avgs = []
        all_doc_f1s = []
        
        # Calculate average per field
        for field in ["dealer_name", "model_name", "horse_power", "asset_cost"]:
            vals = results[method][field]
            avg = sum(vals)/len(vals) if vals else 0
            field_avgs.append(avg)
        
        # Calculate aggregate per document
        num_docs = len(results[method]["dealer_name"])
        for d_idx in range(num_docs):
            doc_sum = sum(results[method][f][d_idx] for f in ["dealer_name", "model_name", "horse_power", "asset_cost"])
            all_doc_f1s.append(doc_sum / 4.0)
            
        agg_f1 = sum(all_doc_f1s) / len(all_doc_f1s) if all_doc_f1s else 0
        agg_scores[method] = all_doc_f1s
        
        row = f"| {method.upper()} | " + " | ".join([f"{a:.2f}" for a in field_avgs]) + f" | {agg_f1:.2f} |"
        print(row)
        
    # Statistical Significance (Wilcoxon)
    if HAS_SCIPY and len(agg_scores["qwen_de"]) > 0:
        print("\n" + "="*80)
        print("📈 STATISTICAL SIGNIFICANCE (Wilcoxon Signed-Rank Test)")
        print("="*80)
        
        # Compare Qwen DE vs Qwen CoT
        de_scores = agg_scores["qwen_de"]
        cot_scores = agg_scores["qwen_cot"]
        
        # Wilcoxon requires differences to be non-zero
        stat, p_val = wilcoxon(de_scores, cot_scores, alternative='two-sided')
        
        print(f"Comparing Qwen-DE vs Qwen-CoT:")
        print(f"  - Statistic: {stat:.4f}")
        print(f"  - P-Value: {p_val:.4f}")
        
        if p_val < 0.05:
            print(f"  - Result: STATISTICALLY SIGNIFICANT (p < 0.05) ✅")
        else:
            print(f"  - Result: NOT statistically significant (p >= 0.05) ❌")
            
    print("\n✅ Evaluation complete. You can update the research paper with these exact numbers!")

if __name__ == "__main__":
    run_experiments()
