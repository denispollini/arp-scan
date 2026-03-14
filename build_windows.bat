@echo off
echo ============================================
echo  ARP Scanner - Build for Windows
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1 || (
    echo [ERROR] Python not found. Download it from https://python.org
    pause & exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install scapy customtkinter pyinstaller --quiet
echo       OK

:: Build with PyInstaller
echo [2/3] Building with PyInstaller...
python -m pyinstaller ^
    --onefile ^
    --windowed ^
    --name "arp-scan" ^
    --icon NONE ^
    --hidden-import customtkinter ^
    --hidden-import scapy.layers.l2 ^
    --hidden-import scapy.layers.inet ^
    arp-scan_gui.py

echo [3/3] Cleaning up temporary files...
rmdir /s /q build >nul 2>&1
del /q arp-scan.spec >nul 2>&1

echo.
echo ============================================
echo  Build complete!
echo  Executable: dist\arp-scan.exe
echo.
echo  NOTE: Run as Administrator
echo  NOTE: Requires Npcap installed
echo        https://npcap.com
echo ============================================
pause
