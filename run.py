# run.py
# description: Entry point để khởi chạy ứng dụng.

import sys
from pathlib import Path

# Thêm thư mục src vào Python Path để có thể import các module
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from extract_app.main_app import main

if __name__ == "__main__":
    main()