"""
Model Manager - Handles loading and caching of YOLO and VLM models
"""

import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
    BitsAndBytesConfig
)
from ultralytics import YOLO
from typing import Tuple

from config import (
    YOLO_MODEL_PATH,
    VLM_MODEL_ID,
    QUANTIZATION_CONFIG,
    YOLO_CONFIDENCE_THRESHOLD
)


class ModelManager:
    """Singleton class to manage model loading and inference"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ModelManager._initialized:
            self.yolo_model = None
            self.vlm_model = None
            self.processor = None
            ModelManager._initialized = True
    
    def load_models(self):
        """Load both YOLO and VLM models into memory"""
        print("🚀 Starting model loading...")
        
        # Load YOLO model
        self.yolo_model = self._load_yolo_model()
        
        # Load VLM model
        self.vlm_model, self.processor = self._load_vlm_model()
        
        # Warm up models to initialize CUDA context
        self._warmup_models()
        
        print("✅ All models loaded successfully!")
    
    def _load_yolo_model(self) -> YOLO:
        """Load trained YOLO model for signature and stamp detection"""
        if not os.path.exists(YOLO_MODEL_PATH):
            raise FileNotFoundError(
                f"YOLO model not found at {YOLO_MODEL_PATH}. "
                "Please ensure best.pt is in utils/models/"
            )
        
        yolo_model = YOLO(str(YOLO_MODEL_PATH))
        print(f"✅ YOLO model loaded from {YOLO_MODEL_PATH}")
        return yolo_model
    
    def _load_vlm_model(self) -> Tuple:
        """
        Load Qwen2.5-VL model with 4-bit quantization
        Downloads from Hugging Face on first run
        """
        print(f"📥 Loading VLM model: {VLM_MODEL_ID}")
        print("   (This will download ~4GB on first run)")

        # Clear GPU cache before loading
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=QUANTIZATION_CONFIG["load_in_4bit"],
            bnb_4bit_quant_type=QUANTIZATION_CONFIG["bnb_4bit_quant_type"],
            bnb_4bit_compute_dtype=getattr(torch, QUANTIZATION_CONFIG["bnb_4bit_compute_dtype"]),
            bnb_4bit_use_double_quant=QUANTIZATION_CONFIG["bnb_4bit_use_double_quant"]
        )
        
        # Load processor
        processor = AutoProcessor.from_pretrained(
            VLM_MODEL_ID,
            trust_remote_code=True
        )
        
        # Load model with quantization
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            VLM_MODEL_ID,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        model.eval()
        print("✅ Qwen2.5-VL model loaded successfully")
        
        return model, processor
    
    def _warmup_models(self):
        """Warm up models with a dummy inference to initialize CUDA context"""
        print("🔥 Warming up models (initializing CUDA context)...")
        import time
        from PIL import Image
        import numpy as np
        
        warmup_start = time.time()
        
        # Create a small dummy image
        dummy_image = Image.fromarray(np.ones((100, 100, 3), dtype=np.uint8) * 255)
        
        try:
            # Warm up VLM
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": dummy_image},
                        {"type": "text", "text": "warm up"}
                    ]
                }
            ]
            
            from qwen_vl_utils import process_vision_info
            text = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )

            device = "cuda" if torch.cuda.is_available() else "cpu"
            inputs = inputs.to(device)
            
            # Run a quick inference
            with torch.no_grad():
                _ = self.vlm_model.generate(**inputs, max_new_tokens=5)
            
            # Clean up
            del inputs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            warmup_time = time.time() - warmup_start
            print(f"✅ Models warmed up in {warmup_time:.2f}s (CUDA context initialized)")
            
        except Exception as e:
            print(f"⚠️ Warmup failed (non-critical): {e}")
    
    def detect_sign_stamp(self, image_path: str):
        """
        Detect signature and stamp in the image using YOLO
        
        Returns:
            tuple: (signature_info, stamp_info, signature_conf, stamp_conf)
        """
        if self.yolo_model is None:
            raise RuntimeError("YOLO model not loaded. Call load_models() first.")
        
        results = self.yolo_model(image_path, verbose=False)[0]
        
        signature_info = {"present": False, "bbox": None}
        stamp_info = {"present": False, "bbox": None}
        signature_conf = 0.0
        stamp_conf = 0.0
        
        if results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                if conf > YOLO_CONFIDENCE_THRESHOLD:
                    bbox = box.xyxy[0].cpu().numpy().tolist()
                    bbox = [int(coord) for coord in bbox]
                    
                    # Class 0: signature, Class 1: stamp
                    if cls_id == 0 and conf > signature_conf:
                        signature_info = {"present": True, "bbox": bbox}
                        signature_conf = conf
                    elif cls_id == 1 and conf > stamp_conf:
                        stamp_info = {"present": True, "bbox": bbox}
                        stamp_conf = conf
        
        return signature_info, stamp_info, signature_conf, stamp_conf
    
    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return (
            self.yolo_model is not None and
            self.vlm_model is not None and
            self.processor is not None
        )


# Global model manager instance
model_manager = ModelManager()