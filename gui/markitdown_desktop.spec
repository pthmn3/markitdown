# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MarkItDown Desktop.
Build with: pyinstaller markitdown_desktop.spec
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Paths
GUI_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_ROOT = os.path.dirname(GUI_DIR)
MARKITDOWN_SRC = os.path.join(PROJECT_ROOT, 'packages', 'markitdown', 'src')

a = Analysis(
    [os.path.join(GUI_DIR, 'markitdown_gui.py')],
    pathex=[GUI_DIR, MARKITDOWN_SRC],
    binaries=[],
    datas=[
        # Include markitdown package source
        (os.path.join(MARKITDOWN_SRC, 'markitdown'), 'markitdown'),
    ],
    hiddenimports=[
        # Core markitdown
        'markitdown',
        'markitdown.__main__',
        'markitdown._markitdown',
        'markitdown._base_converter',
        'markitdown._stream_info',
        'markitdown._uri_utils',
        'markitdown._exceptions',
        'markitdown.converters',
        # Converters
        'markitdown.converters._pdf_converter',
        'markitdown.converters._docx_converter',
        'markitdown.converters._pptx_converter',
        'markitdown.converters._xlsx_converter',
        'markitdown.converters._html_converter',
        'markitdown.converters._plain_text_converter',
        'markitdown.converters._csv_converter',
        'markitdown.converters._image_converter',
        'markitdown.converters._audio_converter',
        'markitdown.converters._epub_converter',
        'markitdown.converters._zip_converter',
        'markitdown.converters._outlook_msg_converter',
        'markitdown.converters._ipynb_converter',
        'markitdown.converters._rss_converter',
        'markitdown.converters._wikipedia_converter',
        'markitdown.converters._youtube_converter',
        'markitdown.converters._bing_serp_converter',
        # Dependencies
        'beautifulsoup4',
        'bs4',
        'requests',
        'markdownify',
        'magika',
        'charset_normalizer',
        'defusedxml',
        # Optional deps (PDF)
        'pdfminer',
        'pdfminer.six',
        'pdfplumber',
        # Optional deps (Office)
        'pptx',
        'mammoth',
        'pandas',
        'openpyxl',
        'xlrd',
        'lxml',
        # Optional deps (Other)
        'olefile',
        'pydub',
        'speech_recognition',
        'youtube_transcript_api',
        'ebooklib',
        # ttkbootstrap
        'ttkbootstrap',
        # tkinter
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MarkItDown Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(GUI_DIR, 'assets', 'icon.ico') if os.path.exists(os.path.join(GUI_DIR, 'assets', 'icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MarkItDown Desktop',
)
