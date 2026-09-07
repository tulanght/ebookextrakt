@echo off
chcp 65001 >nul
title E-Extract - ExtractPDF-EPUB
cd /d "%~dp0"

echo ============================================
echo   E-Extract  -  ExtractPDF-EPUB
echo ============================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [LOI] Khong tim thay venv tai: %CD%\venv
    echo       Tao venv bang lenh:  python -m venv venv
    echo       Roi cai goi:         venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Dang khoi dong ung dung...
echo.

"venv\Scripts\python.exe" run.py

set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" (
    echo ============================================
    echo   UNG DUNG THOAT VOI LOI  ^(ma loi: %RC%^)
    echo   Doc thong bao loi o tren de biet nguyen nhan.
    echo ============================================
    echo.
    pause
) else (
    echo Ung dung da dong binh thuong.
    timeout /t 3 >nul
)
