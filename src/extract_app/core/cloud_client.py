# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/cloud_client.py
# Version: 1.0.0
# Author: Antigravity
# Description: Thin wrapper around the Google Generative AI SDK.
#              Handles model initialisation, multi-model fallback and retries.
# --------------------------------------------------------------------------------

import json
import time
import logging
from typing import Optional, List, Tuple

import google.generativeai as genai

from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# Ordered fallback chain — primary is selected at runtime from settings.
FALLBACK_MODELS = [
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-pro',
    'gemini-1.5-flash',
]

MAX_RETRIES = 3


class CloudAIClient:
    """
    Manages the Gemini API connection and exposes three high-level operations:
      - translate_chunk   : single-chunk translation (EN → VI)
      - transform         : style transformation (archive → website/facebook)
      - extract_glossary  : AI-driven glossary term extraction
    """

    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.prompt_builder = PromptBuilder()
        self.api_key: str = ""
        self._configured = False
        self.setup(settings_manager.get_api_key())

    # ─────────────────────────────────────────────────────────────────
    # Setup
    # ─────────────────────────────────────────────────────────────────

    def setup(self, api_key: str) -> None:
        """Configure the SDK with the given API key."""
        self.api_key = api_key
        self._configured = False
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self._configured = True
            except Exception as e:
                logger.error(f"[CloudAIClient] SDK configuration error: {e}")

    @property
    def is_ready(self) -> bool:
        return bool(self.api_key and self._configured)

    # ─────────────────────────────────────────────────────────────────
    # Translation
    # ─────────────────────────────────────────────────────────────────

    def translate_chunk(
        self, text: str, glossary_str: str = ""
    ) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
        """Translate a single text chunk (EN → VI) with model fallback.

        Returns:
            (translated_text, usage_dict, error_message)
        """
        if not self.is_ready:
            return None, None, "API Key chưa được cấu hình"

        prompt = self.prompt_builder.build_translation_prompt(text, glossary_str)
        generation_config = genai.GenerationConfig(temperature=0.3, top_p=0.9)

        return self._call_with_fallback(prompt, generation_config)

    # ─────────────────────────────────────────────────────────────────
    # Style transformation
    # ─────────────────────────────────────────────────────────────────

    def transform(
        self, prompt: str, temperature: float = 0.5
    ) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
        """Send an already-built prompt to Gemini.

        Returns:
            (result_text, usage_dict, error_message)
        """
        if not self.is_ready:
            return None, None, "API Key chưa được cấu hình"

        generation_config = genai.GenerationConfig(temperature=temperature, top_p=0.95)
        return self._call_with_fallback(prompt, generation_config)

    # ─────────────────────────────────────────────────────────────────
    # Glossary extraction
    # ─────────────────────────────────────────────────────────────────

    def extract_glossary_json(
        self, text: str, subject: str = "tổng hợp"
    ) -> Tuple[Optional[List[dict]], Optional[dict], Optional[str]]:
        """Ask Gemini to extract domain-specific terms as a JSON array.

        Returns:
            (terms_list, usage_dict, error_message)
        """
        if not self.is_ready:
            return None, None, "Vui lòng cấu hình Cloud API Key (Gemini) trong Cài đặt."

        prompt = self.prompt_builder.build_glossary_extraction_prompt(text, subject)
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-flash')

        try:
            model = genai.GenerativeModel(primary)
            raw = ""
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.1),
            )
            raw = response.text.strip()

            # Strip optional markdown fences
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]

            terms = json.loads(raw.strip())
            if isinstance(terms, list):
                return terms, self._extract_usage(response), None
            return None, None, "Gemini không trả về định dạng mảng JSON hợp lệ."
        except json.JSONDecodeError as e:
            return None, None, f"Lỗi parse JSON từ AI: {e}"
        except Exception as e:
            return None, None, f"Lỗi kết nối Gemini: {e}"

    # ─────────────────────────────────────────────────────────────────
    # Content Brief Generation
    # ─────────────────────────────────────────────────────────────────

    def generate_content_brief_json(
        self, text: str
    ) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
        """Ask Gemini to generate an SEO Content Brief as a JSON object.

        Returns:
            (brief_dict, usage_dict, error_message)
        """
        if not self.is_ready:
            return None, None, "Vui lòng cấu hình Cloud API Key (Gemini) trong Cài đặt."

        prompt = self.prompt_builder.build_content_brief_prompt(text)
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-flash')

        try:
            model = genai.GenerativeModel(primary)
            raw = ""
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.3, response_mime_type="application/json"),
            )
            raw = response.text.strip()

            brief = json.loads(raw)
            if isinstance(brief, dict):
                return brief, self._extract_usage(response), None
            return None, None, "Gemini không trả về định dạng Object JSON hợp lệ."
        except json.JSONDecodeError as e:
            return None, None, f"Lỗi parse JSON từ AI: {e}\nRaw Response: {raw[:100]}..."
        except Exception as e:
            return None, None, f"Lỗi kết nối Gemini: {e}"

    # ─────────────────────────────────────────────────────────────────
    # Keyword Cluster Generation
    # ─────────────────────────────────────────────────────────────────

    def generate_keyword_cluster_json(
        self, pillar_keyword: str, context: str = ""
    ) -> Tuple[Optional[List[dict]], Optional[dict], Optional[str]]:
        """Ask Gemini to generate a Topic Cluster as a JSON array.

        Returns:
            (cluster_list, usage_dict, error_message)
        """
        if not self.is_ready:
            return None, None, "Vui lòng cấu hình Cloud API Key (Gemini) trong Cài đặt."

        prompt = self.prompt_builder.build_keyword_cluster_prompt(pillar_keyword, context)
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-flash')

        try:
            model = genai.GenerativeModel(primary)
            raw = ""
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.5, response_mime_type="application/json"),
            )
            raw = response.text.strip()

            cluster = json.loads(raw)
            if isinstance(cluster, list):
                return cluster, self._extract_usage(response), None
            return None, None, "Gemini không trả về định dạng Array JSON hợp lệ cho Topic Cluster."
        except json.JSONDecodeError as e:
            return None, None, f"Lỗi parse JSON từ AI: {e}\nRaw Response: {raw[:100]}..."
        except Exception as e:
            return None, None, f"Lỗi kết nối Gemini: {e}"

    # ─────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────

    def _extract_usage(self, response) -> dict:
        meta = getattr(response, 'usage_metadata', None)
        return {
            "in": getattr(meta, 'prompt_token_count', 0) if meta else 0,
            "out": getattr(meta, 'candidates_token_count', 0) if meta else 0,
        }

    def _call_with_fallback(
        self,
        prompt: str,
        generation_config,
    ) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
        """Try the primary model first, then each fallback in order."""
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-pro')
        models_to_try = [primary] + [m for m in FALLBACK_MODELS if m != primary]

        last_error = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                for attempt in range(MAX_RETRIES):
                    try:
                        response = model.generate_content(prompt, generation_config=generation_config)
                        if response.text:
                            cleaned = self.prompt_builder.clean_output(response.text)
                            return cleaned, self._extract_usage(response), None
                    except Exception as e:
                        last_error = str(e)
                        if "429" in last_error or "Quota" in last_error:
                            time.sleep(5)
                        elif "404" in last_error or "not found" in last_error.lower():
                            break  # model unavailable — skip immediately
                        else:
                            time.sleep(1)
                logger.warning(f"[CloudAIClient] Model {model_name} exhausted: {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"[CloudAIClient] Init failed for {model_name}: {e}")

        return None, None, last_error or "Tất cả các model fallback đều thất bại."
