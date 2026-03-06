# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/translation_service.py
# Version: 3.0.0
# Author: Antigravity
# Description: Hybrid Translation Service (Cloud + Local).
# --------------------------------------------------------------------------------

import time
import re
import logging
import google.generativeai as genai
from typing import Optional, List, Callable, Tuple

from .local_genai import LocalTranslationService
from .style_manager import StyleManager
from .glossary_manager import GlossaryManager

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
        self.glossary_manager = GlossaryManager()
        
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
        """Split text into chunks, preferring Markdown header boundaries.
        
        Strategy:
        1. Split by Markdown headings (## or ###) to keep sub-sections intact.
        2. If a sub-section exceeds chunk_size, fallback to paragraph splitting.
        3. Merge small adjacent sections if they fit within chunk_size.
        """
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        if len(text) <= chunk_size:
            return [text]
        
        # Step 1: Split by Markdown headings (## or ###, but not # which is article title)
        # Each section starts with a heading line
        sections = re.split(r'(?=\n#{2,3} )', text)
        sections = [s.strip() for s in sections if s.strip()]
        
        # Step 2: Process sections — split oversized ones by paragraphs
        processed_sections = []
        for section in sections:
            if len(section) <= chunk_size:
                processed_sections.append(section)
            else:
                # Fallback: split this large section by paragraphs
                paragraphs = re.split(r'\n\n+', section)
                sub_chunk = []
                sub_size = 0
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    if sub_size + len(para) > chunk_size and sub_chunk:
                        processed_sections.append('\n\n'.join(sub_chunk))
                        sub_chunk = [para]
                        sub_size = len(para)
                    else:
                        sub_chunk.append(para)
                        sub_size += len(para)
                if sub_chunk:
                    processed_sections.append('\n\n'.join(sub_chunk))
        
        # Step 3: Merge small adjacent sections to reduce API calls
        chunks = []
        current_chunk = []
        current_size = 0
        
        for section in processed_sections:
            section_size = len(section)
            if current_size + section_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [section]
                current_size = section_size
            else:
                current_chunk.append(section)
                current_size += section_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [text]

    def _translate_cloud_chunk(self, text: str, retries: int = MAX_RETRIES) -> Tuple[Optional[str], Optional[str]]:
        """Translate single chunk using Gemini Cloud with Fallback."""
        if not self.api_key or not self.cloud_model:
            return None, "API Key chưa được cấu hình"

        glossary_str = self.glossary_manager.get_active_glossary_string()
        glossary_prompt = f"7. TỪ VỰNG BẮT BUỘC:\n{glossary_str}\n" if glossary_str else ""

        prompt = (
            "<SYSTEM>\n"
            "Bạn là một phần mềm dịch thuật tự động Anh-Việt.\n"
            "NHIỆM VỤ DUY NHẤT: Dịch văn bản bên dưới sang tiếng Việt.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. CHỈ trả về bản dịch tiếng Việt thuần túy. TUYỆT ĐỐI KHÔNG giải thích, KHÔNG ghi chú, KHÔNG bình luận, KHÔNG thêm tiêu đề 'Bản dịch'.\n"
            "2. KHÔNG viết câu mở đầu kiểu 'Dưới đây là bản dịch...' hay câu kết kiểu 'Lưu ý:...'.\n"
            "3. Giữ nguyên cấu trúc đoạn văn và xuống dòng của bản gốc.\n"
            "4. Giữ nguyên Markdown formatting (##, **, -, v.v.) nếu có.\n"
            "5. Giữ nguyên mọi placeholder __IMG_XXX__ — KHÔNG dịch, KHÔNG xóa chúng.\n"
            "6. Dịch sát nghĩa, tự nhiên, phù hợp ngữ cảnh sách non-fiction.\n"
            f"{glossary_prompt}"
            "</SYSTEM>\n\n"
            f"{text}"
        )

    def extract_glossary_from_text(self, text: str, subject: str = "tổng hợp") -> Tuple[Optional[List[dict]], Optional[str]]:
        """
        Uses Cloud LLM (Gemini) to extract key domain-specific terms from a sample text
        and return them as a JSON array of dicts: [{"en": "term", "vi": "translation"}].
        """
        if not self.api_key or not self.cloud_model:
            return None, "Vui lòng cấu hình Cloud API Key (Gemini) trong Cài đặt để sử dụng tính năng này."

        prompt = (
            f"Bạn là một chuyên gia ngôn ngữ học và dịch giả chuyên ngành [{subject}].\n"
            "Nhiệm vụ của bạn là đọc đoạn văn bản tiếng Anh dưới đây và trích xuất ra danh sách "
            "các thuật ngữ chuyên ngành, danh từ riêng hoặc các từ khóa quan trọng nhất, "
            "sau đó đưa ra bản dịch tiếng Việt chuẩn xác nhất cho ngữ cảnh đó.\n\n"
            "YÊU CẦU BẮT BUỘC:\n"
            "1. Chỉ trích xuất tối đa 30-50 từ vựng quan trọng nhất.\n"
            "2. Trả về KẾT QUẢ DUY NHẤT LÀ MỘT MẢNG JSON HỢP LỆ, không có Markdown backticks (```json), không giải thích thêm.\n"
            "3. Format JSON yêu cầu:\n"
            '[\n  {"en": "từ tiếng anh gốc", "vi": "bản dịch tiếng việt"}\n]\n\n'
            "VĂN BẢN GỐC:\n"
            f"{text[:15000]}" # Limit to 15k chars to save tokens and prevent huge JSONs
        )

        try:
            # We enforce JSON output directly via generation_config if supported, or via prompt
            response = self.cloud_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1, # Low temp for deterministic extraction
                )
            )
            raw_text = response.text.strip()
            
            # Clean potential markdown backticks
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            import json
            terms = json.loads(raw_text.strip())
            if isinstance(terms, list):
                return terms, None
            else:
                return None, "Gemini không trả về định dạng mảng JSON hợp lệ."
                
        except json.JSONDecodeError as e:
            return None, f"Lỗi parse JSON từ AI: {e}\nRaw output: {raw_text[:100]}..."
        except Exception as e:
            return None, f"Lỗi kết nối Gemini: {e}"

        generation_config = genai.GenerationConfig(
            temperature=0.3,
            top_p=0.9,
        )
        
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
                        response = current_model.generate_content(
                            prompt,
                            generation_config=generation_config
                        )
                        if response.text:
                            cleaned = self._clean_translation_output(response.text)
                            return cleaned, None
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
             
        # Inject Glossary support
        glossary = self.glossary_manager.get_active_glossary_string()
        
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
                # Apply same post-processing as Cloud to clean AI artifacts
                cleaned = self._clean_translation_output(result)
                return cleaned, None
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
        
        # Local model needs slightly larger chunks to avoid cutting mid-sentence.
        # TranslateGemma 12B has 8192 token context; 1500 chars ~ 500 tokens source + 800 tokens output.
        if engine == "local":
            chunk_size = min(chunk_size, 1500) 
            
        # Protect Anchors
        protected_text, anchors_map = self._protect_anchors(text)
            
        chunks = self.chunk_text(protected_text, chunk_size)
        total = len(chunks)
        results = [None] * total # Preserve order
        
        if progress_callback:
            progress_callback(0, total, f"Engine: {engine.upper()} | Chunks: {total}")
        
        if engine == "local":
            # Local must be sequential — send each chunk cleanly, no overlap context
            # (TranslateGemma 12B cannot reliably follow 'translate only this part' instructions)
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(i + 1, total, f"Dịch phần {i + 1}/{total} (Local)...")
                
                res, err = self._translate_local_chunk(chunk)
                if err:
                    print(f"[Local] Error chunk {i}: {err}")
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

    def transform_text(self, archive_text: str, original_text: str, variant_type: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Transform an archive translation into a Website or Facebook variant.
        Uses the archive_text as the primary source; original_text for reference.
        """
        if not self.api_key or not self.cloud_model:
            return None, "API Key chưa được cấu hình"

        if variant_type == 'website':
            prompt = (
                "<SYSTEM>\n"
                "Bạn là biên tập viên website chuyên nghiệp.\n"
                "NHIỆM VỤ: Biên tập lại bản dịch tiếng Việt bên dưới thành bài viết website.\n\n"
                "QUY TẮC:\n"
                "1. CHỈ trả về bài viết đã biên tập. KHÔNG giải thích, KHÔNG ghi chú.\n"
                "2. Thêm tiêu đề H2 (##) cho các phần chính, H3 (###) cho phần phụ.\n"
                "3. Chia đoạn văn ngắn (2-4 câu), sử dụng bullet points khi liệt kê.\n"
                "4. Văn phong mạch lạc, chuyên nghiệp nhưng không khô khan.\n"
                "5. Giữ nguyên mọi placeholder __IMG_XXX__ và [Image Anchor:].\n"
                "</SYSTEM>\n\n"
                f"{archive_text}"
            )
        elif variant_type == 'facebook':
            # Load Gem persona from markdown files
            gem_instructions = self._load_gem_style_files()
            prompt = (
                "<SYSTEM>\n"
                f"{gem_instructions}\n\n"
                "NHIỆM VỤ: Chuyển thể bản dịch bên dưới thành bài viết Facebook theo phong cách Gem.\n"
                "CHỈ trả về nội dung bài viết. KHÔNG giải thích thêm.\n"
                "</SYSTEM>\n\n"
                "--- BẢN DỊCH GỐC ---\n"
                f"{archive_text}\n\n"
                "--- VĂN BẢN TIẾNG ANH (THAM KHẢO) ---\n"
                f"{original_text[:3000]}"
            )
        else:
            return None, f"Unknown variant type: {variant_type}"

        generation_config = genai.GenerationConfig(
            temperature=0.7 if variant_type == 'facebook' else 0.4,
            top_p=0.95,
        )

        try:
            model_name = self.settings.get('cloud_model_name', 'gemini-2.5-flash')
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config=generation_config)
            if response.text:
                cleaned = self._clean_translation_output(response.text)
                return cleaned, None
            return None, "Empty response from AI"
        except Exception as e:
            return None, str(e)

    def _load_gem_style_files(self) -> str:
        """Load Gem persona from scripts/gem_dich/*.md files."""
        from pathlib import Path
        gem_dir = Path("scripts/gem_dich")
        files_order = [
            "nhancachcotloi.md",
            "bocongcusangtao.md",
            "anti_ai_style.md",
            "sangtaotieude.md",
            "thuviendochuyennganh.md",
        ]
        parts = []
        for fname in files_order:
            fpath = gem_dir / fname
            if fpath.exists():
                try:
                    parts.append(fpath.read_text(encoding='utf-8'))
                except:
                    pass
        if parts:
            return "\n\n---\n\n".join(parts)
        # Fallback to inline style
        return self.style_manager.get_style_instruction("facebook_gem")


    def _clean_translation_output(self, text: str) -> str:
        """Clean AI output: strip preambles, code fences, trailing notes."""
        result = text.strip()
        
        # 1. Remove code fences if AI wrapped output in ```
        result = re.sub(r'^```[a-zA-Z]*\n?', '', result)
        result = re.sub(r'\n?```$', '', result)
        
        # 2. Remove common preambles (Vietnamese and English)
        preamble_patterns = [
            r'^(?:D\u01b0\u1edbi \u0111\u00e2y l\u00e0|B\u1ea3n d\u1ecbch|Here is|Translation|\*\*B\u1ea3n d\u1ecbch\*\*)[^\n]*\n+',
            r'^(?:##?\s*B\u1ea3n d\u1ecbch[^\n]*)\n+',
        ]
        for pattern in preamble_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # 3. Remove trailing notes
        trailing_patterns = [
            r'\n+(?:L\u01b0u \u00fd|Note|Ghi ch\u00fa|\*\*L\u01b0u \u00fd\*\*)[:\s].*$',
            r'\n+---\n+.*$',
        ]
        for pattern in trailing_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)
        
        # 4. Normalize whitespace: collapse 3+ newlines to 2, strip trailing spaces per line
        lines = result.split('\n')
        lines = [line.rstrip() for line in lines]
        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()

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
        import re
        restored_text = text
        for placeholder, original in mapping.items():
            if placeholder in restored_text:
                restored_text = restored_text.replace(placeholder, original)
            else:
                # Try relaxed matching for AI mutated placeholders
                # Original placeholder: __IMG_001__
                # Mutations to catch: _IMG_001_, IMG_001, __ IMG _ 001 __, etc.
                if placeholder.startswith("__IMG_") and placeholder.endswith("__"):
                    idx = placeholder[6:-2] # get the 001 part
                    # Build regex to find variations
                    pattern = r'_*\s*IMG\s*_*\s*' + idx + r'\s*_*'
                    restored_text = re.sub(pattern, original, restored_text, flags=re.IGNORECASE)
                
        return restored_text
