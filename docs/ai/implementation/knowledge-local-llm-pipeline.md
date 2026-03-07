# Knowledge: Local LLM Translation Pipeline (TranslateGemma)

## 1. Overview
**Entry Point:** `src/extract_app/core/local_genai.py` and `src/extract_app/core/translation_service.py`
**Purpose:** Handles offline translation of EPUB/PDF texts using local GGUF models via `llama.cpp`. 
**Language:** Python
**Key Insight:** Local LLM translation is fundamentally different from Cloud LLM (Gemini). Smaller local models like `translategemma-12b-it` require highly deterministic, aggressive prompting, and strictly clean input contexts without overlapping noise.

## 2. Implementation Details

### A. Model Selection & Configuration (`local_genai.py`)
- **Correct Model:** Must be `translategemma-12b-it.*.gguf`, **not** a generic chat model (`gemma-2-9b-it`). Chat models will hallucinate English summaries and attempt to converse rather than directly translate.
- **Quantization:**
  - `Q4_K_M` (~7GB): Recommended for standard 8GB-12GB VRAM GPUs (Speed: ~12 tokens/sec).
  - `Q6_K` (~10GB): Recommended for 16GB+ VRAM or high-end setups (Higher quality but requires more VRAM to run entirely on GPU).
- **Generation Parameters:**
  - `max_tokens=4096`: Vietnamese translation often expands to 130% of the English source length. Earlier defaults (3072) caused premature truncation on 1500-char input chunks.
  - `temperature=0.15`: Kept low to enforce strict adherence to the glossary and avoid creative hallucinations.

### B. Prompt Engineering Strategy
Local models struggle with multi-constraint zero-shot translation. The `STRICT_SYSTEM_PROMPT` had to be rewritten from "polite requests" to "aggressive commands" to counteract the model's tendency to sanitize the text:
```python
"BẢO TỒN NGUYÊN VẸN PLACEHOLDER: Bất kỳ cụm từ nào có dạng __IMG_000__... PHẢI ĐƯỢC CHÉP LẠI Y HỆT vào bản dịch, đúng vị trí tương ứng. TUYỆT ĐỐI KHÔNG ĐƯỢC XÓA."
```
*Without this strict instruction, TranslateGemma Q4_K_M silently removes image placeholders `__IMG_...__`, assuming they are OCR artifacts.*

### C. Context Chunking (`translation_service.py`)
- **No Overlap Context:** Injecting text from the *previous* chunk (e.g., 400 chars) to maintain literary coherence works for GPT-4/Gemini, but **fails** for 12B local models. It causes the local model to hallucinate and selectively translate parts of the overlap instead of the new chunk.
- **Clean Input:** The solution was to pass pure, disjoint chunks (`chunk_size=1500`) and rely on the active Dictionary/Glossary to maintain terminology coherence across chunks.

### D. Glossary Injection
- **Injection Method:** The active category's terms are fetched from `GlossaryManager` and appended directly into the System Prompt before generation:
  `"TỪ VỰNG BẮT BUỘC (Glossary):\n'term' : 'bản dịch'"`
- **Performance:** For Bulk insertion (e.g., when the AI Glossary Extractor returns 50 terms), `GlossaryManager.bulk_add_terms(dict)` must be used to perform processing in RAM and hit the disk (`glossary.json`) exactly once. Sequential `add_term` calls will cause massive I/O bottlenecks and UI freezing, particularly on HDD drives.

## 3. Dependencies
- **Core Engine:** `llama_cpp.Llama` (Requires correct `llama-cpp-python` wheels compiled with cuBLAS for GPU acceleration).
- **Service Layer:** `GlossaryManager` (Handles JSON disk storage and category tracking).
- **Architecture:** 
  `LibraryView (UI Thread)` -> `TranslationWorker (Background Thread)` -> `TranslationService` -> `LocalGenAI` -> `llama_cpp`.

## 4. Additional Insights & Risks
- **Hardware Fallback Risk:** If `n_gpu_layers=-1` is set but the VRAM is insufficient to hold the selected model (e.g., loading Q6_K on an 8GB GPU), `llama.cpp` will quietly offload the remainder to CPU RAM. This causes translation speed to plummet from 15 t/s down to 3-4 t/s without clear error logs. 
- **Diagnostic Tool:** Provided `diagnose_local_llm.py` in the root folder to benchmark VRAM and token generation speed.

## 5. Metadata
- **Analysis Date:** 2026-03-07
- **Depth:** Deep architectural dive into the Local LLM orchestration.
- **Key Files Touched:** `src/extract_app/core/local_genai.py`, `src/extract_app/core/translation_service.py`, `src/extract_app/core/glossary_manager.py`.

## 6. Next Steps
- Consider upgrading the diagnostic print statements to a formal `logging` module mechanism.
- Investigate deploying smaller embedded models (like Qwen2 1.5B) purely for UI/Title translation tasks to save overhead.
