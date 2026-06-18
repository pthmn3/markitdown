@echo off
REM ╔═══════════════════════════════════════════════════════════════════╗
REM ║  MarkItDown Desktop — Windows Build Script                        ║
REM ║                                                                   ║
REM ║  This script builds the .exe and creates the installer.           ║
REM ║                                                                   ║
REM ║  Prerequisites:                                                   ║
REM ║    1. Python 3.10+ with pip                                       ║
REM ║    2. Inno Setup 6+ (for installer; optional)                     ║
REM ║                                                                   ║
REM ║  Usage:                                                           ║
REM ║    build.bat              Build .exe only                         ║
REM ║    build.bat installer    Build .exe + installer                  ║
REM ╚═══════════════════════════════════════════════════════════════════╝

setlocal enabledelayedexpansion

echo.
echo  ============================================
echo    MarkItDown Desktop -- Build System
echo  ============================================
echo.

REM ── Step 1: Check Python ──
echo [1/6] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    exit /b 1
)
echo       OK
echo.

REM ── Step 2: Install build dependencies ──
echo [2/6] Installing build dependencies (pyinstaller, ttkbootstrap)...
python -m pip install pyinstaller ttkbootstrap
if errorlevel 1 (
    echo WARNING: Some build dependencies may have failed to install.
)
echo       OK
echo.

REM ── Step 3: Install markitdown with all optional deps ──
echo [3/6] Installing markitdown[all]...
echo       This downloads many packages (PDF, Office, audio, etc.)
echo       It may take 2-5 minutes. Please wait...
echo.
cd /d "%~dp0.."
python -m pip install -e "packages/markitdown[all]"
if errorlevel 1 (
    echo.
    echo WARNING: Some markitdown dependencies may have failed.
    echo          The build will continue, but some converters may not work.
    echo          You can also try: pip install markitdown[all]
    echo.
)
cd /d "%~dp0"
echo       OK
echo.

REM ── Step 4: Create assets directory ──
echo [4/6] Preparing assets...
if not exist "assets" mkdir assets
if not exist "assets\icon.ico" (
    echo       Generating app icon...
    python generate_icon.py
)
echo       OK
echo.

REM ── Step 5: Build with PyInstaller ──
echo [5/6] Building executable with PyInstaller...
echo       This may take several minutes...
echo.
python -m PyInstaller markitdown_desktop.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo Check the output above for details.
    exit /b 1
)
echo.
echo       Build complete: dist\MarkItDown Desktop\
echo.

REM ── Step 6: Build installer (optional) ──
if /i "%1"=="installer" (
    echo [6/6] Building installer with Inno Setup...

    REM Try to find Inno Setup
    set ISCC=
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    )
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
        set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    if "!ISCC!"=="" (
        echo.
        echo WARNING: Inno Setup not found!
        echo Install Inno Setup 6 from: https://jrsoftware.org/issetup.php
        echo Then re-run: build.bat installer
        echo.
        echo The .exe build is complete. You can find it in:
        echo   dist\MarkItDown Desktop\MarkItDown Desktop.exe
    ) else (
        REM Check for Python redistributable
        if not exist "redist" mkdir redist
        if not exist "redist\python-3.12.7-amd64.exe" (
            echo.
            echo NOTE: Python installer not found in redist\ folder.
            echo       The installer will be built without bundled Python.
            echo       To include Python, download python-3.12.7-amd64.exe from:
            echo       https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
            echo       and place it in the gui\redist\ folder.
            echo.
        )

        if not exist "installer_output" mkdir installer_output

        "!ISCC!" installer.iss
        if errorlevel 1 (
            echo ERROR: Installer build failed!
            exit /b 1
        )
        echo.
        echo       Installer created: installer_output\MarkItDown_Desktop_Setup_1.0.0.exe
    )
) else (
    echo [6/6] Skipping installer build. Run 'build.bat installer' to create installer.
)

echo.
echo  ============================================
echo    Build Complete!
echo  ============================================
echo.
echo  Executable: dist\MarkItDown Desktop\MarkItDown Desktop.exe
echo.

endlocal
