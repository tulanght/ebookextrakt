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
        gem_instructions: str = "",
    ) -> Optional[str]:
        """Build a variant transform prompt.  Returns None for unknown variant_type."""
        if variant_type == 'website':
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
