# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/translation_service.py
# Version: 4.0.0 (facade refactor)
# Author: Antigravity
# Description: Hybrid Translation Service — now a thin orchestration facade.
#
#   The heavy lifting has been split into focused sub-modules:
#     - ChunkingStrategy  (chunking_strategy.py) — text splitting & anchor protection
#     - PromptBuilder     (prompt_builder.py)     — all prompt templates & output cleaning
#     - CloudAIClient     (cloud_client.py)       — Gemini API wrapper with fallback
#   This file coordinates those helpers plus the local LLM service.
# --------------------------------------------------------------------------------

import time
import logging
from pathlib import Path
from typing import Optional, List, Callable, Tuple

from .chunking_strategy import ChunkingStrategy
from .prompt_builder import PromptBuilder
from .cloud_client import CloudAIClient
from .local_genai import LocalTranslationService
from .style_manager import StyleManager
from .glossary_manager import GlossaryManager

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Hybrid Translation Service.
    Routes requests to Google Gemini (Cloud) or TranslateGemma (Local).

    Public API (unchanged from v3):
        translate_text(text, chunk_size, delay, progress_callback) -> str | None
        transform_text(archive_text, original_text, variant_type)  -> (str, err)
        extract_glossary_from_text(text, subject)                  -> (list, err)
        set_api_key(key)
        cloud_model  (property for backward-compat UI checks)
        api_key      (property)
    """

    MAX_CLOUD_WORKERS = 3

    def __init__(self, settings_manager):
        self.settings = settings_manager

        # Sub-modules
        self.chunker = ChunkingStrategy()
        self.prompt_builder = PromptBuilder()
        self.cloud_client = CloudAIClient(settings_manager)
        self.local_service = LocalTranslationService()
        self.style_manager = StyleManager()
        self.glossary_manager = GlossaryManager()

    # ── Backward-compat properties ────────────────────────────────────

    @property
    def api_key(self) -> str:
        return self.cloud_client.api_key

    @property
    def cloud_model(self):
        """Legacy attribute – widgets check `if service.cloud_model` to know if cloud is ready."""
        return self.cloud_client if self.cloud_client.is_ready else None

    def set_api_key(self, api_key: str) -> None:
        """Update API Key at runtime."""
        self.cloud_client.setup(api_key)

    # ── Main translation entry point ──────────────────────────────────

    def translate_text(
        self,
        text: str,
        chunk_size: int = None,
        delay: float = None,
        progress_callback: Callable[[int, int, str], None] = None,
    ) -> Optional[str]:
        """Translate *text* from English to Vietnamese.

        Uses Cloud (Gemini) or Local (TranslateGemma) depending on settings.
        Supports parallel Cloud execution via ThreadPoolExecutor.
        """
        import concurrent.futures

        engine = self.settings.get("translation_engine", "cloud")

        # Determine effective chunk size
        if engine == "cloud":
            chunk_size = chunk_size or 15000  # Large context is fine for Gemini
        else:
            # Local LLM: leave comfortable headroom within 4096-token context
            chunk_size = min(chunk_size or self.settings.get("chunk_size", 3000), 1500)

        # Protect image anchors before chunking
        protected_text, anchors_map = self.chunker.protect_anchors(text)
        chunks = self.chunker.chunk_text(protected_text, chunk_size)
        total = len(chunks)
        results: List[Optional[str]] = [None] * total

        if progress_callback:
            progress_callback(0, total, f"Engine: {engine.upper()} | Chunks: {total}")

        if engine == "local":
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(i, total, f"Đang dịch phần {i + 1}/{total} (Local)...")
                res, err = self._translate_local_chunk(chunk)
                if err:
                    logger.error(f"[Local] Chunk {i} error: {err}")
                    return None
                results[i] = res
                if progress_callback:
                    progress_callback(i + 1, total, f"Đã dịch {i + 1}/{total} (Local)...")
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_CLOUD_WORKERS) as exc:
                future_to_idx = {
                    exc.submit(self._translate_cloud_chunk, chunk): idx
                    for idx, chunk in enumerate(chunks)
                }
                completed = 0
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        res, err = future.result()
                        if err:
                            logger.error(f"[Cloud] Chunk {idx} error: {err}")
                            return None
                        results[idx] = res
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total, f"Đã dịch {completed}/{total} (Cloud)...")
                    except Exception as e:
                        logger.error(f"[Cloud] Execution error: {e}")
                        return None

        if progress_callback:
            progress_callback(total, total, "Hoàn thành!")

        full_translation = "\n\n".join(r for r in results if r)
        return self.chunker.restore_anchors(full_translation, anchors_map)

    # ── Style transformation ──────────────────────────────────────────

    def transform_text(
        self, archive_text: str, original_text: str, variant_type: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Transform an archive translation into a Website or Facebook variant."""
        if not self.cloud_client.is_ready:
            return None, "API Key chưa được cấu hình"

        gem_instructions = ""
        if variant_type == "facebook":
            gem_instructions = self._load_gem_style_files()

        temperature = 0.7 if variant_type == "facebook" else 0.4
        prompt = self.prompt_builder.build_transform_prompt(
            archive_text, original_text, variant_type, gem_instructions
        )
        if prompt is None:
            return None, f"Unknown variant type: {variant_type}"

        return self.cloud_client.transform(prompt, temperature=temperature)

    # ── Glossary extraction ───────────────────────────────────────────

    def extract_glossary_from_text(
        self, text: str, subject: str = "tổng hợp"
    ) -> Tuple[Optional[List[dict]], Optional[str]]:
        """Ask Gemini to extract domain-specific terms for the glossary."""
        return self.cloud_client.extract_glossary_json(text, subject)

    # ── Internal helpers ──────────────────────────────────────────────

    def _translate_cloud_chunk(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Route a single chunk to the Cloud AI client."""
        glossary_str = self.glossary_manager.get_active_glossary_string()
        return self.cloud_client.translate_chunk(text, glossary_str)

    def _translate_local_chunk(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Route a single chunk to the Local LLM."""
        model_path = self.settings.get("local_model_path", "")
        n_gpu = self.settings.get("n_gpu_layers", -1)

        if not model_path:
            return None, "Chưa chọn file Model Local (.gguf)"

        try:
            engine = self.local_service.engine
            if not engine.model_loaded or engine._model_path != model_path:
                engine.load_model(model_path, n_gpu_layers=n_gpu)
        except Exception as e:
            return None, f"Lỗi load model: {e}"

        style_name = self.settings.get("current_style", "standard")
        try:
            instruction = self.style_manager.get_style_instruction(style_name)
        except Exception:
            instruction = "Bạn là biên dịch viên chuyên nghiệp. Hãy dịch văn bản sau sang tiếng Việt."

        glossary = self.glossary_manager.get_relevant_glossary_string(text)

        try:
            result = self.local_service.translate(text, system_instruction=instruction, glossary=glossary)
            if result:
                return self.prompt_builder.clean_output(result), None
            return None, "Local generation returned empty result."
        except Exception as e:
            return None, f"Local Inference Error: {e}"

    def _load_gem_style_files(self) -> str:
        """Load Gem persona from scripts/gem_dich/*.md files."""
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
                except Exception:
                    pass
        return "\n\n---\n\n".join(parts) if parts else self.style_manager.get_style_instruction("facebook_gem")

    # ── Legacy shims (kept so old callers don't break) ────────────────

    def chunk_text(self, text: str, chunk_size: int = None) -> List[str]:
        """Deprecated shim — delegates to ChunkingStrategy."""
        return self.chunker.chunk_text(text, chunk_size or 3000)

    def _clean_translation_output(self, text: str) -> str:
        """Deprecated shim — delegates to PromptBuilder."""
        return self.prompt_builder.clean_output(text)
