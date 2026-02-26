# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/style_manager.py
# Version: 1.0.0
# Author: Antigravity
# Description: Manages translation styles and glossaries for Local/Hybrid translation.
# --------------------------------------------------------------------------------

import json
from pathlib import Path
from typing import Dict, List, Optional

class StyleManager:
    """
    Manages translation styles (personas) and glossaries.
    """
    
    DEFAULT_STYLES = {
        "standard": "Bạn là biên dịch viên chuyên nghiệp. Dịch sát nghĩa, văn phong tự nhiên.",
        "literary": "Bạn là dịch giả văn học. Dịch văn phong bay bổng, giàu hình ảnh, từ ngữ trau chuốt, phù hợp với tiểu thuyết.",
        "technical": "Bạn là kỹ sư dịch thuật. Ưu tiên độ chính xác thuật ngữ, văn phong gãy gọn, khách quan.",
        "casual": "Bạn là người kể chuyện đời thường. Dịch văn phong gần gũi, dễ hiểu, dùng từ ngữ hiện đại.",
        "buddhism": "Bạn là dịch giả Phật học. Sử dụng từ Hán-Việt trang trọng, âm hưởng thiền môn.",
        "facebook_gem": """
VAI TRÒ:
Bạn là Gem - một chuyên gia động vật học đầy đam mê, hài hước và thích "cà khịa" nhẹ nhàng.
Sứ mệnh: Kể chuyện về sự kỳ thú của tự nhiên, phá bỏ hiểu lầm, khơi gợi tò mò.

PHONG CÁCH (Tone & Voice):
- Xưng hô: "mình" - "bạn" (hoặc "ad" - "các bạn").
- Giọng văn: Kể chuyện (storytelling), lôi cuốn, gần gũi như nói chuyện với bạn bè.
- Cảm xúc: Mở đầu gây tò mò/sốc -> Thân bài giải thích dí dỏm -> Kết bài gợi mở (Cliffhanger).
- BẮT BUỘC:
  + Dùng từ ngữ gợi hình (nhấm nháp, rỉa, phô trương, lẩn mình...).
  + Tránh từ sáo rỗng (Tuy nhiên, Hơn nữa, Đóng vai trò quan trọng...).
  + Không dùng câu bị động dài dòng.

CẤU TRÚC BÀI VIẾT:
1. TIÊU ĐỀ: Viết hoa toàn bộ, giật gân hoặc gây tò mò (Ví dụ: TÒ VÒ MÀ NUÔI CON NHỆN).
2. NỘI DUNG CHÍNH: Dịch và phóng tác nội dung gốc theo phong cách Gem.
3. PHẦN BÌNH LUẬN (CLIFFHANGER): Để lại một thông tin thú vị hoặc câu hỏi ở cuối để người đọc phải bấm vào xem thêm/bình luận.

LƯU Ý: Chỉ dịch ý, không dịch từng chữ. Nếu gặp khái niệm lạ, hãy tìm hình ảnh tương đồng ở Việt Nam để so sánh.
""",
        "website_seo": """
VAI TRÒ:
Bạn là biên tập viên Website chuyên về thiên nhiên, sinh học.
Sứ mệnh: Cung cấp kiến thức chính xác, sâu sắc nhưng vẫn giữ được sự lôi cuốn, đam mê của Gem.

PHONG CÁCH:
- Xưng hô: Trung lập hoặc "chúng tôi".
- Giọng văn: Chuyên nghiệp hơn Facebook nhưng không khô khan. Vẫn dùng từ ngữ gợi hình, tránh sáo rỗng.
- Tập trung: Cung cấp thông tin giá trị, giải quyết thắc mắc của người đọc.

CẤU TRÚC BÀI VIẾT (SEO):
1. Tiêu đề (H1): Chứa từ khóa chính, hấp dẫn.
2. Sapo (Mở đầu): Tóm tắt nội dung, khơi gợi nhu cầu đọc tiếp.
3. Các thẻ H2, H3 rõ ràng cho từng phần.
4. Nội dung: Chia nhỏ đoạn văn, sử dụng Bullet points.
5. Kết luận: Tóm lại ý chính.

LƯU Ý:
- Tối ưu hóa từ khóa (nếu có trong văn bản gốc).
- Giải thích thuật ngữ chuyên ngành rõ ràng.
- Văn phong mạch lạc, dễ đọc trên thiết bị di động.
"""
    }
    
    DEFAULT_GLOSSARY = {
        "AI": "Trí tuệ nhân tạo",
        "Machine Learning": "Học máy",
        "Deep Learning": "Học sâu",
        "Amberat": "Amberat (một dạng 'hổ phách' từ nước tiểu chuột gỗ)",
        # Gen_Dich Style Terms
        "eat": "nhấm nháp/thưởng thức",
        "hide": "ẩn mình/lẩn trốn",
        "show off": "phô trương",
        "colorful": "sặc sỡ/lộng lẫy"
    }

    def __init__(self, user_data_dir: str = "user_data"):
        self.data_dir = Path(user_data_dir)
        self.styles_path = self.data_dir / "styles.json"
        self.glossary_path = self.data_dir / "glossary.json"
        
        self.styles = self.DEFAULT_STYLES.copy()
        self.glossary = self.DEFAULT_GLOSSARY.copy()
        
        self._load_data()

    def _load_data(self):
        """Load styles and glossary from disk."""
        if self.styles_path.exists():
            try:
                with open(self.styles_path, 'r', encoding='utf-8') as f:
                    self.styles.update(json.load(f))
            except Exception as e:
                print(f"[StyleManager] Error loading styles: {e}")
        
        if self.glossary_path.exists():
            try:
                with open(self.glossary_path, 'r', encoding='utf-8') as f:
                    self.glossary.update(json.load(f))
            except Exception as e:
                print(f"[StyleManager] Error loading glossary: {e}")

    def save_data(self):
        """Save current styles and glossary to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.styles_path, 'w', encoding='utf-8') as f:
                json.dump(self.styles, f, indent=4, ensure_ascii=False)
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                json.dump(self.glossary, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[StyleManager] Error saving data: {e}")

    def get_style_instruction(self, style_name: str) -> str:
        return self.styles.get(style_name, self.styles["standard"])

    def get_glossary_text(self, input_text: str = "") -> str:
        """
        Returns a formatted string of glossary terms relevant to the input text.
        If input_text is empty, returns all terms (use carefully).
        """
        relevant_terms = []
        if input_text:
            # Simple content matching (can be optimized)
            input_lower = input_text.lower()
            for key, value in self.glossary.items():
                if key.lower() in input_lower:
                    relevant_terms.append(f"- {key}: {value}")
        else:
            # Return all
            for key, value in self.glossary.items():
                relevant_terms.append(f"- {key}: {value}")
                
        return "\n".join(relevant_terms)

    add_term = lambda self, k, v: self.glossary.update({k: v}) or self.save_data()
    add_style = lambda self, k, v: self.styles.update({k: v}) or self.save_data()
