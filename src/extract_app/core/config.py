import os
import platform
from pathlib import Path

def get_user_data_dir() -> Path:
    """
    Returns the platform-specific application data directory path,
    prioritizing a local 'user_data' folder for portability.
    """
    app_name = "ExtractPDF-EPUB"
    
    # 1. Priority to local user_data in CWD
    local_dir = Path.cwd() / "user_data"
    if local_dir.exists() and local_dir.is_dir():
        return local_dir
        
    # 2. Fallback to local user_data relative to src/
    local_dir_src = Path(__file__).resolve().parent.parent.parent.parent / "user_data"
    if local_dir_src.exists() and local_dir_src.is_dir():
        return local_dir_src

    # 3. System-level AppData
    if platform.system() == "Windows":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / app_name
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    else:  # Linux and others
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / app_name
        return Path.home() / ".local" / "share" / app_name
        
    # 4. Ultimate fallback
    return Path.home() / f".{app_name.lower()}"
