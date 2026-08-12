# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/cloud_client.py
# Version: 1.2.0
# Author: Antigravity
# Description: Wrapper around google.genai Unified SDK (AI Studio & Vertex AI).
# --------------------------------------------------------------------------------

import json
import time
import logging
from typing import Optional, List, Tuple

# Unified SDK (google-genai >= 1.0) — dùng cho cả AI Studio lẫn Vertex AI
try:
    from google import genai as new_genai
    from google.genai import types as new_types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False

# Fallback: old SDK cho AI Studio nếu new SDK chưa cài
import google.generativeai as old_genai

from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# Fallback chain — dùng tên ngắn, new SDK tự xử lý cho cả 2 nền tảng
FALLBACK_MODELS = [
    'gemini-3.1-pro-preview',
    'gemini-3.1-flash-lite',
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
    Manages the Gemini API connection (AI Studio or Vertex AI) and exposes operations.
    Uses the new google-genai Unified SDK (>= 1.0).
    """

    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.prompt_builder = PromptBuilder()
        self.api_key: str = ""
        self._configured = False
        self.provider = "ai_studio"
        self._client = None  # google.genai.Client instance
        self.setup()

    # ─────────────────────────────────────────────────────────────────
    # Setup
    # ─────────────────────────────────────────────────────────────────

    def setup(self, api_key: str = None) -> None:
        """Configure the SDK based on settings."""
        self._configured = False
        self._client = None
        self.provider = self.settings.get("cloud_provider", "ai_studio")

        if not NEW_SDK_AVAILABLE:
            logger.error("[CloudAIClient] google-genai package not installed. Run: pip install google-genai")
            return

        if self.provider == "ai_studio":
            self.api_key = api_key or self.settings.get_api_key()
            if self.api_key:
                try:
                    self._client = new_genai.Client(api_key=self.api_key)
                    self._configured = True
                    logger.info("[CloudAIClient] AI Studio (new SDK) configured.")
                except Exception as e:
                    logger.error(f"[CloudAIClient] AI Studio config error: {e}")

        elif self.provider == "vertex_ai":
            try:
                vertex_api_key = self.settings.get("vertex_api_key", "").strip()
                if vertex_api_key:
                    self._client = new_genai.Client(vertexai=True, api_key=vertex_api_key)
                    self._configured = True
                    logger.info("[CloudAIClient] Vertex AI (new SDK) configured using Agent Platform API Key.")
                else:
                    project = self.settings.get("vertex_project_id", "")
                    location = self.settings.get("vertex_region", "us-central1")
                    creds_path = self.settings.get("vertex_credentials_path", "")

                    if not project:
                        logger.error("[CloudAIClient] Vertex AI requires a Project ID when not using API Key.")
                        return

                    kwargs = {"vertexai": True, "project": project, "location": location}

                    if creds_path:
                        import os
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

                    self._client = new_genai.Client(**kwargs)
                    self._configured = True
                    logger.info(f"[CloudAIClient] Vertex AI (new SDK) configured. Project={project}, Region={location}")
            except Exception as e:
                logger.error(f"[CloudAIClient] Vertex AI config error: {e}")

    @property
    def is_ready(self) -> bool:
        return self._configured and self._client is not None

    def _generate(self, model_name: str, prompt: str, **gen_kwargs) -> str:
        """Low-level call to the unified client."""
        config = new_types.GenerateContentConfig(**gen_kwargs)
        response = self._client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    def _extract_usage(self, response) -> dict:
        meta = getattr(response, 'usage_metadata', None)
        return {
            "in": getattr(meta, 'prompt_token_count', 0) if meta else 0,
            "out": getattr(meta, 'candidates_token_count', 0) if meta else 0,
        }


    # ─────────────────────────────────────────────────────────────────
    # Translation
    # ─────────────────────────────────────────────────────────────────

    def translate_chunk(
        self, text: str, glossary_str: str = ""
    ) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
        if not self.is_ready:
            return None, None, "API Key hoặc Vertex AI chưa được cấu hình"

        prompt = self.prompt_builder.build_translation_prompt(text, glossary_str)
        return self._call_with_fallback(prompt, temperature=0.3, top_p=0.9)

    # ─────────────────────────────────────────────────────────────────
    # Style transformation
    # ─────────────────────────────────────────────────────────────────

    def transform(
        self, prompt: str, temperature: float = 0.5
    ) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
        if not self.is_ready:
            return None, None, "API Key hoặc Vertex AI chưa được cấu hình"

        return self._call_with_fallback(prompt, temperature=temperature, top_p=0.95)

    # ─────────────────────────────────────────────────────────────────
    # Glossary extraction
    # ─────────────────────────────────────────────────────────────────

    def extract_glossary_json(
        self, text: str, subject: str = "tổng hợp"
    ) -> Tuple[Optional[List[dict]], Optional[dict], Optional[str]]:
        if not self.is_ready:
            return None, None, "Vui lòng cấu hình Cloud API trong Cài đặt."

        prompt = self.prompt_builder.build_glossary_extraction_prompt(text, subject)
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-flash')

        try:
            raw = self._generate(primary, prompt, temperature=0.1)
            raw = raw.strip()

            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]

            terms = json.loads(raw.strip())
            if isinstance(terms, list):
                return terms, {}, None
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
        if not self.is_ready:
            return None, None, "Vui lòng cấu hình Cloud API trong Cài đặt."

        prompt = self.prompt_builder.build_content_brief_prompt(text)
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-flash')

        try:
            raw = self._generate(primary, prompt, temperature=0.3, response_mime_type="application/json")
            raw = raw.strip()

            brief = json.loads(raw)
            if isinstance(brief, dict):
                return brief, {}, None
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
        if not self.is_ready:
            return None, None, "Vui lòng cấu hình Cloud API trong Cài đặt."

        prompt = self.prompt_builder.build_keyword_cluster_prompt(pillar_keyword, context)
        primary = self.settings.get('cloud_model_name', 'gemini-2.5-flash')

        try:
            raw = self._generate(primary, prompt, temperature=0.5, response_mime_type="application/json")
            raw = raw.strip()

            cluster = json.loads(raw)
            if isinstance(cluster, list):
                return cluster, {}, None
            return None, None, "Gemini không trả về định dạng Array JSON hợp lệ cho Topic Cluster."
        except json.JSONDecodeError as e:
            return None, None, f"Lỗi parse JSON từ AI: {e}\nRaw Response: {raw[:100]}..."
        except Exception as e:
            return None, None, f"Lỗi kết nối Gemini: {e}"

    # ─────────────────────────────────────────────────────────────────
    # Internal helpers — Fallback loop
    # ─────────────────────────────────────────────────────────────────

    def _call_with_fallback(
        self,
        prompt: str,
        **gen_kwargs,
    ) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
        primary = self.settings.get('cloud_model_name', FALLBACK_MODELS[0])
        models_to_try = [primary] + [m for m in FALLBACK_MODELS if m != primary]

        last_error = None
        for model_name in models_to_try:
            for attempt in range(MAX_RETRIES):
                try:
                    text = self._generate(model_name, prompt, **gen_kwargs)
                    if text:
                        cleaned = self.prompt_builder.clean_output(text)
                        return cleaned, {}, None
                except Exception as e:
                    last_error = str(e)
                    err_lower = last_error.lower()
                    if "429" in last_error or "quota" in err_lower or "resource_exhausted" in err_lower:
                        time.sleep(5)
                    elif "404" in last_error or "not found" in err_lower:
                        break  # model không tồn tại, thử model tiếp theo
                    else:
                        time.sleep(1)
            logger.warning(f"[CloudAIClient] Model {model_name} exhausted: {last_error}")

        return None, None, last_error or "Tất cả các model fallback đều thất bại."
