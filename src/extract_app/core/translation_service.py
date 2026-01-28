# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/translation_service.py
# Version: 1.0.0
# Author: Antigravity
# Description: Wrapper for Google Gemini API for translation tasks.
# --------------------------------------------------------------------------------

import google.generativeai as genai
from typing import Optional

class TranslationService:
    """
    Service to handle text translation using Google Gemini API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash') # Use Flash for speed/cost

    def set_api_key(self, api_key: str):
        """Update API Key at runtime."""
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def translate_text(self, text: str) -> Optional[str]:
        """
        Translates the given text to Vietnamese using Gemini.
        Returns None if failed.
        """
        if not self.api_key or not hasattr(self, 'model'):
            return None

        prompt = f"""
        Bạn là một biên dịch viên chuyên nghiệp. Nhiệm vụ của bạn là dịch văn bản sau sang tiếng Việt.
        
        Yêu cầu:
        1. Dịch sát nghĩa nhưng văn phong tự nhiên, dễ đọc.
        2. Giữ nguyên các định dạng Markdown (như **bold**, [link], v.v.).
        3. Giữ nguyên các thuật ngữ chuyên ngành công nghệ nếu phổ biến (hoặc chua nghĩa tiếng Việt bên cạnh).
        4. KHÔNG thêm bất kỳ lời dẫn nào (như "Đây là bản dịch..."), chỉ trả về nội dung dịch.
        
        Văn bản cần dịch:
        ---
        {text}
        ---
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Translation Error: {e}")
            return None
