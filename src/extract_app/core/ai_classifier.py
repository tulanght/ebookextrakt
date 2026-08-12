# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/ai_classifier.py
# Version: 1.2.0
# Author: Antigravity
# Description: Vertex AI integration for Ebook classification and metadata extraction (Single-Shot)
# --------------------------------------------------------------------------------

import json
from typing import Dict, Any, Optional
from .cloud_client import CloudAIClient
from src.extract_app.shared.debug_logger import log as global_log

class AIClassifier:
    """
    Handles AI-driven content classification and metadata extraction using Vertex AI.
    Relies on the existing CloudAIClient for authentication and API calls.
    """
    def __init__(self, cloud_client: CloudAIClient):
        self.cloud_client = cloud_client

    def analyze_book(self, text_sample: str) -> Dict[str, Any]:
        """
        Determines the true metadata and category of a book in a single AI call.
        Returns a dict: {category_id, reason, title, author, year}
        """
        if not self.cloud_client.is_ready:
            return {"category_id": "Khac", "reason": "Vertex AI chưa cấu hình", "title": "", "author": ""}
            
        prompt = f"""
        Bạn là một chuyên gia thư viện khoa học. Dưới đây là Mục lục (Table of Contents) hoặc phần đầu của một cuốn sách.
        Hãy thực hiện 2 nhiệm vụ:
        
        1. XÁC ĐỊNH METADATA THỰC SỰ:
        - Lấy Tên sách gốc và Tên Tác giả thực sự.
        - LOẠI BỎ TOÀN BỘ rác của uploader như "z-lib.org", "z-library", "1lib", "libgen", "pdf".
        
        2. PHÂN LOẠI:
        Bắt buộc phải chọn đúng 1 Mã kho (category_id) trong 4 kho sau:
        - Dong_Vat : Sách chỉ nói về động vật (Zoology, Wildlife, Thú y...)
        - Thuc_Vat : Sách chỉ nói về thực vật (Botany, Nông nghiệp, Trồng trọt, Hoa lá...)
        - Dong_Vat_Va_Thuc_Vat : Sách Sinh thái học tổng hợp, đa dạng sinh học chứa cả Động vật và Thực vật.
        - Khac : Nằm ngoài lĩnh vực Sinh học (Văn học, Lịch sử, Kinh tế, Tiểu thuyết...)
        
        Nội dung sách:
        ---
        {text_sample[:10000]}
        ---
        
        Trả về ĐÚNG định dạng JSON sau (không markdown, không code block):
        {{
            "category_id": "Dong_Vat" | "Thuc_Vat" | "Dong_Vat_Va_Thuc_Vat" | "Khac",
            "reason": "Lý do ngắn gọn",
            "title": "Tên sách cực sạch",
            "author": "Tên tác giả",
            "year": 2023
        }}
        """
        primary = self.cloud_client.settings.get('cloud_model_name', 'gemini-2.5-flash')
        try:
            raw = self.cloud_client._generate(primary, prompt, temperature=0.1, response_mime_type="application/json")
            data = json.loads(raw.strip())
            
            cat_id = data.get("category_id", "Khac")
            if cat_id not in ["Dong_Vat", "Thuc_Vat", "Dong_Vat_Va_Thuc_Vat", "Khac"]:
                data["category_id"] = "Khac"
                
            return data
        except Exception as e:
            global_log(f"[Vertex AI ERROR] {e}")
            return {"category_id": "Khac", "reason": f"Lỗi AI: {e}", "title": "", "author": ""}
