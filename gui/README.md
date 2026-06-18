# MarkItDown Desktop

A modern Windows desktop GUI for Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library. Convert PDF, Word, PowerPoint, Excel, images, audio, HTML, and many more formats to Markdown with a beautiful, easy-to-use interface.

![MarkItDown Desktop](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **Drag & Drop** — Drop files directly into the app
- **Batch Conversion** — Convert multiple files at once
- **Live Preview** — See Markdown output instantly
- **20+ Formats** — PDF, Word, PowerPoint, Excel, HTML, images, audio, EPub, CSV, JSON, XML, ZIP, and more
- **URL Support** — Convert web pages by entering a URL
- **Auto-Save** — Automatically save converted files to a folder
- **Copy to Clipboard** — One-click copy of Markdown output
- **Plugin Support** — Enable 3rd-party MarkItDown plugins
- **Dark Theme** — Beautiful modern dark UI
- **Keyboard Shortcuts** — Ctrl+O (Add Files), Ctrl+S (Save), Ctrl+Q (Quit)

## 📦 Installation

### Option 1: Windows Installer (Recommended)

1. Download `MarkItDown_Desktop_Setup_1.0.0.exe` from the [Releases](../../releases) page
2. Run the installer
3. The installer will:
   - Install the MarkItDown Desktop application
   - Optionally install Python 3.12 (if not already installed)
   - Install the `markitdown` package and all dependencies via pip

### Option 2: Run from Source

```bash
# 1. Install Python 3.10+ from https://python.org

# 2. Clone the repository
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# 3. Install markitdown with all optional dependencies
pip install -e "packages/markitdown[all]"

# 4. Install GUI dependencies
pip install ttkbootstrap

# 5. Run the GUI
python gui/markitdown_gui.py
```

## 🔨 Building the Installer

### Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.10+** with pip
- **Inno Setup 6+** (for building the installer): [Download](https://jrsoftware.org/issetup.php)

### Build Steps

```batch
cd gui

REM Build the .exe only
build.bat

REM Build the .exe AND the installer
build.bat installer
```

### Build Output

| File | Location |
|------|----------|
| Executable | `gui/dist/MarkItDown Desktop/MarkItDown Desktop.exe` |
| Installer | `gui/installer_output/MarkItDown_Desktop_Setup_1.0.0.exe` |

### Optional: Bundle Python with the Installer

To create an installer that can install Python offline:

1. Download `python-3.12.7-amd64.exe` from [python.org](https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe)
2. Place it in `gui/redist/`
3. Run `build.bat installer`

## 📂 Project Structure

```
gui/
├── markitdown_gui.py          # Main GUI application
├── markitdown_desktop.spec    # PyInstaller build specification
├── installer.iss              # Inno Setup installer script
├── build.bat                  # Windows build script
├── generate_icon.py           # App icon generator
├── requirements_install.txt   # Requirements for pip install during setup
├── assets/
│   └── icon.ico               # Application icon (generated)
├── dist/                      # PyInstaller output (after build)
├── redist/                    # Redistributables (Python installer)
└── installer_output/          # Inno Setup output (after build)
```

## 🖥️ Supported File Formats

| Category | Formats |
|----------|---------|
| Documents | PDF, DOCX, PPTX, EPUB |
| Spreadsheets | XLSX, XLS, CSV |
| Web | HTML, HTM, XML, JSON, RSS |
| Images | JPG, PNG, GIF, BMP, TIFF |
| Audio | WAV, MP3 |
| Other | ZIP, MSG, IPYNB, TXT, MD, RST |
| URLs | HTTP/HTTPS web pages, YouTube |

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Add Files |
| `Ctrl+S` | Save current output |
| `Ctrl+Q` | Quit |
| `Delete` | Remove selected file(s) |

## 📄 License

MIT License — see [LICENSE](../LICENSE) for details.

MarkItDown is a Microsoft open-source project.
