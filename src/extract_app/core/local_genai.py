# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/local_genai.py
# Version: 1.0.0
# Author: Antigravity
# Description: Local LLM Service using llama-cpp-python for TranslateGemma 12B.
# --------------------------------------------------------------------------------

import os
import time
from typing import Optional, Dict, Any, List, Callable

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LocalGenAI:
    """
    Wrapper for local LLM inference using llama-cpp-python.
    Designed for TranslateGemma 12B (GGUF).
    """

    _instance = None
    _model_path: str = ""
    _llm: Optional[Any] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LocalGenAI()
        return cls._instance

    def __init__(self):
        self.model_loaded = False
        
    def load_model(self, model_path: str, n_ctx: int = 8192, n_gpu_layers: int = -1):
        """
        Load the GGUF model into memory/GPU.
        
        Args:
            model_path: Absolute path to .gguf file
            n_ctx: Context window size (default 8192 for Gemma 2)
            n_gpu_layers: Number of layers to offload to GPU (-1 = all, 0 = cpu only)
        """
        if Llama is None:
            raise ImportError("Thư viện 'llama-cpp-python' chưa được cài đặt.")
            
        if self._llm and self._model_path == model_path:
            return  # Already loaded

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy model tại: {model_path}")

        print(f"[LocalLLM] Loading model: {model_path} (GPU Layers: {n_gpu_layers})...")
        
        # Attempt 1: Load with requested configuration (likely with GPU)
        try:
            self._llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            self._model_path = model_path
            self.model_loaded = True
            print("[LocalLLM] Model loaded successfully.")
            return
        except Exception as e:
            print(f"[LocalLLM] Error loading with GPU layers={n_gpu_layers}: {e}")
            
            # Attempt 2: Fallback to CPU if GPU failed and n_gpu_layers was not 0
            if n_gpu_layers != 0:
                print("[LocalLLM] Attempting fallback to CPU (n_gpu_layers=0)...")
                try:
                    self._llm = Llama(
                        model_path=model_path,
                        n_ctx=n_ctx,
                        n_gpu_layers=0, # Force CPU
                        verbose=False
                    )
                    self._model_path = model_path
                    self.model_loaded = True
                    print("[LocalLLM] Model loaded successfully (CPU Fallback).")
                    return
                except Exception as e_cpu:
                    print(f"[LocalLLM] CPU Fallback failed: {e_cpu}")
            
            self.model_loaded = False
            raise e

    def unload_model(self):
        """Free memory by releasing the model."""
        if self._llm:
            del self._llm
            self._llm = None
        self.model_loaded = False
        import gc
        gc.collect()

    def generate_response(self, 
                          system_instruction: str, 
                          prompt: str, 
                          max_tokens: int = 3072,
                          temperature: float = 0.3,
                          stop: List[str] = None) -> Optional[str]:
        """
        Generate response using ChatML/Gemma format.
        """
        if not self._llm:
            return None

        # Construct Prompt (Gemma 2 / ChatML style)
        # Standard Gemma: <start_of_turn>user\n{content}<end_of_turn>\n<start_of_turn>model\n
        
        full_prompt = f"<start_of_turn>user\n{system_instruction}\n\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        
        try:
            output = self._llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["<end_of_turn>", "<start_of_turn>"],
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            print(f"[LocalLLM] Generation error: {e}")
            return None

class LocalTranslationService:
    """
    Service to handle translation using LocalGenAI.
    """
    
    def __init__(self, model_path: str = ""):
        self.engine = LocalGenAI.get_instance()
        self.model_path = model_path

    def translate(self, text: str, 
                  system_instruction: str = "Bạn là biên dịch viên chuyên nghiệp.",
                  glossary: str = "") -> Optional[str]:
        
        # Ensure model is active
        if not self.engine.model_loaded:
            if self.model_path:
                self.engine.load_model(self.model_path)
            else:
                return "Error: Model path not configured."
        
        full_instruction = f"{system_instruction}\n\nLưu ý từ vựng (Glossary):\n{glossary}" if glossary else system_instruction
        
        return self.engine.generate_response(
            system_instruction=full_instruction,
            prompt=f"Hãy dịch văn bản sau sang tiếng Việt:\n\n{text}"
        )
