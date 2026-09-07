import os
import sys
import platform
from pathlib import Path


def _get_exe_dir() -> Path:
    """Returns the directory containing the EXE (when frozen by PyInstaller)
    or the project root (when running as normal Python script).
    """
    if getattr(sys, 'frozen', False):
        # Running inside PyInstaller EXE — sys.executable is E-Extract.exe
        return Path(sys.executable).parent
    # Normal Python execution
    return Path(__file__).resolve().parent.parent.parent.parent


def get_user_data_dir() -> Path:
    """
    Returns the platform-specific application data directory path.

    Priority order:
    1. user_data/ cạnh EXE (hoặc cạnh run.py trong dev) — portable, ưu tiên cao nhất
    2. user_data/ relative to src/ (dev fallback)
    3. %APPDATA%\\ExtractPDF-EPUB\\ (Windows system-level)
    4. Platform-specific home dir

    Args:
        None

    Returns:
        Path: Resolved path to user data directory (created on first use by callers).
    """
    app_name = "ExtractPDF-EPUB"

    # 1. user_data/ cạnh EXE / project root (portable — highest priority)
    exe_adjacent = _get_exe_dir() / "user_data"
    if exe_adjacent.exists() and exe_adjacent.is_dir():
        return exe_adjacent

    # 2. user_data/ relative to CWD (legacy dev support)
    local_dir = Path.cwd() / "user_data"
    if local_dir.exists() and local_dir.is_dir():
        return local_dir

    # 3. user_data/ relative to src/ package (dev fallback)
    local_dir_src = Path(__file__).resolve().parent.parent.parent.parent / "user_data"
    if local_dir_src.exists() and local_dir_src.is_dir():
        return local_dir_src

    # 4. Frozen EXE first-run: create user_data/ next to EXE
    if getattr(sys, 'frozen', False):
        portable_dir = _get_exe_dir() / "user_data"
        portable_dir.mkdir(parents=True, exist_ok=True)
        return portable_dir

    # 5. System-level AppData (dev machines without user_data/)
    if platform.system() == "Windows":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / app_name
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    else:  # Linux
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / app_name
        return Path.home() / ".local" / "share" / app_name

    # 6. Ultimate fallback
    return Path.home() / f".{app_name.lower()}"
