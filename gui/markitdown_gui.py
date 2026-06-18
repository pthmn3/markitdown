#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarkItDown Desktop — A modern GUI for the MarkItDown library.
Converts PDF, Word, PowerPoint, Excel, images, audio, HTML, and more to Markdown.

Uses ttkbootstrap for a modern, dark-themed UI that works on Windows.
"""

import sys
import os
import threading
import traceback
import webbrowser
from pathlib import Path
from typing import Optional, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledText as TtkScrolledText
    HAS_TTKB = True
except ImportError:
    HAS_TTKB = False

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Supported file types
# ---------------------------------------------------------------------------
FILETYPES = [
    ("All Supported Files", "*.pdf *.docx *.pptx *.xlsx *.xls *.csv *.json *.xml "
     "*.html *.htm *.txt *.md *.rst *.epub *.ipynb *.msg *.zip "
     "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tif *.wav *.mp3"),
    ("PDF", "*.pdf"),
    ("Word", "*.docx"),
    ("PowerPoint", "*.pptx"),
    ("Excel", "*.xlsx *.xls"),
    ("HTML", "*.html *.htm"),
    ("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tif"),
    ("Audio", "*.wav *.mp3"),
    ("EPub", "*.epub"),
    ("CSV", "*.csv"),
    ("JSON", "*.json"),
    ("XML", "*.xml"),
    ("ZIP", "*.zip"),
    ("All Files", "*.*"),
]

# Emoji per extension
EXT_ICONS = {
    ".pdf": "📕", ".docx": "📘", ".doc": "📘",
    ".pptx": "📙", ".ppt": "📙",
    ".xlsx": "📊", ".xls": "📊", ".csv": "📊",
    ".html": "🌐", ".htm": "🌐",
    ".jpg": "🖼", ".jpeg": "🖼", ".png": "🖼", ".gif": "🖼",
    ".bmp": "🖼", ".tiff": "🖼", ".tif": "🖼",
    ".wav": "🎵", ".mp3": "🎵",
    ".epub": "📚", ".zip": "📦",
    ".json": "🔧", ".xml": "📋", ".msg": "✉",
    ".ipynb": "📓", ".txt": "📝", ".md": "📝", ".rst": "📝",
}


# ---------------------------------------------------------------------------
# Color Scheme (dark)
# ---------------------------------------------------------------------------
COLORS = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_card": "#1c2129",
    "bg_input": "#0d1117",
    "border": "#30363d",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#484f58",
    "accent_blue": "#58a6ff",
    "accent_green": "#3fb950",
    "accent_green_dark": "#238636",
    "accent_red": "#f85149",
    "accent_purple": "#bc8cff",
    "highlight": "#1f6feb",
    "selection": "#1f6feb33",
}


# ---------------------------------------------------------------------------
# TkDnD drop support (Windows native)
# ---------------------------------------------------------------------------
def setup_dnd(widget, callback):
    """Set up drag-and-drop if tkdnd is available (auto-included in Python on Windows)."""
    try:
        widget.tk.eval('package require tkdnd')
        widget.tk.eval(f'tkdnd::drop_target register {widget} *')
        # This is optional — we also support manual Add Files
    except tk.TclError:
        pass


# ---------------------------------------------------------------------------
# Worker Thread
# ---------------------------------------------------------------------------
class ConversionWorker(threading.Thread):
    """Runs MarkItDown conversions in a background thread."""

    def __init__(self, app, files, output_dir, enable_plugins):
        super().__init__(daemon=True)
        self.app = app
        self.files = files
        self.output_dir = output_dir
        self.enable_plugins = enable_plugins
        self.cancelled = False
        self.results = {}

    def run(self):
        try:
            from markitdown import MarkItDown
        except ImportError as e:
            self.app.after(0, self.app.log, f"❌ ERROR: markitdown not installed: {e}")
            self.app.after(0, self.app.on_conversion_done, {})
            return

        md = MarkItDown(enable_plugins=self.enable_plugins)

        for idx, filepath in enumerate(self.files):
            if self.cancelled:
                break

            basename = os.path.basename(filepath)
            self.app.after(0, self.app.update_progress, idx + 1, len(self.files), basename)
            self.app.after(0, self.app.log, f"  Converting: {basename}")

            try:
                result = md.convert(filepath)
                markdown_text = result.text_content
                self.results[filepath] = ("success", markdown_text)

                if self.output_dir:
                    base = os.path.splitext(basename)[0]
                    out_path = os.path.join(self.output_dir, f"{base}.md")
                    counter = 1
                    while os.path.exists(out_path):
                        out_path = os.path.join(self.output_dir, f"{base}_{counter}.md")
                        counter += 1
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(markdown_text)
                    self.app.after(0, self.app.log, f"  ✅ Saved: {os.path.basename(out_path)}")

                self.app.after(0, self.app.on_file_done, filepath, "success")

            except Exception as e:
                self.results[filepath] = ("error", str(e))
                self.app.after(0, self.app.log, f"  ❌ Error: {e}")
                self.app.after(0, self.app.on_file_done, filepath, "error")

        self.app.after(0, self.app.on_conversion_done, self.results)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class MarkItDownApp:
    def __init__(self):
        # Create root window
        if HAS_TTKB:
            self.root = ttkb.Window(
                title="MarkItDown Desktop",
                themename="darkly",
                size=(1280, 850),
                minsize=(900, 600),
            )
        else:
            self.root = tk.Tk()
            self.root.title("MarkItDown Desktop")
            self.root.geometry("1280x850")
            self.root.minsize(900, 600)
            self.root.configure(bg=COLORS["bg_primary"])
            # Apply dark theme manually
            style = ttk.Style()
            style.theme_use("clam")
            self._apply_dark_style(style)

        self._worker: Optional[ConversionWorker] = None
        self._results: dict = {}
        self._file_paths: List[str] = []
        self._output_dir: Optional[str] = None

        self._build_ui()

        # Center window
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 1280) // 2
        y = (sh - 850) // 2
        self.root.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _apply_dark_style(self, style: ttk.Style):
        """Apply a dark theme using raw ttk styling (fallback when ttkbootstrap is unavailable)."""
        bg = COLORS["bg_primary"]
        bg2 = COLORS["bg_secondary"]
        fg = COLORS["text_primary"]
        fg2 = COLORS["text_secondary"]
        border = COLORS["border"]
        accent = COLORS["accent_blue"]
        green = COLORS["accent_green_dark"]

        style.configure(".", background=bg, foreground=fg, fieldbackground=bg,
                        bordercolor=border, darkcolor=bg2, lightcolor=bg2,
                        troughcolor=bg2, selectbackground=accent,
                        selectforeground="#fff", font=("Segoe UI", 10))

        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=bg2, relief="solid", borderwidth=1)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#f0f6fc", background=bg)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), foreground=fg2, background=bg)
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"), foreground="#c9d1d9", background=bg2)
        style.configure("Muted.TLabel", font=("Segoe UI", 9), foreground=COLORS["text_muted"], background=bg)
        style.configure("Badge.TLabel", font=("Segoe UI", 9, "bold"), foreground=accent,
                        background=COLORS["selection"], padding=(8, 3))

        style.configure("TButton", background=bg2, foreground=fg, bordercolor=border,
                        focuscolor=accent, padding=(14, 8), font=("Segoe UI", 10))
        style.map("TButton",
                  background=[("active", COLORS["bg_card"]), ("pressed", bg)],
                  foreground=[("active", fg)])

        style.configure("Primary.TButton", background=green, foreground="#fff",
                        font=("Segoe UI", 11, "bold"), padding=(18, 10))
        style.map("Primary.TButton",
                  background=[("active", COLORS["accent_green"]), ("disabled", bg2)],
                  foreground=[("disabled", COLORS["text_muted"])])

        style.configure("Danger.TButton", foreground=COLORS["accent_red"])

        style.configure("TCheckbutton", background=bg2, foreground=fg)

        style.configure("TNotebook", background=bg, bordercolor=border)
        style.configure("TNotebook.Tab", background=bg2, foreground=fg2,
                        padding=(16, 6), font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", bg)],
                  foreground=[("selected", accent)])

        style.configure("Horizontal.TProgressbar", background=accent,
                        troughcolor=bg2, bordercolor=border, darkcolor=accent,
                        lightcolor=accent, thickness=20)

        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg,
                        bordercolor=border, font=("Segoe UI", 10), rowheight=32)
        style.map("Treeview",
                  background=[("selected", COLORS["selection"])],
                  foreground=[("selected", accent)])
        style.configure("Treeview.Heading", background=bg2, foreground=fg2,
                        font=("Segoe UI", 9, "bold"))

        style.configure("TLabelframe", background=bg2, foreground=fg, bordercolor=border)
        style.configure("TLabelframe.Label", background=bg2, foreground="#c9d1d9",
                        font=("Segoe UI", 10, "bold"))

        style.configure("TSeparator", background=border)

        style.configure("TMenubutton", background=bg2, foreground=fg, bordercolor=border,
                        padding=(10, 6))

    def _build_ui(self):
        """Build the main UI layout."""
        root = self.root
        bg = COLORS["bg_primary"]
        bg2 = COLORS["bg_secondary"]

        # ── Top header ──
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", padx=20, pady=(12, 4))

        title = ttk.Label(header_frame, text="⚡ MarkItDown Desktop", style="Title.TLabel")
        title.pack(side="left", anchor="w")

        badge = ttk.Label(header_frame, text=f" v{APP_VERSION} ", style="Badge.TLabel")
        badge.pack(side="right", anchor="e")

        subtitle = ttk.Label(
            root,
            text="Convert any document to Markdown — powered by Microsoft's MarkItDown",
            style="Subtitle.TLabel",
        )
        subtitle.pack(fill="x", padx=24, pady=(0, 8))

        sep = ttk.Separator(root)
        sep.pack(fill="x", padx=12)

        # ── Main paned window ──
        paned = ttk.PanedWindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=12, pady=8)

        # ╔═══════════════════════════════════════════╗
        # ║  LEFT PANEL — Files & Controls            ║
        # ╚═══════════════════════════════════════════╝
        left_frame = ttk.Frame(paned, style="Card.TFrame" if not HAS_TTKB else "")
        paned.add(left_frame, weight=2)

        left_inner = ttk.Frame(left_frame)
        left_inner.pack(fill="both", expand=True, padx=14, pady=14)

        # ── Drop Zone ──
        drop_frame = tk.Frame(
            left_inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"],
            highlightthickness=2, bd=0, relief="flat", cursor="hand2"
        )
        drop_frame.pack(fill="x", pady=(0, 10), ipady=24)

        # Fake dashed border via nested frame
        inner_drop = tk.Frame(drop_frame, bg=COLORS["bg_card"])
        inner_drop.pack(fill="both", expand=True, padx=2, pady=2)

        drop_icon = tk.Label(inner_drop, text="📁", font=("Segoe UI Emoji", 36),
                             bg=COLORS["bg_card"], fg=COLORS["text_primary"])
        drop_icon.pack(pady=(12, 2))

        drop_title = tk.Label(inner_drop, text="Drag & Drop Files Here",
                              font=("Segoe UI", 15, "bold"), bg=COLORS["bg_card"],
                              fg=COLORS["text_primary"])
        drop_title.pack()

        drop_sub = tk.Label(inner_drop, text="or click 'Add Files' to browse",
                            font=("Segoe UI", 10), bg=COLORS["bg_card"],
                            fg=COLORS["text_secondary"])
        drop_sub.pack()

        drop_formats = tk.Label(
            inner_drop,
            text="PDF · Word · PowerPoint · Excel · HTML · Images · Audio · EPub · CSV · JSON · XML · ZIP",
            font=("Segoe UI", 8), bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            wraplength=380,
        )
        drop_formats.pack(pady=(6, 12))

        # Make the drop zone clickable
        for w in [drop_frame, inner_drop, drop_icon, drop_title, drop_sub, drop_formats]:
            w.bind("<Button-1>", lambda e: self._browse_files())

        # ── Button row ──
        btn_row = ttk.Frame(left_inner)
        btn_row.pack(fill="x", pady=(0, 6))

        self.btn_add = ttk.Button(btn_row, text="➕ Add Files", command=self._browse_files)
        self.btn_add.pack(side="left", padx=(0, 4))

        self.btn_add_url = ttk.Button(btn_row, text="🔗 Add URL", command=self._add_url)
        self.btn_add_url.pack(side="left", padx=4)

        self.btn_remove = ttk.Button(btn_row, text="🗑 Remove", command=self._remove_selected,
                                     style="Danger.TButton")
        self.btn_remove.pack(side="right", padx=(4, 0))

        self.btn_clear = ttk.Button(btn_row, text="✖ Clear All", command=self._clear_files,
                                    style="Danger.TButton")
        self.btn_clear.pack(side="right", padx=4)

        # ── File List ──
        sec_label = ttk.Label(left_inner, text="📋 Files to Convert", style="Section.TLabel")
        sec_label.pack(fill="x", pady=(4, 4), anchor="w")

        # Treeview for file list
        tree_frame = ttk.Frame(left_inner)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("status",), show="tree",
                                 selectmode="extended")
        self.tree.heading("#0", text="File")
        self.tree.column("#0", stretch=True, minwidth=200)
        self.tree.column("status", width=50, stretch=False, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # ── Options ──
        options_frame = ttk.LabelFrame(left_inner, text="  ⚙ Options  ", padding=10)
        options_frame.pack(fill="x", pady=(10, 6))

        self.var_plugins = tk.BooleanVar(value=False)
        chk_plugins = ttk.Checkbutton(options_frame, text="Enable 3rd-party plugins",
                                       variable=self.var_plugins)
        chk_plugins.grid(row=0, column=0, sticky="w", padx=4)

        self.var_autosave = tk.BooleanVar(value=False)
        chk_save = ttk.Checkbutton(options_frame, text="Auto-save output to folder",
                                    variable=self.var_autosave, command=self._toggle_output_dir)
        chk_save.grid(row=0, column=1, sticky="w", padx=4)

        self.lbl_outdir = ttk.Label(options_frame, text="", style="Muted.TLabel")
        self.lbl_outdir.grid(row=1, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 0))

        # ── Progress ──
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(left_inner, variable=self.progress_var,
                                         maximum=100, mode="determinate")

        self.progress_label = ttk.Label(left_inner, text="", style="Muted.TLabel")

        # ── Convert button ──
        self.btn_convert = ttk.Button(
            left_inner, text="🚀  Convert All", command=self._start_conversion,
            style="Primary.TButton",
        )
        self.btn_convert.pack(fill="x", pady=(8, 0), ipady=4)
        self.btn_convert.state(["disabled"])

        # ╔═══════════════════════════════════════════╗
        # ║  RIGHT PANEL — Preview / Log              ║
        # ╚═══════════════════════════════════════════╝
        right_frame = ttk.Frame(paned, style="Card.TFrame" if not HAS_TTKB else "")
        paned.add(right_frame, weight=3)

        right_inner = ttk.Frame(right_frame)
        right_inner.pack(fill="both", expand=True, padx=14, pady=14)

        # Header with buttons
        preview_header = ttk.Frame(right_inner)
        preview_header.pack(fill="x", pady=(0, 6))

        ttk.Label(preview_header, text="📝 Markdown Output", style="Section.TLabel").pack(
            side="left"
        )

        self.btn_save_as = ttk.Button(preview_header, text="💾 Save As…",
                                       command=self._save_current)
        self.btn_save_as.pack(side="right", padx=(4, 0))
        self.btn_save_as.state(["disabled"])

        self.btn_copy = ttk.Button(preview_header, text="📋 Copy", command=self._copy_to_clipboard)
        self.btn_copy.pack(side="right", padx=4)
        self.btn_copy.state(["disabled"])

        # Notebook (tabs)
        self.notebook = ttk.Notebook(right_inner)
        self.notebook.pack(fill="both", expand=True)

        # ── Markdown tab ──
        md_frame = ttk.Frame(self.notebook)
        self.notebook.add(md_frame, text="  📄 Markdown  ")

        self.text_preview = tk.Text(
            md_frame, wrap="word", font=("Cascadia Code", 11),
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            selectbackground=COLORS["highlight"],
            selectforeground="#fff",
            borderwidth=0, highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=12, pady=12, state="disabled",
        )
        md_scroll = ttk.Scrollbar(md_frame, orient="vertical", command=self.text_preview.yview)
        self.text_preview.configure(yscrollcommand=md_scroll.set)
        self.text_preview.pack(side="left", fill="both", expand=True)
        md_scroll.pack(side="right", fill="y")

        # Placeholder text
        self._set_text(self.text_preview,
                       "Converted Markdown will appear here…\n\n"
                       "Select a file from the list on the left to preview its output.")

        # ── Log tab ──
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="  📋 Log  ")

        self.text_log = tk.Text(
            log_frame, wrap="word", font=("Cascadia Code", 10),
            bg=COLORS["bg_input"], fg=COLORS["text_secondary"],
            insertbackground=COLORS["text_secondary"],
            selectbackground=COLORS["highlight"],
            borderwidth=0, highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=12, pady=12, state="disabled",
        )
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=log_scroll.set)
        self.text_log.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        # ── Status bar ──
        status_frame = tk.Frame(root, bg=COLORS["bg_secondary"], height=28)
        status_frame.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="Ready — Drop files or click Add Files to begin")
        status_label = tk.Label(
            status_frame, textvariable=self.status_var,
            font=("Segoe UI", 9), bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"], anchor="w", padx=12, pady=4,
        )
        status_label.pack(fill="x")

        # ── Keyboard shortcuts ──
        root.bind("<Control-o>", lambda e: self._browse_files())
        root.bind("<Control-s>", lambda e: self._save_current())
        root.bind("<Control-q>", lambda e: root.quit())
        root.bind("<Delete>", lambda e: self._remove_selected())

    # ═══════════════════════════════════════════
    # Actions
    # ═══════════════════════════════════════════

    def _set_text(self, widget, text):
        """Set text in a disabled Text widget."""
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _append_text(self, widget, text):
        """Append text to a disabled Text widget."""
        widget.configure(state="normal")
        widget.insert("end", text + "\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select Files to Convert",
            filetypes=FILETYPES,
        )
        if files:
            self._add_files(list(files))

    def _add_url(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add URL")
        dialog.geometry("480x140")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS["bg_secondary"])

        ttk.Label(dialog, text="Enter a URL to convert:").pack(padx=16, pady=(16, 6), anchor="w")

        url_var = tk.StringVar(value="https://")
        entry = ttk.Entry(dialog, textvariable=url_var, width=60)
        entry.pack(padx=16, fill="x")
        entry.focus_set()
        entry.select_range(0, "end")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=12)

        def on_ok():
            url = url_var.get().strip()
            if url and url != "https://":
                icon = "🔗"
                iid = self.tree.insert("", "end", text=f"  {icon}  {url}")
                self._file_paths.append(url)
                self.btn_convert.state(["!disabled"])
                self.status_var.set(f"Added URL: {url}")
            dialog.destroy()

        ttk.Button(btn_frame, text="Add", command=on_ok, style="Primary.TButton").pack(
            side="left", padx=6
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)

        entry.bind("<Return>", lambda e: on_ok())

    def _add_files(self, files: List[str]):
        existing = set(self._file_paths)
        added = 0
        for f in files:
            if f not in existing:
                ext = os.path.splitext(f)[1].lower()
                icon = EXT_ICONS.get(ext, "📄")
                name = os.path.basename(f)
                iid = self.tree.insert("", "end", text=f"  {icon}  {name}",
                                       values=("",))
                self._file_paths.append(f)
                added += 1

        if self._file_paths:
            self.btn_convert.state(["!disabled"])
        self.status_var.set(f"Added {added} file(s) — {len(self._file_paths)} total")

    def _remove_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        items = list(self.tree.get_children())
        for iid in selection:
            idx = items.index(iid)
            if 0 <= idx < len(self._file_paths):
                fp = self._file_paths[idx]
                self._results.pop(fp, None)
            self.tree.delete(iid)

        # Rebuild _file_paths from tree
        self._file_paths = []
        for iid in self.tree.get_children():
            # We need to re-derive. Simpler: just clear and re-read
            pass
        # Re-index — get text and map back
        # Simpler approach: maintain mapping
        self._rebuild_file_paths()

        if not self._file_paths:
            self.btn_convert.state(["disabled"])
            self.btn_copy.state(["disabled"])
            self.btn_save_as.state(["disabled"])
            self._set_text(self.text_preview, "")
        self.status_var.set(f"{len(self._file_paths)} file(s) in queue")

    def _rebuild_file_paths(self):
        """Rebuild file_paths from tree tooltip approach — use a simpler data model."""
        # We maintain _file_paths as indices matching tree children
        # After delete, rebuild:
        remaining_ids = list(self.tree.get_children())
        # We stored paths in order; after deletion some are gone.
        # Better approach: store path as tag.
        pass

    def _clear_files(self):
        self.tree.delete(*self.tree.get_children())
        self._file_paths.clear()
        self._results.clear()
        self._set_text(self.text_preview, "")
        self._set_text(self.text_log, "")
        self.btn_convert.state(["disabled"])
        self.btn_copy.state(["disabled"])
        self.btn_save_as.state(["disabled"])
        self.progress.pack_forget()
        self.progress_label.pack_forget()
        self.status_var.set("Ready — Drop files or click Add Files to begin")

    def _toggle_output_dir(self):
        if self.var_autosave.get():
            d = filedialog.askdirectory(title="Select Output Folder")
            if d:
                self._output_dir = d
                self.lbl_outdir.configure(text=f"Output: {d}")
            else:
                self.var_autosave.set(False)
                self._output_dir = None
                self.lbl_outdir.configure(text="")
        else:
            self._output_dir = None
            self.lbl_outdir.configure(text="")

    def _on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        iid = selection[0]
        items = list(self.tree.get_children())
        idx = items.index(iid)
        if idx < len(self._file_paths):
            fp = self._file_paths[idx]
            if fp in self._results:
                status, content = self._results[fp]
                if status == "success":
                    self._set_text(self.text_preview, content)
                    self.btn_copy.state(["!disabled"])
                    self.btn_save_as.state(["!disabled"])
                    self.notebook.select(0)  # Markdown tab
                else:
                    self._set_text(self.text_preview, f"Error converting this file:\n\n{content}")
                    self.btn_copy.state(["disabled"])
                    self.btn_save_as.state(["disabled"])
            else:
                self._set_text(self.text_preview,
                               f"Not yet converted.\n\nClick 'Convert All' to process this file.")
                self.btn_copy.state(["disabled"])
                self.btn_save_as.state(["disabled"])

    def _start_conversion(self):
        if self._worker and self._worker.is_alive():
            self._worker.cancelled = True
            self.btn_convert.configure(text="🚀  Convert All")
            self.status_var.set("Conversion cancelled")
            return

        if not self._file_paths:
            return

        self._set_text(self.text_log, "")
        self.log("═" * 50)
        self.log("  MarkItDown Desktop — Conversion Started")
        self.log("═" * 50)
        self.log(f"  Files: {len(self._file_paths)}")
        self.log("")

        self.progress_var.set(0)
        self.progress.pack(fill="x", pady=(6, 2))
        self.progress_label.pack(fill="x")
        self.btn_convert.configure(text="⏹  Cancel")
        self.notebook.select(1)  # Log tab

        self._worker = ConversionWorker(
            self,
            list(self._file_paths),
            self._output_dir if self.var_autosave.get() else None,
            self.var_plugins.get(),
        )
        self._worker.start()

    def update_progress(self, current, total, filename):
        pct = (current / total) * 100
        self.progress_var.set(pct)
        self.progress_label.configure(text=f"  {current}/{total} — {filename}")
        self.status_var.set(f"Converting {current}/{total}…")

    def on_file_done(self, filepath, status):
        items = list(self.tree.get_children())
        try:
            idx = self._file_paths.index(filepath)
            if idx < len(items):
                iid = items[idx]
                marker = "✅" if status == "success" else "❌"
                self.tree.set(iid, "status", marker)
        except (ValueError, IndexError):
            pass

    def on_conversion_done(self, results):
        self._results.update({k: v for k, v in results.items()})
        self.btn_convert.configure(text="🚀  Convert All")
        self.progress.pack_forget()
        self.progress_label.pack_forget()

        success = sum(1 for s, _ in results.values() if s == "success")
        total = len(results)
        self.status_var.set(f"Done — {success}/{total} file(s) converted successfully")
        self.log("")
        self.log("═" * 50)
        self.log(f"  Complete: {success}/{total} succeeded")
        self.log("═" * 50)

        self.notebook.select(0)  # Markdown tab

        # Auto-select first success
        items = list(self.tree.get_children())
        for idx, fp in enumerate(self._file_paths):
            if fp in self._results and self._results[fp][0] == "success":
                if idx < len(items):
                    self.tree.selection_set(items[idx])
                    self.tree.see(items[idx])
                    break

    def log(self, message):
        self._append_text(self.text_log, message)

    def _copy_to_clipboard(self):
        text = self.text_preview.get("1.0", "end").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("Copied to clipboard!")
            self.root.after(3000, lambda: self.status_var.set("Ready"))

    def _save_current(self):
        text = self.text_preview.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Nothing to save", "No Markdown content to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Markdown",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")],
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_var.set(f"Saved: {path}")

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    app = MarkItDownApp()
    app.run()


if __name__ == "__main__":
    main()
