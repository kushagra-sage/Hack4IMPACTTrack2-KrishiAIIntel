"""
Inference Processor - Handles VLM extraction, validation, and result formatting
"""

import torch
import time
import json
import codecs
import re
import cv2
import numpy as np
from PIL import Image
from qwen_vl_utils import process_vision_info
from typing import Dict, Tuple

from config import (
    MAX_IMAGE_SIZE,
    HP_VALID_RANGE,
    ASSET_COST_VALID_RANGE,
    COST_PER_GPU_HOUR
)
from model_manager import model_manager


# Single-step extraction prompt (original "simple" mode)
EXTRACTION_PROMPT = """
You are an expert at reading noisy, handwritten Indian invoices and quotations.

Your task is to extract text EXACTLY as it appears in the image.
Do NOT translate, summarize, normalize, or rewrite any text.
Preserve the original language (Hindi, Marathi, Kannada, English, etc.).

Carefully read the image and extract the following fields.

Return ONLY valid JSON in this format:

{
  "dealer_name": string,
  "model_name": string,
  "horse_power": number,
  "asset_cost": number
}

Critical rules:
- Dealer name must be copied exactly from the image in the original language and spelling.
- Model name must be copied exactly from the image without translation.
- Do NOT convert regional language text into English.
- Do NOT expand abbreviations or correct spelling.
- Only numbers may be normalized.

Extraction hints:
- Asset cost is the total amount, usually the largest number on the page, the total amount after TAX, final price or final cost.
- Dealer name is usually at the top header or company name.
- Model name often appears near words like Model, Tractor, Variant.
- Horse power must come ONLY from explicit HP text, never from model numbers.
- Horse power may appear as "HP", handwritten like "49 HP", "63hp", "HP-30".
- Remove commas and currency symbols from numbers only.
- If handwriting is unclear, make your best reasonable interpretation of the characters — but preserve language.

Output rules:
- Output ONLY valid JSON.
- Do NOT include markdown, explanations, or extra text.
"""


# Combined Chain of Thought prompt (reasoning mode) - Single call with reasoning and extraction
COMBINED_REASONING_EXTRACTION_PROMPT = """
Analyze this Indian tractor invoice using Chain of Thought reasoning.

First, share your observations about the 2 key fields:

MODEL NAME:
- How is it presented? (checkbox/handwritten/printed or any other way)
- If a checkboxes or anything marked?
- What exact text do you see?
- There could be only one model asssociated with a deal. If you see multiple model names listed, check if one of them is marked or highlighted in some way. 
- Based on this, which model name you think is involved in the deal.

HORSE POWER:
- Where is HP mentioned?
- Explicit text like "49 HP" or in checkbox?
- Which value is marked?
- HP must come from explicit HP text only, never from model numbers
- If only one value for HP is associated with the correct Model name, it is the models HP.
- If multiple HP values are associated with the correct Model, the correct HP will be usuall marked.


After reasoning, extract the fields.

Return ONLY valid JSON:
{{
  "reasoning": "your observations and thoughts here",
  "dealer_name": "string",
  "model_name": string,
  "horse_power": number,
  "asset_cost": number
}}

Rules for extraction:
- Copy dealer/model names EXACTLY in original language, don't translate
- HP as number only ("49 HP" → 49), use selected checkbox
- Asset cost as number (remove ₹, commas: "1,50,000" → 150000)
- Asset cost is the final total after TAX
- Dealer is usually at top header
- If handwriting unclear, make best interpretation but preserve language


Extraction hints:
- Dealer name is usually at the top header or company name.
- Model name often appears near words like Model, Tractor, Variant.
- Horse power must come ONLY from explicit HP text, never from model numbers.
- Horse power may appear as "HP", handwritten like "49 HP", "63hp", "HP-30".
- Remove commas and currency symbols from numbers only.
- If handwriting is unclear, make your best reasonable interpretation of the characters — but preserve language.


Output ONLY valid JSON, no markdown.
"""


