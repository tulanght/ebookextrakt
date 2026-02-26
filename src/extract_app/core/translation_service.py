# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/translation_service.py
# Version: 3.0.0
# Author: Antigravity
# Description: Hybrid Translation Service (Cloud + Local).
# --------------------------------------------------------------------------------

import time
import re
import google.generativeai as genai
from typing import Optional, List, Callable, Tuple

from .local_genai import LocalTranslationService
from .style_manager import StyleManager

class TranslationService:
    """
    Hybrid Translation Service.
    Routes requests to Google Gemini (Cloud) or TranslateGemma (Local).
    """
    
    DEFAULT_CHUNK_SIZE = 3000
    DEFAULT_DELAY = 1.0
    MAX_RETRIES = 3
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.style_manager = StyleManager()
        
        # Cloud Setup
        self.api_key = self.settings.get_api_key()
        self.cloud_model = None
        self._setup_cloud()
        
        # Local Setup
        self.local_service = LocalTranslationService()

    def _setup_cloud(self):
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model_name = self.settings.get('cloud_model_name', 'gemini-1.5-pro')
                self.cloud_model = genai.GenerativeModel(model_name)
            except Exception as e:
                print(f"[Translation] Cloud setup error: {e}")

    def set_api_key(self, api_key: str):
        """Update API Key at runtime."""
        self.api_key = api_key
        self._setup_cloud()

    def chunk_text(self, text: str, chunk_size: int = None) -> List[str]:
        """Split text into chunks by paragraphs."""
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        if len(text) <= chunk_size:
            return [text]
        
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para: continue
            
            para_size = len(para)
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [text]

    def _translate_cloud_chunk(self, text: str, retries: int = MAX_RETRIES) -> Tuple[Optional[str], Optional[str]]:
        """Translate single chunk using Gemini Cloud with Fallback."""
        if not self.api_key or not self.cloud_model:
            return None, "API Key chưa được cấu hình"

        prompt = f"""Bạn là biên dịch viên chuyên nghiệp. Dịch văn bản sau sang tiếng Việt.
Yêu cầu: Sát nghĩa, tự nhiên, giữ nguyên Markdown và thuật ngữ.
Văn bản:
---
{text}
---"""
        
        # Get current model name to try first
        primary_model_name = self.settings.get('cloud_model_name', 'gemini-2.5-pro')
        
        # List of models to try in order
        models_to_try = [primary_model_name]
        
        # Add fallbacks if they are not the primary
        # Prioritize newer models found in user's environment
        fallbacks = [
            'gemini-2.5-pro', 
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
            'gemini-1.5-pro', 
            'gemini-1.5-flash'
        ]
        for fb in fallbacks:
            if fb != primary_model_name and fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        
        for model_name in models_to_try:
            # Re-configure model if we are switching or just to be safe
            try:
                current_model = genai.GenerativeModel(model_name)
                
                # Try generation with retries for THIS model
                for attempt in range(retries):
                    try:
                        response = current_model.generate_content(prompt)
                        if response.text:
                            return response.text.strip(), None
                    except Exception as e:
                        last_error = str(e)
                        if "429" in last_error or "Quota" in last_error:
                            time.sleep(5)
                        else:
                            # If it's a 404 (model not found) or 400, break for-loop to try next model immediately
                            if "404" in last_error or "not found" in last_error.lower():
                                break 
                            time.sleep(1)
                            
                # If we get here, retries for this model exhausted or hit non-retryable error
                print(f"[Translation] Model {model_name} failed: {last_error}. Trying next...")
                
            except Exception as e:
                print(f"[Translation] Failed to init model {model_name}: {e}")
                last_error = str(e)

        return None, f"All models failed. Last error: {last_error}"

    def _translate_local_chunk(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Translate single chunk using Local LLM."""
        model_path = self.settings.get("local_model_path", "")
        n_gpu = self.settings.get("n_gpu_layers", -1)
        
        if not model_path:
            return None, "Chưa chọn file Model Local (.gguf)"
        
        # Load model if not loaded or path changed
        # Note: LocalGenAI handles the singleton logic, but we should pass params
        try:
            if not self.local_service.engine.model_loaded or self.local_service.engine._model_path != model_path:
                 self.local_service.engine.load_model(model_path, n_gpu_layers=n_gpu)
        except Exception as e:
             return None, f"Lỗi load model: {e}"

        style_name = self.settings.get("current_style", "standard")
        # Ensure we have a valid instruction even if style manager fails
        try:
            instruction = self.style_manager.get_style_instruction(style_name)
        except:
             instruction = "Bạn là biên dịch viên chuyên nghiệp. Hãy dịch văn bản sau sang tiếng Việt."
             
        # Optional: Glossary support
        glossary = "" # Placeholder for future glossary manager integration
        
        try:
            # We call the engine directly now or via wrapper? 
            # The wrapper `LocalTranslationService` in local_genai.py simplifies this.
            # Let's use the wrapper's translate method which handles prompt construction
            result = self.local_service.translate(
                text, 
                system_instruction=instruction, 
                glossary=glossary
            )
            
            if result:
                return result, None
            else:
                return None, "Local generation returned empty result."
        except Exception as e:
            return None, f"Local Inference Error: {e}"

    def translate_text(self, text: str, 
                       chunk_size: int = None,
                       delay: float = None,
                       progress_callback: Callable[[int, int, str], None] = None) -> Optional[str]:
        """
        Main translation entry point. Supports parallel execution for Cloud and larger chunks.
        """
        import concurrent.futures
        
        engine = self.settings.get("translation_engine", "cloud")
        
        # Increase chunk size for Cloud to leverage context and speed
        if engine == "cloud" and not chunk_size:
            chunk_size = 15000 # 5x larger than default
        else:
            chunk_size = chunk_size or self.settings.get("chunk_size", 3000)
        
        # Local model typically needs smaller chunks
        if engine == "local":
            chunk_size = min(chunk_size, 2000) 
            
        # Protect Anchors
        protected_text, anchors_map = self._protect_anchors(text)
            
        chunks = self.chunk_text(protected_text, chunk_size)
        total = len(chunks)
        results = [None] * total # Preserve order
        
        if progress_callback:
            progress_callback(0, total, f"Engine: {engine.upper()} | Chunks: {total}")
            
        if engine == "local":
            # Local must be sequential
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(i + 1, total, f"Dịch phần {i + 1}/{total} (Local)...")
                
                res, err = self._translate_local_chunk(chunk)
                if err:
                    print(f"Error chunk {i}: {err}")
                    return None
                results[i] = res
        else:
            # Cloud can be parallel
            # We use 3 workers as a safe default for free tier/low latency
            MAX_CLOUD_WORKERS = 3 
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CLOUD_WORKERS) as executor:
                future_to_idx = {executor.submit(self._translate_cloud_chunk, chunk): i for i, chunk in enumerate(chunks)}
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        res, err = future.result()
                        if err:
                            print(f"Cloud Chunk {idx} Error: {err}")
                            return None
                        results[idx] = res
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total, f"Đã dịch {completed}/{total} (Cloud)...")
                    except Exception as e:
                        print(f"Cloud Execution Error: {e}")
                        return None
                        
        if progress_callback:
            progress_callback(total, total, "Hoàn thành!")
            
        full_translation = "\n\n".join(results)
        
        # Restore Anchors
        final_text = self._restore_anchors(full_translation, anchors_map)
        
        return final_text

    def _protect_anchors(self, text: str) -> Tuple[str, dict]:
        """Replaces [Image: ...] tags with safely translatable placeholders."""
        import re
        anchor_pattern = r'\[Image:.*?\]'
        anchors = re.findall(anchor_pattern, text)
        mapping = {}
        
        protected_text = text
        for i, anchor in enumerate(anchors):
            # Use a placeholder that AI is unlikely to translate or break
            # __IMG_001__ is safer than "Image 1" which might get translated to "Hình ảnh 1"
            placeholder = f"__IMG_{i:03d}__"
            mapping[placeholder] = anchor
            # Replace only the first occurrence to handle duplicates correctly if any (though unlikely for exact same anchor string)
            protected_text = protected_text.replace(anchor, placeholder, 1)
            
        return protected_text, mapping

    def _restore_anchors(self, text: str, mapping: dict) -> str:
        """Restores placeholders back to original anchor tags."""
        restored_text = text
        for placeholder, original in mapping.items():
            # Support case where AI might have added spaces or punctuation
            # Check strictly first
            if placeholder in restored_text:
                restored_text = restored_text.replace(placeholder, original)
            else:
                # Try relaxed matching (maybe AI removed underscores?)
                # For now, simplistic. If missing, we might have lost an image.
                # Let's try to handle common AI mutations:
                # __ IMG _ 001 __
                # IMG_001
                pass
                
        return restored_text
