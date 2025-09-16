# bootstrap.py
# description: Kịch bản tự động tạo cấu trúc thư mục và file ban đầu cho dự án ExtractPDF-EPUB.

import os
from pathlib import Path

# Cấu trúc dự án
project_structure = {
    "src/extract_app": {
        "core": [
            "__init__.py",
            "database.py",
            "pdf_parser.py",
            "epub_parser.py",
            "content_structurer.py",
        ],
        "modules": [
            "__init__.py",
            "main_window.py",
            "input_handler_ui.py",
            "storage_handler_ui.py",
        ],
        "shared": [
            "__init__.py",
            "constants.py",
            "utils.py",
        ],
        "__init__.py": None,
        "main_app.py": """# main_app.py
# version: 1.0
# last-updated: 2025-09-16
# description: File điều phối chính của ứng dụng, quản lý cửa sổ và các module.

def main():
    print("Application starting...")
    # Logic khởi tạo giao diện chính sẽ được thêm ở đây
    print("Application finished.")

if __name__ == "__main__":
    main()
""",
    },
    "scripts": [
        "__init__.py",
        # "release.py": "...", # Sẽ được thêm sau
    ],
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
venv/
.venv/
env/
.env

# Build artifacts
dist/
build/
*.egg-info/

# IDE specific
.vscode/
.idea/

# OS specific
.DS_Store
Thumbs.db
""",
    "run.py": """# run.py
# description: Entry point để khởi chạy ứng dụng.

import sys
from pathlib import Path

# Thêm thư mục src vào Python Path để có thể import các module
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from extract_app.main_app import main

if __name__ == "__main__":
    main()
""",
    "requirements.txt": """# Các thư viện cơ bản ban đầu
PyMuPDF
ebooklib
customtkinter
sv-ttk
""",
    "README.md": "# ExtractPDF-EPUB App\n\nMột ứng dụng desktop giúp trích xuất nội dung văn bản và hình ảnh từ các file PDF và EPUB.",
    "WORKFLOW.md": "# Kế thừa từ Gemini Creative Suite",
    "CHANGELOG.md": "# Lịch sử thay đổi\n\n## [0.1.0] - Unreleased",
    "ROADMAP.md": "# Lộ trình Phát triển",
    "TECHNICAL_NOTES.md": "# Ghi chú Kỹ thuật & Quyết định Kiến trúc",
}

def create_project_structure(base_path, structure):
    """Tạo cấu trúc thư mục và file dựa trên dictionary đầu vào."""
    for name, content in structure.items():
        path = Path(base_path) / name
        if isinstance(content, dict):
            # Nếu là thư mục, tạo thư mục và đệ quy
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            create_project_structure(path, content)
        elif isinstance(content, list):
            # Nếu là danh sách file trong thư mục
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            for filename in content:
                (path / filename).touch()
                print(f"  - Created file: {path / filename}")
        else:
            # Nếu là file có nội dung
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                if content:
                    f.write(content.strip())
            print(f"Created file: {path}")

if __name__ == "__main__":
    project_root = Path(__file__).parent
    print(f"Bắt đầu tạo cấu trúc dự án tại: {project_root}")
    create_project_structure(project_root, project_structure)
    print("\nHoàn tất! Cấu trúc dự án đã được tạo thành công.")
    print("Bạn có thể xóa file bootstrap.py này sau khi đã chạy xong.")