import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
from threading import Thread
import os
from datetime import datetime
import math
from utils.helpers import get_scraper, ensure_directory
from utils.logger import get_logger
from processor.content import ContentProcessor
from video.render import SmartVideoRenderer
from video.segments import VideoSegmenter, ProductSegmenter

logger = get_logger()


class NMH03VideoProV3:
    """Complete video creator with Short/Long formats + Segment export"""
    
    VIDEO_FORMATS = {
        'short': {'name': '⚡ Short (15-30s)', 'duration': 30, 'scenes': 3, 'icon': '⚡'},
        'medium': {'name': '📹 Medium (45-60s)', 'duration': 60, 'scenes': 5, 'icon': '📹'},
        'long': {'name': '🎬 Long (2-5 min)', 'duration': 180, 'scenes': 10, 'icon': '🎬'},
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 NMH03 Video Pro v3 - Complete Edition")
        self.root.geometry("1500x900")
        self.root.resizable(True, True)
        self.root.configure(bg="#0d1117")

        self.is_processing = False
        self.video_path = None
        self.status_text = tk.StringVar(value="Ready 🚀")
        self.progress_percent = tk.IntVar(value=0)
        self.person_image_path = None
        self.segments_data = []
        self.selected_segments = []  # For export
        
        self._setup_ui()
        ensure_directory("output/videos")
        ensure_directory("output/segments")

    def _setup_ui(self):
        main = tk.Frame(self.root, bg="#0d1117")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header với gradient effect
        header = tk.Frame(main, bg="#161b22", height=100)
        header.pack(fill=tk.X, pady=(0, 20))
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg="#161b22")
        title_frame.pack(side=tk.LEFT, padx=30, pady=25)
        
        tk.Label(title_frame,
                text="🎬 NMH03 Video Pro",
                font=("Segoe UI", 26, "bold"),
                fg="#58a6ff",
                bg="#161b22").pack(anchor="w")
        
        tk.Label(title_frame,
                text="Product • Movie • Video Clipper • Auto Highlights",
                font=("Segoe UI", 10),
                fg="#8b949e",
                bg="#161b22").pack(anchor="w")
        
        # Version badge
        tk.Label(header,
                text="v3.1",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#238636",
                padx=10,
                pady=5).pack(side=tk.RIGHT, padx=30)
        
        # Tabs
        content = tk.Frame(main, bg="#0d1117")
        content.pack(fill=tk.BOTH, expand=True)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.TNotebook', 
                       background='#161b22', 
                       borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                       background='#21262d',
                       foreground='#8b949e',
                       padding=[25, 12],
                       font=('Segoe UI', 11, 'bold'))
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', '#58a6ff')],
                 foreground=[('selected', '#ffffff')])
        
        self.notebook = ttk.Notebook(content, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 4 tabs: Product, Movie, Video Clipper, Settings
        self.product_tab = tk.Frame(self.notebook, bg="#161b22")
        self.movie_tab = tk.Frame(self.notebook, bg="#161b22")
        self.clipper_tab = tk.Frame(self.notebook, bg="#161b22")
        self.settings_tab = tk.Frame(self.notebook, bg="#161b22")
        
        self.notebook.add(self.product_tab, text='  📦 Product Review  ')
        self.notebook.add(self.movie_tab, text='  📽️ Movie Review  ')
        self.notebook.add(self.clipper_tab, text='  ✂️ Video Clipper  ')
        self.notebook.add(self.settings_tab, text='  ⚙️ Settings  ')
        
        self._setup_product_tab()
        self._setup_movie_tab()
        self._setup_clipper_tab()
        self._setup_settings_tab()

    def _setup_product_tab(self):
        """Product tab with format options"""
        container = tk.Frame(self.product_tab, bg="#161b22")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left = tk.Frame(container, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(container, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # === LEFT PANEL ===
        scroll_frame = tk.Frame(left, bg="#0d1117")
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg="#0d1117", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#0d1117")
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # URL Input
        self._add_card(scrollable, "🔗 Product URL", "Shopee, TikTok Shop, etc.")
        self.product_url = tk.Text(scrollable, height=2, font=("Consolas", 10),
                                   bg="#21262d", fg="#c9d1d9", insertbackground="#58a6ff",
                                   relief=tk.FLAT, wrap=tk.WORD, padx=10, pady=10)
        self.product_url.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Video Format Selection
        self._add_card(scrollable, "📐 Video Format", "Choose video length")
        format_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        format_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.product_format = tk.StringVar(value='short')
        for key, fmt in self.VIDEO_FORMATS.items():
            row = tk.Frame(format_frame, bg="#21262d")
            row.pack(fill=tk.X, pady=5)
            
            rb = tk.Radiobutton(row,
                              text=fmt['name'],
                              variable=self.product_format,
                              value=key,
                              font=("Segoe UI", 11, "bold"),
                              bg="#21262d", fg="#c9d1d9",
                              selectcolor="#161b22",
                              activebackground="#21262d",
                              cursor="hand2")
            rb.pack(side=tk.LEFT, padx=5)
            
            tk.Label(row,
                    text=f"~{fmt['duration']}s, {fmt['scenes']} scenes",
                    font=("Segoe UI", 9),
                    fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=10)
        
        # Video Style
        self._add_card(scrollable, "🎨 Video Style", "Presentation mode")
        style_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        style_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.product_mode = tk.StringVar(value='simple')
        for mode, label, desc in [
            ('simple', '📹 Simple', 'Product + text + voiceover'),
            ('reviewer', '🎙️ Reviewer', 'Talking head (AI avatar)')
        ]:
            row = tk.Frame(style_frame, bg="#21262d")
            row.pack(fill=tk.X, pady=5)
            rb = tk.Radiobutton(row, text=label, variable=self.product_mode,
                              value=mode, font=("Segoe UI", 11, "bold"),
                              bg="#21262d", fg="#c9d1d9", selectcolor="#161b22")
            rb.pack(side=tk.LEFT, padx=5)
            tk.Label(row, text=desc, font=("Segoe UI", 9),
                    fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=10)
        
        # AI Avatar
        self._add_card(scrollable, "🤖 AI Avatar (Optional)", "For Reviewer mode only")
        avatar_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        avatar_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.product_use_avatar = tk.BooleanVar(value=False)
        tk.Checkbutton(avatar_frame,
                      text="Enable Talking Avatar",
                      variable=self.product_use_avatar,
                      font=("Segoe UI", 10, "bold"),
                      bg="#21262d", fg="#58a6ff",
                      selectcolor="#161b22").pack(anchor="w")
        
        tk.Button(avatar_frame,
                 text="📁 Upload Face Image",
                 font=("Segoe UI", 10, "bold"),
                 bg="#238636", fg="#ffffff",
                 activebackground="#2ea043",
                 relief=tk.FLAT, cursor="hand2",
                 command=lambda: self._select_image("product")).pack(pady=(10, 0), ipadx=20, ipady=8)
        
        # === RIGHT PANEL ===
        btn_frame = tk.Frame(right, bg="#21262d", padx=25, pady=25)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame,
                 text="🚀 Generate Product Video",
                 font=("Segoe UI", 16, "bold"),
                 bg="#1f6feb", fg="#ffffff",
                 activebackground="#1158c7",
                 relief=tk.FLAT, cursor="hand2",
                 command=lambda: self._generate("product")).pack(fill=tk.X, ipady=20)
        
        self._add_status_panel(right)
        self._add_tips_panel(right, [
            "⚡ Short: Best for TikTok/Reels (viral)",
            "📹 Medium: Instagram/YouTube Shorts",
            "🎬 Long: Full review for YouTube"
        ])

    def _setup_movie_tab(self):
        """Movie tab with segment export"""
        container = tk.Frame(self.movie_tab, bg="#161b22")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left = tk.Frame(container, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(container, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # LEFT
        scroll_frame = tk.Frame(left, bg="#0d1117")
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg="#0d1117", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#0d1117")
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content Type Selection
        self._add_card(scrollable, "📚 Content Type", "Choose what to create")
        content_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        content_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.movie_content_type = tk.StringVar(value='movie')
        
        for ctype, label, desc in [
            ('movie', '🎬 Movie Review', 'IMDb, Wikipedia movie'),
            ('story', '📖 Web Story/Article', 'Blog, news, any webpage')
        ]:
            row = tk.Frame(content_frame, bg="#21262d")
            row.pack(fill=tk.X, pady=5)
            rb = tk.Radiobutton(row, text=label, variable=self.movie_content_type,
                              value=ctype, font=("Segoe UI", 11, "bold"),
                              bg="#21262d", fg="#c9d1d9", selectcolor="#161b22",
                              command=self._toggle_movie_input_type)
            rb.pack(side=tk.LEFT, padx=5)
            tk.Label(row, text=desc, font=("Segoe UI", 9),
                    fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=10)
        
        # Movie Input
        self._add_card(scrollable, "🎬 Movie URL or Name", "IMDb, Wikipedia, or title")
        self.movie_input_help = tk.Label(scrollable,
                            text="Examples: 'https://imdb.com/title/tt123', 'Oppenheimer', 'Avatar 2'",
                            font=("Segoe UI", 9),
                            fg="#8b949e", bg="#0d1117")
        self.movie_input_help.pack(padx=25, pady=(0, 5), anchor="w")
        
        self.movie_url = tk.Text(scrollable, height=2, font=("Consolas", 10),
                                bg="#21262d", fg="#c9d1d9", insertbackground="#58a6ff",
                                relief=tk.FLAT, wrap=tk.WORD, padx=10, pady=10)
        self.movie_url.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Video Duration Slider
        self._add_card(scrollable, "⏱️ Video Duration", "Drag to set video length")
        slider_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        slider_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Label showing current value
        duration_label_frame = tk.Frame(slider_frame, bg="#21262d")
        duration_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(duration_label_frame, text="Duration:", font=("Segoe UI", 10, "bold"),
                 fg="#c9d1d9", bg="#21262d").pack(side=tk.LEFT)
        
        self.movie_duration_var = tk.IntVar(value=60)
        self.movie_duration_label = tk.Label(duration_label_frame, 
                                             text="60s (Medium)", 
                                             font=("Segoe UI", 12, "bold"),
                                             fg="#58a6ff", bg="#21262d")
        self.movie_duration_label.pack(side=tk.LEFT, padx=10)
        
        # Slider (15s to 180s)
        self.movie_duration_slider = tk.Scale(slider_frame,
                                             from_=15, to=180,
                                             orient=tk.HORIZONTAL,
                                             variable=self.movie_duration_var,
                                             font=("Segoe UI", 10),
                                             bg="#161b22", fg="#c9d1d9",
                                             highlightthickness=0,
                                             troughcolor="#0d1117",
                                             activebackground="#58a6ff",
                                             command=self._update_duration_label,
                                             length=400,
                                             width=20)
        self.movie_duration_slider.pack(fill=tk.X, pady=(0, 5))
        
        # Quick presets
        preset_frame = tk.Frame(slider_frame, bg="#21262d")
        preset_frame.pack(fill=tk.X)
        
        for label, seconds in [("⚡ Short", 30), ("📹 Medium", 60), ("🎬 Long", 120)]:
            tk.Button(preset_frame, text=label,
                     font=("Segoe UI", 9),
                     bg="#238636", fg="#ffffff",
                     relief=tk.FLAT, cursor="hand2",
                     command=lambda s=seconds: self.movie_duration_var.set(s),
                     padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Segment Detection
        self._add_card(scrollable, "✂️ Auto Segment Detection", "Smart chapter detection")
        seg_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        seg_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.enable_segments = tk.BooleanVar(value=True)
        tk.Checkbutton(seg_frame,
                      text="✓ Detect chapters (Intro, Plot, Highlights, Review)",
                      variable=self.enable_segments,
                      font=("Segoe UI", 10, "bold"),
                      bg="#21262d", fg="#58a6ff",
                      selectcolor="#161b22").pack(anchor="w")
        
        self.suggest_clips = tk.BooleanVar(value=False)
        tk.Checkbutton(seg_frame,
                      text="✓ Suggest 60s clips for TikTok/Reels",
                      variable=self.suggest_clips,
                      font=("Segoe UI", 10, "bold"),
                      bg="#21262d", fg="#58a6ff",
                      selectcolor="#161b22").pack(anchor="w", pady=(10, 0))
        
        # Detected Segments Display
        self._add_card(scrollable, "📊 Detected Segments", "Auto-detected chapters")
        segments_container = tk.Frame(scrollable, bg="#21262d")
        segments_container.pack(fill=tk.BOTH, padx=20, pady=(0, 20))
        
        self.segments_text = scrolledtext.ScrolledText(segments_container,
                                                       height=8,
                                                       font=("Consolas", 9),
                                                       bg="#161b22", fg="#c9d1d9",
                                                       relief=tk.FLAT,
                                                       padx=10, pady=10,
                                                       wrap=tk.WORD)
        self.segments_text.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # Export buttons
        export_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        export_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(export_frame,
                 text="💾 Export All Segments",
                 font=("Segoe UI", 10, "bold"),
                 bg="#6e40c9", fg="#ffffff",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._export_segments).pack(side=tk.LEFT, padx=5, ipadx=15, ipady=8)
        
        tk.Button(export_frame,
                 text="📋 Copy Timestamps",
                 font=("Segoe UI", 10, "bold"),
                 bg="#8b949e", fg="#ffffff",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._copy_timestamps).pack(side=tk.LEFT, padx=5, ipadx=15, ipady=8)
        
        # RIGHT
        btn_frame = tk.Frame(right, bg="#21262d", padx=25, pady=25)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame,
                 text="🎬 Generate Movie Review",
                 font=("Segoe UI", 16, "bold"),
                 bg="#da3633", fg="#ffffff",
                 activebackground="#b62324",
                 relief=tk.FLAT, cursor="hand2",
                 command=lambda: self._generate("movie")).pack(fill=tk.X, ipady=20)
        
        self._add_status_panel(right)
        self._add_tips_panel(right, [
            "✂️ Auto-detects Intro/Plot/Review",
            "📤 Export segments separately",
            "📋 Copy timestamps for YouTube"
        ])

    def _setup_clipper_tab(self):
        """Video Clipper tab - Cut existing videos into highlights"""
        container = tk.Frame(self.clipper_tab, bg="#161b22")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left = tk.Frame(container, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(container, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # LEFT
        scroll_frame = tk.Frame(left, bg="#0d1117")
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg="#0d1117", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#0d1117")
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Video Source Selection
        self._add_card(scrollable, "📹 Video Source", "URL or Local File")
        
        # Source type radio
        source_type_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=10)
        source_type_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.clipper_source_type = tk.StringVar(value='url')
        for src_key, src_label in [('url', '🌐 URL'), ('file', '📁 Local File')]:
            rb = tk.Radiobutton(source_type_frame, text=src_label, 
                              variable=self.clipper_source_type,
                              value=src_key, font=("Segoe UI", 11, "bold"),
                              bg="#21262d", fg="#c9d1d9", selectcolor="#161b22",
                              command=self._toggle_clipper_source)
            rb.pack(side=tk.LEFT, padx=10)
        
        # URL Input (shown by default)
        self.clipper_url_frame = tk.Frame(scrollable, bg="#0d1117")
        self.clipper_url_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        help_text = tk.Label(self.clipper_url_frame,
                            text="Example: 'https://youtube.com/watch?v=...', 'https://tiktok.com/@user/video/...'",
                            font=("Segoe UI", 9),
                            fg="#8b949e", bg="#0d1117")
        help_text.pack(padx=5, pady=(0, 5), anchor="w")
        
        self.clipper_url = tk.Text(self.clipper_url_frame, height=2, font=("Consolas", 10),
                                   bg="#21262d", fg="#c9d1d9", insertbackground="#58a6ff",
                                   relief=tk.FLAT, wrap=tk.WORD, padx=10, pady=10)
        self.clipper_url.pack(fill=tk.X, pady=(0, 5))
        
        # File Browser (hidden by default)
        self.clipper_file_frame = tk.Frame(scrollable, bg="#0d1117")
        # Don't pack yet - will show/hide with toggle
        
        file_help = tk.Label(self.clipper_file_frame,
                            text="Click to browse video files (MP4, AVI, MOV, MKV)",
                            font=("Segoe UI", 9),
                            fg="#8b949e", bg="#0d1117")
        file_help.pack(padx=5, pady=(0, 5), anchor="w")
        
        file_btn_frame = tk.Frame(self.clipper_file_frame, bg="#21262d", padx=15, pady=15)
        file_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.clipper_file_path = tk.StringVar(value="")
        tk.Button(file_btn_frame,
                 text="📂 Choose Video File",
                 font=("Segoe UI", 11, "bold"),
                 bg="#238636", fg="#ffffff",
                 activebackground="#2ea043",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._browse_video_file).pack(side=tk.LEFT, padx=5, ipadx=20, ipady=10)
        
        self.clipper_file_label = tk.Label(file_btn_frame,
                                          text="No file selected",
                                          font=("Segoe UI", 10),
                                          fg="#8b949e", bg="#21262d")
        self.clipper_file_label.pack(side=tk.LEFT, padx=15)
        
        # Clip Format
        self._add_card(scrollable, "📐 Clip Format", "Output clip length")
        format_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        format_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.clipper_format = tk.StringVar(value='short')
        for fmt_key, fmt_info in [
            ('short', '⚡ Short (15-30s) - TikTok/Reels viral'),
            ('medium', '📹 Medium (30-60s) - Instagram/YouTube Shorts')
        ]:
            row = tk.Frame(format_frame, bg="#21262d")
            row.pack(fill=tk.X, pady=5)
            rb = tk.Radiobutton(row, text=fmt_info, variable=self.clipper_format,
                              value=fmt_key, font=("Segoe UI", 11, "bold"),
                              bg="#21262d", fg="#c9d1d9", selectcolor="#161b22")
            rb.pack(side=tk.LEFT, padx=5)
        
        # Number of Clips
        self._add_card(scrollable, "🎬 Number of Clips", "How many highlights to extract")
        num_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        num_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(num_frame, text="Extract:", font=("Segoe UI", 10, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        self.num_clips = tk.IntVar(value=5)
        tk.Spinbox(num_frame, from_=1, to=10, textvariable=self.num_clips,
                  font=("Segoe UI", 11), width=10,
                  bg="#161b22", fg="#c9d1d9", relief=tk.FLAT).pack(side=tk.LEFT, padx=10)
        
        tk.Label(num_frame, text="best clips", font=("Segoe UI", 10),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT)
        
        # Detection Method
        self._add_card(scrollable, "🔍 Detection Method", "How to find highlights")
        method_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        method_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.detection_method = tk.StringVar(value='audio')
        for method, label, desc in [
            ('audio', '🔊 Audio Peaks', 'Loud/exciting moments (fastest)'),
            ('semantic', '🧠 Content (ASR)', 'Understand speech, pick best lines'),
            ('uniform', '📏 Uniform', 'Evenly spaced clips (simple)')
        ]:
            row = tk.Frame(method_frame, bg="#21262d")
            row.pack(fill=tk.X, pady=5)
            rb = tk.Radiobutton(row, text=label, variable=self.detection_method,
                              value=method, font=("Segoe UI", 11, "bold"),
                              bg="#21262d", fg="#c9d1d9", selectcolor="#161b22")
            rb.pack(side=tk.LEFT, padx=5)
            tk.Label(row, text=desc, font=("Segoe UI", 9),
                    fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=10)
        
        # Detected Highlights Display
        self._add_card(scrollable, "📊 Detected Highlights", "Auto-detected exciting moments")
        highlights_container = tk.Frame(scrollable, bg="#21262d")
        highlights_container.pack(fill=tk.BOTH, padx=20, pady=(0, 20))
        
        self.highlights_text = scrolledtext.ScrolledText(highlights_container,
                                                         height=10,
                                                         font=("Consolas", 9),
                                                         bg="#161b22", fg="#c9d1d9",
                                                         relief=tk.FLAT,
                                                         padx=10, pady=10,
                                                         wrap=tk.WORD)
        self.highlights_text.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # RIGHT
        btn_frame = tk.Frame(right, bg="#21262d", padx=25, pady=25)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.clipper_btn = tk.Button(btn_frame,
                 text="✂️ Auto-Cut Video",
                 font=("Segoe UI", 16, "bold"),
                 bg="#f85149", fg="#ffffff",
                 activebackground="#da3633",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._auto_cut_video)
        self.clipper_btn.pack(fill=tk.X, ipady=20)
        
        self._add_status_panel(right)
        self._add_tips_panel(right, [
            "📥 Downloads video automatically",
            "🔊 Detects exciting moments",
            "✂️ Cuts into TikTok-ready clips",
            "💾 Saves to output/clips/"
        ])

    def _setup_settings_tab(self):
        """Settings tab"""
        container = tk.Frame(self.settings_tab, bg="#161b22", padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        self._add_card(container, "⚙️ API Configuration", "Optional AI services")
        
        settings = [
            ("OPENAI_API_KEY", "OpenAI API Key (for ChatGPT script generation)"),
            ("OMDB_API_KEY", "OMDb API Key (for movie metadata)"),
            ("DID_API_KEY", "D-ID API Key (premium avatar)"),
        ]
        
        for key, desc in settings:
            frame = tk.Frame(container, bg="#21262d", padx=20, pady=15)
            frame.pack(fill=tk.X, pady=10)
            
            tk.Label(frame, text=desc, font=("Segoe UI", 10, "bold"),
                    fg="#c9d1d9", bg="#21262d").pack(anchor="w")
            
            entry = tk.Entry(frame, font=("Consolas", 10),
                           bg="#161b22", fg="#c9d1d9",
                           insertbackground="#58a6ff",
                           relief=tk.FLAT, show="*")
            entry.pack(fill=tk.X, pady=(5, 0), ipady=8)
        
        tk.Button(container,
                 text="💾 Save Settings",
                 font=("Segoe UI", 12, "bold"),
                 bg="#238636", fg="#ffffff",
                 relief=tk.FLAT, cursor="hand2").pack(pady=20, ipadx=30, ipady=12)

    def _add_card(self, parent, title, subtitle=""):
        """Add section card"""
        frame = tk.Frame(parent, bg="#0d1117")
        frame.pack(fill=tk.X, padx=20, pady=(20, 5))
        
        tk.Label(frame, text=title, font=("Segoe UI", 14, "bold"),
                fg="#c9d1d9", bg="#0d1117").pack(anchor="w")
        
        if subtitle:
            tk.Label(frame, text=subtitle, font=("Segoe UI", 9),
                    fg="#8b949e", bg="#0d1117").pack(anchor="w")

    def _add_status_panel(self, parent):
        """Add status panel"""
        status_card = tk.Frame(parent, bg="#21262d", padx=20, pady=20)
        status_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(status_card, text="📊 Status", font=("Segoe UI", 13, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(anchor="w", pady=(0, 10))
        
        self.status_label = tk.Label(status_card, textvariable=self.status_text,
                                     font=("Segoe UI", 10), fg="#8b949e", bg="#21262d",
                                     wraplength=500, justify=tk.LEFT)
        self.status_label.pack(anchor="w", pady=(0, 15))
        
        self.progress_bar = ttk.Progressbar(status_card, variable=self.progress_percent,
                                           maximum=100, length=500)
        self.progress_bar.pack(fill=tk.X)

    def _add_tips_panel(self, parent, tips):
        """Add tips panel"""
        tips_card = tk.Frame(parent, bg="#21262d", padx=20, pady=20)
        tips_card.pack(fill=tk.X)
        
        tk.Label(tips_card, text="💡 Tips", font=("Segoe UI", 12, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(anchor="w", pady=(0, 10))
        
        for tip in tips:
            tk.Label(tips_card, text=tip, font=("Segoe UI", 9),
                    fg="#8b949e", bg="#21262d", wraplength=500,
                    justify=tk.LEFT).pack(anchor="w", pady=2)

    def _select_image(self, tab):
        """Upload image"""
        path = filedialog.askopenfilename(
            title="Select Face Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )
        if path:
            self.person_image_path = path
            self.status_text.set(f"✅ Image loaded: {os.path.basename(path)}")

    def _generate(self, content_type):
        """Generate video"""
        if self.is_processing:
            return
        
        url = (self.product_url.get("1.0", tk.END) if content_type == "product" 
               else self.movie_url.get("1.0", tk.END)).strip()
        
        if not url:
            messagebox.showwarning("Missing Input", f"Please enter {content_type} URL")
            return
        
        self.is_processing = True
        self.progress_percent.set(0)
        
        thread = threading.Thread(target=self._generate_worker, args=(url, content_type))
        thread.daemon = True
        thread.start()

    def _generate_worker(self, url, content_type):
        """Background worker"""
        try:
            self._ui("🔄 Starting...", 5)
            
            # Determine actual content type (movie vs story)
            actual_type = content_type
            if content_type == "movie" and hasattr(self, 'movie_content_type'):
                actual_type = self.movie_content_type.get()
            
            # Get target duration from slider
            target_duration = self.movie_duration_var.get() if hasattr(self, 'movie_duration_var') else 60
            
            # Calculate number of scenes based on duration
            avg_per_scene = 15  # Average 15 seconds per scene
            num_scenes = max(3, min(12, math.ceil(target_duration / avg_per_scene)))
            
            self._ui(f"📥 Fetching {actual_type} data...", 10)
            
            # Get appropriate scraper
            if actual_type == "story":
                try:
                    # Import directly to avoid circular imports
                    import sys
                    sys.path.insert(0, 'scraper')
                    from web_story import WebStoryCScraper
                    scraper = WebStoryCScraper()
                except ImportError as e:
                    raise ValueError(f"Web story scraper not found: {e}")
            else:
                scraper = get_scraper(url)
                if not scraper:
                    raise ValueError("Unsupported platform")
            
            data = scraper.scrape(url)
            if not data.get("title"):
                raise ValueError("Failed to fetch data")
            
            self._ui("🔄 Processing content...", 30)
            
            # For story mode, process differently
            if actual_type == "story":
                processed = {
                    'title': data.get('title', 'Story'),
                    'description': data.get('description', ''),
                    'content': data.get('content', ''),
                    'image_urls': data.get('image_urls', [])  # Use downloaded images from scraper
                }
            else:
                processor = ContentProcessor()
                processed = processor.process(data)
            
            # Get settings
            if content_type == "product":
                mode = self.product_mode.get()
                use_avatar = self.product_use_avatar.get()
                # Get format for product
                format_key = self.product_format.get()
                format_info = self.VIDEO_FORMATS[format_key]
            else:
                mode = "simple"
                use_avatar = False
            
            processed["person_image_path"] = self.person_image_path
            
            # Create renderer
            renderer = SmartVideoRenderer(
                video_mode=mode,
                use_ai_avatar=use_avatar,
                avatar_backend="wav2lip",
                content_type=actual_type
            )
            
            # Generate script based on content type and format
            self._ui(f"📝 Generating {actual_type} script ({target_duration}s)...", 40)
            
            if actual_type == "story":
                try:
                    from video.story_generator import StoryScriptGenerator
                    story_gen = StoryScriptGenerator()
                    script = story_gen.generate(
                        processed['title'],
                        processed.get('description', ''),
                        processed.get('content', ''),
                        max_scenes=num_scenes
                    )
                except ImportError:
                    raise ValueError("Story generator not found")
            else:
                script = renderer.script_gen.generate(
                    processed['title'],
                    processed['description'],
                    processed.get('price', '')
                )
            
            # Pass script to renderer so it doesn't regenerate
            processed["script"] = script
            
            # Limit script to calculated scenes
            script = script[:num_scenes]
            
            # SEGMENT DETECTION for movies
            if content_type == "movie" and actual_type == "movie" and self.enable_segments.get():
                self._ui("✂️ Detecting segments...", 45)
                segmenter = VideoSegmenter()
                segments = segmenter.detect_segments(script)
                self.segments_data = segments
                
                self.root.after(0, lambda: self._display_segments(segments))
                
                if self.suggest_clips.get():
                    clips = segmenter.suggest_clips(segments, 60)
                    logger.info(f"💡 Suggested {len(clips)} clips")
            
            # Render
            self._ui(f"🎬 Rendering video ({target_duration}s)...", 50)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/videos/{content_type}_{actual_type}_{timestamp}.mp4"
            
            success = renderer.render(
                processed,
                output_path,
                max_images=len(script),
                target_duration=target_duration,
                progress_callback=lambda msg, pct: self._ui(msg, pct)
            )
            
            if success:
                self.video_path = output_path
                self._ui("✅ Video complete!", 100)
                self.root.after(100, lambda: messagebox.showinfo(
                    "Success", f"Video saved:\n{output_path}"
                ))
            else:
                raise Exception("Rendering failed")
                
        except Exception as e:
            logger.exception("Generation failed")
            self._ui(f"❌ Error: {str(e)}", 0)
            self.root.after(100, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_processing = False

    def _display_segments(self, segments):
        """Display detected segments"""
        self.segments_text.delete("1.0", tk.END)
        
        time_offset = 0
        for i, seg in enumerate(segments):
            seg_type = seg['type'].upper()
            duration = seg['duration_estimate']
            num_sents = len(seg['sentences'])
            
            timestamp = f"[{self._format_time(time_offset)} - {self._format_time(time_offset + duration)}]"
            line = f"{i+1}. {timestamp} {seg_type} ({num_sents} sentences, {duration:.1f}s)\n"
            
            self.segments_text.insert(tk.END, line)
            time_offset += duration
        
        self.segments_text.insert(tk.END, f"\n✅ Total: {len(segments)} segments, ~{time_offset:.1f}s")

    def _format_time(self, seconds):
        """Format seconds to MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _export_segments(self):
        """Export segments as separate videos"""
        if not self.segments_data:
            messagebox.showwarning("No Segments", "Generate a movie review first")
            return
        
        messagebox.showinfo("Export", f"Exporting {len(self.segments_data)} segments...")
        # TODO: Implement segment export

    def _copy_timestamps(self):
        """Copy timestamps to clipboard"""
        if not self.segments_data:
            messagebox.showwarning("No Segments", "Generate a movie review first")
            return
        
        text = self.segments_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Timestamps copied to clipboard!")

    def _toggle_movie_input_type(self):
        """Toggle between Movie and Story input"""
        content_type = self.movie_content_type.get()
        
        if content_type == 'story':
            self.movie_input_help.config(
                text="Example: 'https://example.com/article', 'https://news-site.com/story'"
            )
        else:
            self.movie_input_help.config(
                text="Examples: 'https://imdb.com/title/tt123', 'Oppenheimer', 'Avatar 2'"
            )

    def _update_duration_label(self, value):
        """Update duration label when slider moves"""
        seconds = int(float(value))
        
        # Determine category
        if seconds <= 40:
            category = "Short"
            icon = "⚡"
        elif seconds <= 90:
            category = "Medium"
            icon = "📹"
        else:
            category = "Long"
            icon = "🎬"
        
        self.movie_duration_label.config(text=f"{seconds}s ({icon} {category})")

    def _toggle_clipper_source(self):
        """Toggle between URL and file input"""
        source_type = self.clipper_source_type.get()
        
        if source_type == 'url':
            # Show URL, hide file
            self.clipper_file_frame.pack_forget()
            self.clipper_url_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        else:
            # Show file, hide URL
            self.clipper_url_frame.pack_forget()
            self.clipper_file_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

    def _browse_video_file(self):
        """Browse for local video file"""
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.clipper_file_path.set(path)
            filename = os.path.basename(path)
            self.clipper_file_label.config(
                text=f"✓ {filename[:35]}..." if len(filename) > 35 else f"✓ {filename}",
                fg="#3fb950"
            )

    def _auto_cut_video(self):
        """Auto-cut video into highlights"""
        source_type = self.clipper_source_type.get()
        
        # Get video source
        if source_type == 'url':
            video_source = self.clipper_url.get("1.0", tk.END).strip()
            if not video_source:
                messagebox.showwarning("Missing URL", "Please paste a video URL")
                return
        else:  # file
            video_source = self.clipper_file_path.get()
            if not video_source:
                messagebox.showwarning("Missing File", "Please select a video file")
                return
        
        num_clips = self.num_clips.get()
        clip_format = self.clipper_format.get()
        method = self.detection_method.get()
        
        self.clipper_btn.config(state=tk.DISABLED, bg="#6e7681")
        self.status_text.set("🔄 Processing video...")
        self.progress_percent.set(0)
        
        Thread(target=self._clip_video_worker, 
               args=(video_source, source_type, num_clips, clip_format, method),
               daemon=True).start()

    def _clip_video_worker(self, video_source, source_type, num_clips, clip_format, method):
        """Optimized worker thread for video clipping"""
        try:
            from video.clipper import SmartClipper, VideoHighlightDetector
            import time
            
            start_time = time.time()
            format_str = 'short' if clip_format == 'short' else 'medium'
            
            if source_type == 'url':
                self._ui("📥 Downloading video...", 20)
                
                clipper = SmartClipper()
                result = clipper.clip_from_url(
                    url=video_source,
                    num_clips=num_clips,
                    format=format_str,
                    method=method,
                    cleanup=True  # Auto-delete temp
                )
                
                if result.get('error'):
                    raise Exception(result['error'])
                
                clips = result.get('clips', [])
                highlights = result.get('highlights', [])
                
            else:  # local file
                self._ui("📂 Loading video...", 20)
                
                detector = VideoHighlightDetector()
                
                try:
                    # Detect
                    if method == 'semantic':
                        self._ui("🧠 Understanding content...", 40)
                    else:
                        self._ui("🔍 Analyzing audio...", 40)
                    highlights = detector.detect_highlights(video_source, num_clips, method=method)
                    
                    # Cut
                    self._ui("✂️ Cutting clips...", 60)
                    output_dir = "output/clips"
                    clips = detector.auto_clip(video_source, output_dir, num_clips, format_str, method)
                    
                finally:
                    detector.cleanup()  # Always cleanup
            
            if not clips:
                self._ui("❌ No clips generated", 0)
                def show_error():
                    messagebox.showerror("Error", "Failed to generate clips")
                self.root.after(0, show_error)
                return
            
            # Display results
            elapsed = time.time() - start_time
            self._ui("📊 Processing results...", 90)
            
            self.highlights_text.delete("1.0", tk.END)
            self.highlights_text.insert(tk.END, 
                f"✅ Generated {len(clips)} clips in {elapsed:.1f}s:\n\n")
            
            for i, (clip_path, highlight) in enumerate(zip(clips, highlights), 1):
                filename = os.path.basename(clip_path)
                score = highlight.get('score', 0) * 100
                self.highlights_text.insert(tk.END, 
                    f"{i}. {filename}\n"
                    f"   📁 {clip_path}\n"
                    f"   ⭐ Score: {score:.0f}%\n\n")
            
            # Cleanup status
            if source_type == 'url' and result.get('temp_deleted'):
                self.highlights_text.insert(tk.END, 
                    "\n🗑️ Temp video cleaned up (saved disk space)\n")
            
            self._ui(f"✅ Done! ({elapsed:.1f}s)", 100)
            
            def show_success():
                messagebox.showinfo("Success", 
                    f"✅ Created {len(clips)} clips in {elapsed:.1f}s!\n"
                    f"📁 Saved to: output/clips/")
            self.root.after(0, show_success)
            
        except ImportError as e:
            error_msg = str(e)
            is_ytdlp = 'yt_dlp' in error_msg
            self._ui("❌ Missing dependencies", 0)
            
            def show_error():
                if is_ytdlp and source_type == 'url':
                    messagebox.showerror("Error", 
                        "yt-dlp not installed!\n\n"
                        "Install: pip install yt-dlp")
                else:
                    messagebox.showerror("Error", f"Missing: {error_msg}")
            self.root.after(0, show_error)
            
        except Exception as e:
            error_msg = str(e)
            self._ui(f"❌ Error: {error_msg}", 0)
            logger.exception("Clip video failed")
            
            def show_error():
                messagebox.showerror("Error", f"Failed:\n{error_msg}")
            self.root.after(0, show_error)
            
        finally:
            def enable_button():
                self.clipper_btn.config(state=tk.NORMAL, bg="#f85149")
            self.root.after(0, enable_button)

    def _ui(self, message, progress):
        """Update UI"""
        def update():
            self.status_text.set(message)
            if progress is not None:
                self.progress_percent.set(progress)
        self.root.after(0, update)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = NMH03VideoProV3()
    app.run()
