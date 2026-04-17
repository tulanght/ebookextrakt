# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/prompt_builder.py
# Version: 1.0.0
# Author: Antigravity
# Description: Builds all AI prompts and cleans AI output artifacts.
#              Pure string manipulation — no network or file I/O.
# --------------------------------------------------------------------------------

import re
from typing import Optional


class PromptBuilder:
    """
    Encapsulates all prompt templates for translation, transformation and
    glossary extraction.  Each `build_*` method returns a fully formed
    prompt string ready to pass to an AI client.
    """

    # ─────────────────────────────────────────────────────────────────
    # Translation Prompt
    # ─────────────────────────────────────────────────────────────────

    def build_translation_prompt(self, text: str, glossary_str: str = "") -> str:
        """Build the standard Archive-style translation prompt (EN → VI)."""
        glossary_prompt = (
            f"7. TỪ VỰNG BẮT BUỘC:\n{glossary_str}\n"
            if glossary_str else ""
        )
        return (
            "<SYSTEM>\n"
            "Bạn là một phần mềm dịch thuật tự động Anh-Việt.\n"
            "NHIỆM VỤ DUY NHẤT: Dịch văn bản bên dưới sang tiếng Việt.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. CHỈ trả về bản dịch tiếng Việt thuần túy. TUYỆT ĐỐI KHÔNG giải thích, "
            "KHÔNG ghi chú, KHÔNG bình luận, KHÔNG thêm tiêu đề 'Bản dịch'.\n"
            "2. KHÔNG viết câu mở đầu kiểu 'Dưới đây là bản dịch...' hay câu kết "
            "kiểu 'Lưu ý:...'.\n"
            "3. Giữ nguyên cấu trúc đoạn văn và xuống dòng của bản gốc.\n"
            "4. Giữ nguyên Markdown formatting (##, **, -, v.v.) nếu có.\n"
            "5. Giữ nguyên mọi placeholder __IMG_XXX__ — KHÔNG dịch, KHÔNG xóa chúng.\n"
            "6. Dịch sát nghĩa, tự nhiên, phù hợp ngữ cảnh sách non-fiction.\n"
            f"{glossary_prompt}"
            "</SYSTEM>\n\n"
            f"{text}"
        )

    # ─────────────────────────────────────────────────────────────────
    # Transform Prompts (Website / Facebook variants)
    # ─────────────────────────────────────────────────────────────────

    def build_transform_prompt(
        self,
        archive_text: str,
        original_text: str,
        variant_type: str,
        article_template: str = "",
        gem_instructions: str = "",
    ) -> Optional[str]:
        """Build a variant transform prompt.  Returns None for unknown variant_type."""
        if variant_type == 'website':
            template_instruction = f"\nCấu trúc bài viết PHẢI theo đúng outline sau:\n{article_template}\n" if article_template else ""
            return (
                "<SYSTEM>\n"
                "Bạn là biên tập viên website chuyên nghiệp.\n"
                "NHIỆM VỤ: Biên tập lại bản dịch tiếng Việt bên dưới thành bài viết website.\n\n"
                "QUY TẮC:\n"
                "1. CHỈ trả về bài viết đã biên tập. KHÔNG giải thích, KHÔNG ghi chú.\n"
                "2. Thêm tiêu đề H2 (##) cho các phần chính, H3 (###) cho phần phụ.\n"
                "3. Chia đoạn văn ngắn (2-4 câu), sử dụng bullet points khi liệt kê.\n"
                "4. Văn phong mạch lạc, chuyên nghiệp nhưng không khô khan.\n"
                "5. Giữ nguyên mọi placeholder __IMG_XXX__ và [Image Anchor:].\n"
                f"{template_instruction}"
                "</SYSTEM>\n\n"
                f"{archive_text}"
            )
        elif variant_type == 'facebook':
            instructions = gem_instructions or (
                "Bạn là Gem — chuyên gia động vật học đầy đam mê, hài hước.\n"
                "Chuyển thể nội dung thành bài Facebook gần gũi, lôi cuốn, khơi gợi tò mò."
            )
            return (
                "<SYSTEM>\n"
                f"{instructions}\n\n"
                "NHIỆM VỤ: Chuyển thể bản dịch bên dưới thành bài viết Facebook theo phong cách Gem.\n"
                "CHỈ trả về nội dung bài viết. KHÔNG giải thích thêm.\n"
                "</SYSTEM>\n\n"
                "--- BẢN DỊCH GỐC ---\n"
                f"{archive_text}\n\n"
                "--- VĂN BẢN TIẾNG ANH (THAM KHẢO) ---\n"
                f"{original_text[:3000]}"
            )
        return None

    # ─────────────────────────────────────────────────────────────────
    # Glossary Extraction Prompt
    # ─────────────────────────────────────────────────────────────────

    def build_glossary_extraction_prompt(self, text: str, subject: str = "tổng hợp") -> str:
        """Build prompt to extract domain-specific terms for glossary."""
        return (
            f"Bạn là một chuyên gia ngôn ngữ học và dịch giả chuyên ngành [{subject}].\n"
            "Nhiệm vụ của bạn là đọc đoạn văn bản tiếng Anh dưới đây và trích xuất ra danh sách "
            "các thuật ngữ MÀ MỘT MODEL DỊCH TỰ ĐỘNG NHỎ (12B) CÓ THỂ DỊCH SAI, "
            "sau đó đưa ra bản dịch tiếng Việt chuẩn xác nhất cho ngữ cảnh đó.\n\n"
            "YÊU CẦU BẮT BUỘC:\n"
            "1. Chỉ trích xuất tối đa 30-50 từ vựng quan trọng nhất.\n"
            "2. ƯU TIÊN các loại từ sau:\n"
            "   a) Thuật ngữ chuyên ngành/khoa học (ví dụ: 'entelodonts', 'lachrymal bone')\n"
            "   b) Từ ĐA NGHĨA dễ dịch sai theo ngữ cảnh (ví dụ: 'sow' = 'lợn nái' chứ KHÔNG phải 'gieo hạt')\n"
            "   c) Danh từ riêng cần phiên âm/giữ nguyên (tên giống loài, địa danh, nhân vật)\n"
            "   d) Cụm từ ghép phức tạp (ví dụ: 'free-range pork', 'even-toed ungulates')\n"
            "3. TUYỆT ĐỐI KHÔNG trích xuất từ phổ thông cơ bản như: "
            "water, food, history, animal, large, small, climate, important, natural, human.\n"
            "4. Trả về KẾT QUẢ DUY NHẤT LÀ MỘT MẢNG JSON HỢP LỆ, không có Markdown backticks, không giải thích thêm.\n"
            "5. Format JSON yêu cầu:\n"
            '[{"en": "sow", "vi": "lợn nái"}, {"en": "Suidae family", "vi": "Họ Lợn (Suidae)"}]\n\n'
            "VĂN BẢN GỐC:\n"
            f"{text[:15000]}"
        )

    # ─────────────────────────────────────────────────────────────────
    # Composition Prompt
    # ─────────────────────────────────────────────────────────────────

    def build_composition_prompt(self, sources: list[str], research_notes: str, focus_keyword: str, article_template: str = "") -> str:
        """Build prompt for composing a multi-source article."""
        n = len(sources)
        sources_text = "\n\n".join([f"--- NGUỒN {i+1} ---\n{src}" for i, src in enumerate(sources)])
        notes_text = f"--- RESEARCH NOTES ---\n{research_notes}\n" if research_notes else ""
        template_instruction = f"Cấu trúc bài viết PHẢI theo đúng template sau:\n{article_template}\n" if article_template else ""
        
        return (
            "<SYSTEM>\n"
            "Bạn là một biên tập viên website và chuyên gia SEO.\n"
            f"NHIỆM VỤ: Dựa trên {n} nguồn tài liệu và research notes được cung cấp, hãy tổng hợp và viết một bài hoàn chỉnh.\n\n"
            "QUY TẮC:\n"
            f"1. Target keyword (từ khóa chính) là '{focus_keyword}'. Hãy phân bổ keyword tự nhiên trong bài.\n"
            f"2. {template_instruction}"
            "3. Văn phong mạch lạc, chuyên nghiệp, thông tin chính xác tổng hợp từ các nguồn.\n"
            "4. KHÔNG sao chép y nguyên, hãy viết lại bằng văn phong của riêng bạn.\n"
            "5. CHỈ trả về nội dung bài viết, KHÔNG giải thích gì thêm.\n"
            "</SYSTEM>\n\n"
            f"{notes_text}\n"
            f"{sources_text}"
        )

    # ─────────────────────────────────────────────────────────────────
    # Content Brief Generation Prompt
    # ─────────────────────────────────────────────────────────────────

    def build_content_brief_prompt(self, text: str) -> str:
        """Build prompt to generate an SEO Content Brief in JSON format."""
        return (
            "Bạn là một chuyên gia SEO (Search Engine Optimization) và Content Manager chuyên nghiệp.\n"
            "Dựa vào nội dung bài viết dưới đây, hãy phân tích và tạo ra một Content Brief (Bản tóm tắt nội dung) "
            "chi tiết, nhằm giúp người viết tối ưu định hướng bài viết trên công cụ tìm kiếm chuẩn Google.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Phân tích văn bản với tư duy làm SEO mảng nội dung.\n"
            "2. Trả về KẾT QUẢ DUY NHẤT LÀ MỘT ĐỐI TƯỢNG JSON HỢP LỆ, TUYỆT ĐỐI KHÔNG có Markdown backticks (như ```json), "
            "KHÔNG có bất kỳ văn bản giải thích nào khác ngoại trừ JSON string. Parse JSON phải hoàn hảo.\n"
            "3. Format JSON bắt buộc (điền dữ liệu vào các value dựa trên nội dung bạn phân tích được):\n"
            "{\n"
            '  "search_intent": "Câu ngắn mô tả mục đích người dùng khi tìm kiếm (Vd: Tìm kiếm thông tin, So sánh, Mua hàng...)",\n'
            '  "content_type": "Loại nội dung (Vd: Bài viết cẩm nang, Hướng dẫn, Quan điểm...)",\n'
            '  "target_audience": "Mô tả ngắn gọn về chân dung độc giả mục tiêu",\n'
            '  "lsi_keywords": ["từ khoá LSI 1", "từ khoá 2", "từ khoá 3", "từ khoá 4", "từ khoá 5"],\n'
            '  "faqs": [\n'
            '    {"question": "Câu hỏi phổ biến 1 người dùng hay thắc mắc?", "answer": "Câu trả lời ngắn gọn (1-2 câu)."},\n'
            '    {"question": "Câu hỏi phổ biến 2?", "answer": "Trả lời..."}\n'
            '  ],\n'
            '  "outline": [\n'
            '    "H2: [Tiêu đề phụ chính 1]",\n'
            '    "H3: [Tiêu đề con 1.1]",\n'
            '    "H2: [Tiêu đề phụ chính 2]"\n'
            '  ]\n'
            "}\n\n"
            "NỘI DUNG GỐC ĐỂ PHÂN TÍCH:\n"
            f"{text[:15000]}"
        )

    # ─────────────────────────────────────────────────────────────────
    # Keyword Cluster Generation Prompt
    # ─────────────────────────────────────────────────────────────────

    def build_keyword_cluster_prompt(self, pillar_keyword: str, context: str = "") -> str:
        """Build prompt to generate an SEO Topic Cluster (8-10 keywords) in JSON format."""
        context_prompt = f"Ngữ cảnh / Thông tin bổ sung (Niche/Website/Ngôn ngữ): {context}\nHãy tạo các từ khóa phù hợp với ngữ cảnh trên.\n" if context else ""
        return (
            "Bạn là một chuyên gia SEO Master và Content Strategist chuyên nghiệp.\n"
            f"Nhiệm vụ: Xây dựng một Topic Cluster (Chùm bài viết vệ tinh) tối ưu SEO xoay quanh Pillar Keyword (Từ khóa chính) sau: '{pillar_keyword}'.\n"
            f"{context_prompt}\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Bao phủ đầy đủ các Search Intent (Thông tin, Thương mại, Hướng dẫn...) liên quan đến Pillar Keyword.\n"
            "2. Trả về KẾT QUẢ DUY NHẤT LÀ MỘT MẢNG JSON HỢP LỆ, chứa đúng 8-10 bài vệ tinh. TUYỆT ĐỐI KHÔNG có Markdown backticks (như ```json), "
            "KHÔNG có văn bản giải thích nào khác. Parse JSON phải hoàn hảo.\n"
            "3. Format JSON bắt buộc (mảng các Object):\n"
            "[\n"
            '  {\n'
            '    "keyword": "Từ khóa vệ tinh 1",\n'
            '    "content_type": "Loại nội dung (Vd: Bài viết cẩm nang, Hướng dẫn, Đánh giá, FAQs...)",\n'
            '    "word_count_target": 1200\n'
            '  },\n'
            '  {\n'
            '    "keyword": "Từ khóa vệ tinh 2",\n'
            '    "content_type": "...",\n'
            '    "word_count_target": 1500\n'
            '  }\n'
            "]\n\n"
            "Hãy phân tích và trả về ngay kết quả JSON."
        )

    # ─────────────────────────────────────────────────────────────────
    # Output Cleaning
    # ─────────────────────────────────────────────────────────────────

    def clean_output(self, text: str) -> str:
        """Strip AI artifacts: code fences, preambles, trailing notes."""
        result = text.strip()

        # 1. Remove code fences
        result = re.sub(r'^```[a-zA-Z]*\n?', '', result)
        result = re.sub(r'\n?```$', '', result)

        # 2. Remove common preambles (Vietnamese and English)
        preamble_patterns = [
            r'^(?:Dưới đây là|Bản dịch|Here is|Translation|\*\*Bản dịch\*\*)[^\n]*\n+',
            r'^(?:##?\s*Bản dịch[^\n]*)\n+',
        ]
        for pattern in preamble_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # 3. Remove trailing notes
        trailing_patterns = [
            r'\n+(?:Lưu ý|Note|Ghi chú|\*\*Lưu ý\*\*)[:\s].*$',
            r'\n+---\n+.*$',
        ]
        for pattern in trailing_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

        # 4. Normalize whitespace
        lines = [line.rstrip() for line in result.split('\n')]
        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()
