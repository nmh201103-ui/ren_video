"""Product Review Tab - Affiliate video creator"""
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
from datetime import datetime
import math
import os

from utils.helpers import ensure_directory
from utils.logger import get_logger
from processor.content import ContentProcessor
from video.render import SmartVideoRenderer

logger = get_logger()


class ProductReviewTab:
    """Tab for creating affiliate product review videos"""
    
    VIDEO_FORMATS = {
        'short': {'name': '⚡ Short (15-30s)', 'duration': 30, 'scenes': 3, 'icon': '⚡'},
        'medium': {'name': '📹 Medium (45-60s)', 'duration': 60, 'scenes': 5, 'icon': '📹'},
        'long': {'name': '🎬 Long (2-5 min)', 'duration': 180, 'scenes': 10, 'icon': '🎬'},
    }
    
    def __init__(self, parent_frame, status_callback, video_formats=None):
        """
        Initialize Product Review Tab
        Args:
            parent_frame: tk.Frame - Parent widget
            status_callback: function - Callback for UI updates (message, progress)
            video_formats: dict - Video format definitions
        """
        self.parent = parent_frame
        self.status_callback = status_callback
        self.is_processing = False
        self.video_path = None
        self.person_image_path = None
        
        if video_formats:
            self.VIDEO_FORMATS = video_formats
        
        self._setup_ui()
        ensure_directory("output/videos")
    
    def _setup_ui(self):
        """Build the Product Review tab UI"""
        container = tk.Frame(self.parent, bg="#161b22")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left = tk.Frame(container, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(container, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # === LEFT PANEL ===
        from tkinter import ttk
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
                 command=self._select_image).pack(pady=(10, 0), ipadx=20, ipady=8)
        
        # === RIGHT PANEL ===
        btn_frame = tk.Frame(right, bg="#21262d", padx=25, pady=25)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame,
                 text="🚀 Generate Product Video",
                 font=("Segoe UI", 16, "bold"),
                 bg="#1f6feb", fg="#ffffff",
                 activebackground="#1158c7",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._generate).pack(fill=tk.X, ipady=20)
        
        self._add_status_panel(right)
        self._add_tips_panel(right, [
            "⚡ Short: Best for TikTok/Reels (viral)",
            "📹 Medium: Instagram/YouTube Shorts",
            "🎬 Long: Full review for YouTube"
        ])
    
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
        """Add status display panel"""
        from tkinter import ttk
        
        status_card = tk.Frame(parent, bg="#21262d", padx=20, pady=20)
        status_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(status_card, text="📊 Status", font=("Segoe UI", 13, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(anchor="w", pady=(0, 10))
        
        self.status_label = tk.Label(status_card, text="Ready 🚀",
                                     font=("Segoe UI", 10), fg="#8b949e", bg="#21262d",
                                     wraplength=500, justify=tk.LEFT)
        self.status_label.pack(anchor="w", pady=(0, 15))
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(status_card, variable=self.progress_var,
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
    
    def _select_image(self):
        """Upload face image for avatar"""
        path = filedialog.askopenfilename(
            title="Select Face Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )
        if path:
            self.person_image_path = path
            self.status_label.config(text=f"✅ Image loaded: {os.path.basename(path)}")
    
    def _generate(self):
        """Start video generation"""
        if self.is_processing:
            return
        
        url = self.product_url.get("1.0", tk.END).strip()
        if not url:
            messagebox.showwarning("Missing Input", "Please enter product URL")
            return
        
        self.is_processing = True
        self.progress_var.set(0)
        Thread(target=self._generate_worker, args=(url,), daemon=True).start()
    
    def _generate_worker(self, url):
        """Background worker for video generation"""
        try:
            self._ui("🔄 Starting...", 5)
            
            # Get format info
            format_key = self.product_format.get()
            format_info = self.VIDEO_FORMATS[format_key]
            target_duration = format_info['duration']
            num_scenes = format_info['scenes']
            
            self._ui("📥 Fetching product data...", 10)
            
            from utils.helpers import get_scraper
            scraper = get_scraper(url)
            if not scraper:
                raise ValueError("Unsupported platform")
            
            data = scraper.scrape(url)
            if not data.get("title"):
                raise ValueError("Failed to fetch product data")
            
            self._ui("🔄 Processing content...", 30)
            
            processor = ContentProcessor()
            processed = processor.process(data)
            processed["person_image_path"] = self.person_image_path
            
            # Create renderer
            mode = self.product_mode.get()
            use_avatar = self.product_use_avatar.get()
            
            renderer = SmartVideoRenderer(
                video_mode=mode,
                use_ai_avatar=use_avatar,
                avatar_backend="wav2lip",
                content_type="product"
            )
            
            # Generate script
            self._ui(f"📝 Generating script ({target_duration}s)...", 40)
            script = renderer.script_gen.generate(
                processed['title'],
                processed['description'],
                processed.get('price', '')
            )
            
            processed["script"] = script[:num_scenes]
            
            # Render video
            self._ui(f"🎬 Rendering video ({target_duration}s)...", 50)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/videos/product_{format_key}_{timestamp}.mp4"
            
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
                messagebox.showinfo("Success", f"Video saved:\n{output_path}")
            else:
                raise Exception("Rendering failed")
        
        except Exception as e:
            logger.exception("Generation failed")
            self._ui(f"❌ Error: {str(e)}", 0)
            messagebox.showerror("Error", str(e))
        
        finally:
            self.is_processing = False
    
    def _ui(self, message, progress):
        """Update UI status"""
        def update():
            self.status_label.config(text=message)
            if progress is not None:
                self.progress_var.set(progress)
        
        if hasattr(self.parent, 'after'):
            self.parent.after(0, update)
        else:
            update()