class InferenceProcessor:
    """Handles VLM inference, validation, and result processing"""
    
    @staticmethod
    def enhance_image_opencv(image_path: str) -> str:
        """
        Apply OpenCV preprocessing to enhance image quality
        Returns path to enhanced image (same as input, modified in place)
        """
        # Load image (BGR)
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image from {image_path}")
        
        # Convert to LAB color space (better for contrast)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE on L-channel
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge back
        lab_enhanced = cv2.merge((l_enhanced, a, b))
        contrast_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoisingColored(
            contrast_enhanced,
            None,
            h=10, hColor=10,
            templateWindowSize=7,
            searchWindowSize=21
        )
        
        # Sharpening (Unsharp Mask)
        blur = cv2.GaussianBlur(denoised, (0, 0), sigmaX=1.2)
        sharpened = cv2.addWeighted(denoised, 1.5, blur, -0.5, 0)
        
        # Save enhanced image back to the same path
        cv2.imwrite(image_path, sharpened)
        print(f"✨ Image enhanced with OpenCV preprocessing")
        
        return image_path
    
    @staticmethod
    def preprocess_image(image_path: str) -> Image.Image:
        """Load and resize image if needed"""
        image = Image.open(image_path).convert("RGB")
        
        # Resize if too large
        if max(image.size) > MAX_IMAGE_SIZE:
            ratio = MAX_IMAGE_SIZE / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)
            print(f"🔄 Image resized to {new_size}")
        
        return image
    
    @staticmethod
    def run_vlm_extraction(image: Image.Image) -> Tuple[str, float]:
        """Run VLM model to extract invoice fields"""
        if not model_manager.is_loaded():
            raise RuntimeError("Models not loaded")
        
        model = model_manager.vlm_model
        processor = model_manager.processor
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": EXTRACTION_PROMPT}
                ]
            }
        ]
        
        # Apply chat template
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Process vision input
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda")
        
        start = time.time()
        
        # Generate
        generated_ids = model.generate(**inputs, max_new_tokens=256)
        
        latency = time.time() - start
        
        # Decode output
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )
        
        output_text = output_text[0] if isinstance(output_text, list) else output_text
        
        # Clean up GPU memory
        del inputs, generated_ids, generated_ids_trimmed
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return output_text, latency
    
    @staticmethod
    def run_vlm_reasoning_and_extraction(image: Image.Image) -> Tuple[str, str, float]:
        """
        Run VLM model with combined Chain of Thought reasoning and extraction in single call
        Returns: (reasoning_text, extraction_json_str, latency)
        """
        if not model_manager.is_loaded():
            raise RuntimeError("Models not loaded")
        
        model = model_manager.vlm_model
        processor = model_manager.processor
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": COMBINED_REASONING_EXTRACTION_PROMPT}
                ]
            }
        ]
        
        # Apply chat template
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Process vision input
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda")
        
        start = time.time()
        
        # Generate with more tokens for combined reasoning + extraction
        generated_ids = model.generate(**inputs, max_new_tokens=384)
        
        latency = time.time() - start
        
        # Decode output
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )
        
        output_text = output_text[0] if isinstance(output_text, list) else output_text
        
        # Clean up GPU memory
        del inputs, generated_ids, generated_ids_trimmed
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Parse the combined output to separate reasoning from extraction
        reasoning_text = ""
        extraction_json = output_text
        
        # First, remove markdown code fences if present
        cleaned_output = output_text.strip()
        if cleaned_output.startswith('```'):
            # Remove opening ```json or ```
            lines = cleaned_output.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            # Remove closing ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned_output = '\n'.join(lines).strip()
        
        try:
            # Try to parse the cleaned JSON
            parsed = json.loads(cleaned_output)
            if "reasoning" in parsed:
                reasoning_text = parsed["reasoning"]
                # Remove reasoning from output to get clean extraction JSON
                extraction_dict = {k: v for k, v in parsed.items() if k != "reasoning"}
                extraction_json = json.dumps(extraction_dict)
            else:
                # No reasoning field, use entire output as extraction
                extraction_json = cleaned_output
        except json.JSONDecodeError:
            # If parsing fails, try to find JSON pattern in the text
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    parsed = json.loads(json_str)
                    if "reasoning" in parsed:
                        reasoning_text = parsed["reasoning"]
                        extraction_dict = {k: v for k, v in parsed.items() if k != "reasoning"}
                        extraction_json = json.dumps(extraction_dict)
                    else:
                        extraction_json = json_str
                except:
                    extraction_json = json_str
                # Everything before JSON is additional reasoning
                prefix = cleaned_output[:json_match.start()].strip()
                if prefix and not reasoning_text:
                    reasoning_text = prefix
        
        print(f"🧠 Combined reasoning + extraction completed in {latency:.2f}s")
        return reasoning_text, extraction_json, latency
    
    @staticmethod
    def extract_json_from_output(text: str) -> Dict:
        """Extract JSON from model output"""
        # Handle single/double backticks
        if text.count('```') in [1, 2]:
            data = text.split('```')[1]
            if data.startswith('json'):
                data = data[4:]
            try:
                return json.loads(data.strip())
            except:
                pass
        
        # Try markdown code blocks
        markdown_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if markdown_match:
            try:
                return json.loads(markdown_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Find JSON blocks
        json_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        
        for match in json_matches:
            json_str = match.group(0)
            try:
                parsed = json.loads(json_str)
                # Verify expected keys
                if all(key in parsed for key in ["dealer_name", "model_name", "horse_power", "asset_cost"]):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        # Fallback
        return {
            "dealer_name": None,
            "model_name": None,
            "horse_power": None,
            "asset_cost": None
        }
    
    @staticmethod
    def clean_text(text) -> str:
        """Clean text field"""
        if not text:
            return None
        text = str(text).strip()
        text = re.sub(r"\s+", " ", text)
        return text if len(text) > 1 else None
    
    @staticmethod
    def clean_number(num):
        """Clean number field"""
        try:
            if num is None:
                return None
            return int(float(num))
        except:
            return None
    
    @staticmethod
    def fix_horse_power(vlm_hp, model_name) -> Tuple:
        """Fix common HP extraction mistakes"""
        # Accept if in valid range
        if vlm_hp is not None and HP_VALID_RANGE[0] <= vlm_hp <= HP_VALID_RANGE[1]:
            return vlm_hp, 1.0
        
        # Try extracting from model name
        if model_name:
            match = re.search(r"HP[- ]?(\d+)", model_name, re.I)
            if match:
                hp = int(match.group(1))
                if HP_VALID_RANGE[0] <= hp <= HP_VALID_RANGE[1]:
                    return hp, 0.8
        
        return None, 0.2
    
    @staticmethod
    def validate_asset_cost(cost) -> Tuple:
        """Validate asset cost"""
        if cost is None:
            return None, 0.2
        
        cost = InferenceProcessor.clean_number(cost)
        
        if ASSET_COST_VALID_RANGE[0] <= cost <= ASSET_COST_VALID_RANGE[1]:
            return cost, 1.0
        
        return None, 0.3
    
    @staticmethod
    def validate_text_field(text) -> Tuple:
        """Validate text fields"""
        text = InferenceProcessor.clean_text(text)
        if not text or len(text) < 3:
            return None, 0.3
        return text, 1.0
    
    @staticmethod
    def validate_prediction(raw_json: Dict) -> Tuple[Dict, float, list]:
        """Validate and fix extracted fields"""
        warnings = []
        confidences = []
        
        # Dealer
        dealer, dealer_conf = InferenceProcessor.validate_text_field(raw_json.get("dealer_name"))
        if dealer is None:
            warnings.append("Dealer name invalid")
        confidences.append(dealer_conf)
        
        # Model
        model_name, model_conf = InferenceProcessor.validate_text_field(raw_json.get("model_name"))
        if model_name is None:
            warnings.append("Model name invalid")
        confidences.append(model_conf)
        
        # Horse Power
        hp_raw = InferenceProcessor.clean_number(raw_json.get("horse_power"))
        hp, hp_conf = InferenceProcessor.fix_horse_power(hp_raw, model_name)
        if hp is None:
            warnings.append("Horse power invalid")
        confidences.append(hp_conf)
        
        # Asset Cost
        cost_raw = InferenceProcessor.clean_number(raw_json.get("asset_cost"))
        cost, cost_conf = InferenceProcessor.validate_asset_cost(cost_raw)
        if cost is None:
            warnings.append("Asset cost invalid")
        confidences.append(cost_conf)
        
        # Overall field confidence
        field_confidence = round(sum(confidences) / len(confidences), 3)
        
        validated = {
            "dealer_name": dealer,
            "model_name": model_name,
            "horse_power": hp,
            "asset_cost": cost
        }
        
        return validated, field_confidence, warnings
    
    @staticmethod
    def process_invoice(image_path: str, doc_id: str = None, enhance_image: bool = False, reasoning_mode: str = "simple") -> Dict:
        """
        Complete invoice processing pipeline
        
        Args:
            image_path: Path to invoice image
            doc_id: Document identifier (optional)
            enhance_image: Whether to apply OpenCV enhancement (optional)
            reasoning_mode: "simple" for single-step extraction, "reason" for Chain of Thought (optional)
        
        Returns:
            dict: Complete JSON output with all fields
        """
        total_start = time.time()
        timing_breakdown = {}
        
        # Generate doc_id if not provided
        if doc_id is None:
            import os
            doc_id = os.path.splitext(os.path.basename(image_path))[0]
        
        # Step 0: Apply OpenCV Enhancement if requested
        if enhance_image:
            t0 = time.time()
            image_path = InferenceProcessor.enhance_image_opencv(image_path)
            timing_breakdown['opencv_enhancement'] = round(time.time() - t0, 3)
        
        # Step 1: Preprocess image
        t1 = time.time()
        image = InferenceProcessor.preprocess_image(image_path)
        timing_breakdown['image_preprocessing'] = round(time.time() - t1, 3)
        
        # Step 2: YOLO Detection
        t2 = time.time()
        signature_info, stamp_info, signature_conf, stamp_conf = model_manager.detect_sign_stamp(image_path)
        timing_breakdown['yolo_detection'] = round(time.time() - t2, 3)
        
        # Step 3: VLM Extraction (either simple or with Chain of Thought reasoning)
        t3 = time.time()
        if reasoning_mode == "reason":
            # Combined Chain of Thought: reasoning + extraction in single call
            print("🧠 Using Chain of Thought reasoning mode (single call)")
            
            reasoning_output, vlm_output, vlm_latency = InferenceProcessor.run_vlm_reasoning_and_extraction(image)
            timing_breakdown['vlm_inference'] = round(vlm_latency, 3)
            
            # Store reasoning for debugging/transparency
            timing_breakdown['reasoning_output'] = reasoning_output
        else:
            # Single-step simple extraction (original approach)
            print("⚡ Using simple mode (1-step)")
            vlm_output, vlm_latency = InferenceProcessor.run_vlm_extraction(image)
            timing_breakdown['vlm_inference'] = round(vlm_latency, 3)
        
        # Clean up image
        image.close()
        del image
        
        # Step 4: Parse JSON
        t4 = time.time()
        raw_json = InferenceProcessor.extract_json_from_output(vlm_output)
        timing_breakdown['json_parsing'] = round(time.time() - t4, 3)
        
        # Step 5: Validate and fix
        t5 = time.time()
        validated_fields, field_confidence, warnings = InferenceProcessor.validate_prediction(raw_json)
        timing_breakdown['validation'] = round(time.time() - t5, 3)
        
        # Add signature and stamp
        validated_fields["signature"] = signature_info
        validated_fields["stamp"] = stamp_info
        
        # Calculate overall confidence - average of YOLO detection scores only
        confidences = []
        if signature_info["present"]:
            confidences.append(signature_conf)
        if stamp_info["present"]:
            confidences.append(stamp_conf)
        
        # If both sign and stamp detected, average them; otherwise use whichever is present
        overall_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
        
        # Calculate time and cost
        total_time = time.time() - total_start
        cost_estimate = (COST_PER_GPU_HOUR * total_time) / 3600
        
        # Build result
        result = {
            "doc_id": doc_id,
            "fields": validated_fields,
            "confidence": overall_confidence,
            "processing_time_sec": round(total_time, 2),
            "timing_breakdown": timing_breakdown,
            "cost_estimate_usd": round(cost_estimate, 6),
            "warnings": warnings if warnings else None
        }
        
        return result
