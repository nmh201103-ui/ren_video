import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os
from datetime import datetime
from utils.helpers import get_scraper, ensure_directory
from utils.logger import get_logger
from processor.content import ContentProcessor
from video.render import SmartVideoRenderer

logger = get_logger()


class VideoCreatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 NMH03 Video Pro")
        self.root.geometry("1300x800")
        self.root.resizable(True, True)
        self.root.configure(bg="#1a1d29")

        self.is_processing = False
        self.video_path = None
        self.status_text = tk.StringVar(value="Ready 🚀")
        self.progress_percent = tk.IntVar(value=0)
        self.thumbnail_img = None
        self.video_mode = tk.StringVar(value="reviewer")
        self.content_type = tk.StringVar(value="product")  # "product" or "movie"
        self.person_image_path = None
        
        self._setup_ui()
        ensure_directory("output/videos")

    def _setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg="#1a1d29")
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header = tk.Frame(main, bg="#252836", height=80)
        header.pack(fill=tk.X, pady=(0, 15))
        header.pack_propagate(False)
        
        tk.Label(header,
                text="🎬 NMH03 Video Pro",
                font=("Segoe UI", 22, "bold"),
                fg="#6c63ff",
                bg="#252836").pack(side=tk.LEFT, padx=25, pady=20)
        
        tk.Label(header,
                text="TikTok • Shorts • Reels",
                font=("Segoe UI", 10),
                fg="#9499a8",
                bg="#252836").pack(side=tk.LEFT, padx=5)
        
        # Content area
        content = tk.Frame(main, bg="#1a1d29")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel
        left = tk.Frame(content, bg="#252836", width=750)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left.pack_propagate(False)
        
        # Right panel
        right = tk.Frame(content, bg="#252836", width=500)
        right.pack(side=tk.RIGHT, fill=tk.BOTH)
        right.pack_propagate(False)
        
        # === LEFT: SETTINGS ===
        settings_scroll = tk.Canvas(left, bg="#252836", highlightthickness=0)
        settings_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=settings_scroll.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        settings_scroll.configure(yscrollcommand=scrollbar.set)
        
        settings_inner = tk.Frame(settings_scroll, bg="#252836")
        settings_scroll.create_window((0, 0), window=settings_inner, anchor="nw")
        
        # Store reference for scrolling
        self.settings_scroll = settings_scroll
        self.left_panel = left
        
        # Smooth mousewheel scrolling - works when mouse is over left panel
        def _on_mousewheel(event):
            self.settings_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mousewheel to left panel and all its children
        def _bind_to_mousewheel(widget):
            """Recursively bind mousewheel to widget and its children"""
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_to_mousewheel(child)
        
        # Bind to left panel (settings area)
        _bind_to_mousewheel(left)
        
        # Quick Actions
        self._add_section(settings_inner, "⚡ Quick Presets")
        quick_frame = tk.Frame(settings_inner, bg="#252836")
        quick_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        presets = [
            ("📦 Unboxing", "reviewer", True, "#6c63ff", "product"),
            ("⭐ Review", "reviewer", True, "#ff6584", "product"),
            ("📹 Simple", "simple", False, "#4CAF50", "product"),
            ("📽️ Movie", "simple", False, "#FF8C00", "movie"),  # NEW: Movie Review
        ]
        
        for text, mode, avatar, color, ctype in presets:
            btn = tk.Button(quick_frame,
                          text=text,
                          font=("Segoe UI", 10, "bold"),
                          bg=color,
                          fg="white",
                          activebackground=color,
                          relief=tk.FLAT,
                          cursor="hand2",
                          command=lambda m=mode, a=avatar, ct=ctype: self._apply_preset(m, a, ct))
            btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=15, ipady=10)
        
        # URL Input
        self._add_section(settings_inner, "🔗 Movie/Product URL")
        url_frame = tk.Frame(settings_inner, bg="#252836")
        url_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.url_text = tk.Text(url_frame,
                               height=3,
                               font=("Segoe UI", 10),
                               bg="#1a1d29",
                               fg="#e4e6eb",
                               insertbackground="#6c63ff",
                               relief=tk.FLAT,
                               wrap=tk.WORD)
        self.url_text.pack(fill=tk.X, ipady=5)
        
        # Video Style
        self._add_section(settings_inner, "🎨 Video Style")
        style_frame = tk.Frame(settings_inner, bg="#252836")
        style_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        styles = [
            ("📹 Simple", "simple", "Product + voiceover"),
            ("🎙️ Reviewer", "reviewer", "Talking head + product"),
        ]
        
        for text, value, desc in styles:
            radio_frame = tk.Frame(style_frame, bg="#1a1d29")
            radio_frame.pack(fill=tk.X, pady=5)
            
            rb = tk.Radiobutton(radio_frame,
                              text=text,
                              variable=self.video_mode,
                              value=value,
                              font=("Segoe UI", 11, "bold"),
                              bg="#1a1d29",
                              fg="#e4e6eb",
                              selectcolor="#252836",
                              activebackground="#1a1d29",
                              cursor="hand2")
            rb.pack(side=tk.LEFT, padx=10, pady=8)
            
            tk.Label(radio_frame,
                    text=desc,
                    font=("Segoe UI", 9),
                    fg="#9499a8",
                    bg="#1a1d29").pack(side=tk.LEFT, padx=5)
        
        # AI Avatar Settings
        self._add_section(settings_inner, "🤖 AI Avatar")
        avatar_frame = tk.Frame(settings_inner, bg="#252836")
        avatar_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        enable_frame = tk.Frame(avatar_frame, bg="#1a1d29")
        enable_frame.pack(fill=tk.X, pady=5)
        
        self.use_ai_avatar = tk.BooleanVar(value=True)
        ai_check = tk.Checkbutton(enable_frame,
                                 text="Enable Talking Avatar",
                                 variable=self.use_ai_avatar,
                                 font=("Segoe UI", 11, "bold"),
                                 bg="#1a1d29",
                                 fg="#e4e6eb",
                                 selectcolor="#252836",
                                 activebackground="#1a1d29",
                                 cursor="hand2")
        ai_check.pack(side=tk.LEFT, padx=10, pady=8)
        
        # Backend selection
        backend_frame = tk.Frame(avatar_frame, bg="#1a1d29")
        backend_frame.pack(fill=tk.X, padx=30, pady=(5, 0))
        
        self.avatar_backend = tk.StringVar(value="wav2lip")
        
        backends = [
            ("⚡ Wav2Lip", "wav2lip", "Fast & Free"),
            ("💎 D-ID", "did", "Premium Quality"),
        ]
        
        for text, value, desc in backends:
            back_row = tk.Frame(backend_frame, bg="#1a1d29")
            back_row.pack(fill=tk.X, pady=3)
            
            rb = tk.Radiobutton(back_row,
                              text=text,
                              variable=self.avatar_backend,
                              value=value,
                              font=("Segoe UI", 10),
                              bg="#1a1d29",
                              fg="#9499a8",
                              selectcolor="#252836",
                              cursor="hand2")
            rb.pack(side=tk.LEFT)
            
            tk.Label(back_row,
                    text=f"• {desc}",
                    font=("Segoe UI", 8),
                    fg="#6c757d",
                    bg="#1a1d29").pack(side=tk.LEFT, padx=5)
        
        # Upload Image
        self._add_section(settings_inner, "👤 Reviewer Image")
        upload_frame = tk.Frame(settings_inner, bg="#252836")
        upload_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        upload_inner = tk.Frame(upload_frame, bg="#1a1d29")
        upload_inner.pack(fill=tk.X, pady=5)
        
        self.upload_btn = tk.Button(upload_inner,
                                    text="📁 Choose Image",
                                    font=("Segoe UI", 10, "bold"),
                                    bg="#6c63ff",
                                    fg="white",
                                    activebackground="#5a52d5",
                                    relief=tk.FLAT,
                                    cursor="hand2",
                                    command=self._select_person_image)
        self.upload_btn.pack(side=tk.LEFT, padx=10, pady=8, ipadx=15, ipady=8)
        
        self.image_label = tk.Label(upload_inner,
                                    text="No image selected",
                                    font=("Segoe UI", 9),
                                    fg="#6c757d",
                                    bg="#1a1d29")
        self.image_label.pack(side=tk.LEFT, padx=10)
        
        # Update scroll region
        settings_inner.update_idletasks()
        settings_scroll.configure(scrollregion=settings_scroll.bbox("all"))
        
        # Re-bind mousewheel after all widgets are created
        def _on_mousewheel(event):
            self.settings_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_to_mousewheel(child)
        
        _bind_to_mousewheel(self.left_panel)
        
        # === RIGHT: ACTIONS & PREVIEW ===
        # Generate Button
        gen_frame = tk.Frame(right, bg="#252836")
        gen_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.generate_btn = tk.Button(gen_frame,
                                     text="🚀 Generate Video",
                                     font=("Segoe UI", 16, "bold"),
                                     bg="#6c63ff",
                                     fg="white",
                                     activebackground="#5a52d5",
                                     relief=tk.FLAT,
                                     cursor="hand2",
                                     command=self._generate_video)
        self.generate_btn.pack(fill=tk.X, ipady=18)
        
        # Status
        status_card = tk.Frame(right, bg="#1a1d29")
        status_card.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        tk.Label(status_card,
                text="📊 Status",
                font=("Segoe UI", 12, "bold"),
                fg="#e4e6eb",
                bg="#1a1d29").pack(anchor="w", padx=15, pady=(15, 5))
        
        self.status_label = tk.Label(status_card,
                                     textvariable=self.status_text,
                                     font=("Segoe UI", 10),
                                     fg="#9499a8",
                                     bg="#1a1d29",
                                     wraplength=400,
                                     justify=tk.LEFT)
        self.status_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Progress bar
        progress_style = ttk.Style()
        progress_style.configure("Custom.Horizontal.TProgressbar",
                                troughcolor="#252836",
                                background="#6c63ff",
                                thickness=25)
        
        self.progress_bar = ttk.Progressbar(status_card,
                                           variable=self.progress_percent,
                                           maximum=100,
                                           style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Preview
        preview_card = tk.Frame(right, bg="#1a1d29")
        preview_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tk.Label(preview_card,
                text="📺 Preview",
                font=("Segoe UI", 12, "bold"),
                fg="#e4e6eb",
                bg="#1a1d29").pack(anchor="w", padx=15, pady=(15, 10))
        
        self.preview_canvas = tk.Canvas(preview_card,
                                       width=400,
                                       height=450,
                                       bg="#252836",
                                       highlightthickness=0)
        self.preview_canvas.pack(padx=15, pady=(0, 15))
        
        # Tips
        tips_card = tk.Frame(right, bg="#1a1d29")
        tips_card.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(tips_card,
                text="💡 Pro Tips",
                font=("Segoe UI", 11, "bold"),
                fg="#e4e6eb",
                bg="#1a1d29").pack(anchor="w", padx=15, pady=(15, 8))
        
        tips = [
            "Use Reviewer mode for talking head videos",
            "Upload clear face photos for best results",
            "Wav2Lip is faster, D-ID has higher quality",
        ]
        
        for tip in tips:
            tip_frame = tk.Frame(tips_card, bg="#1a1d29")
            tip_frame.pack(fill=tk.X, padx=15, pady=3)
            
            tk.Label(tip_frame,
                    text="•",
                    font=("Segoe UI", 10),
                    fg="#6c63ff",
                    bg="#1a1d29").pack(side=tk.LEFT, padx=(0, 5))
            
            tk.Label(tip_frame,
                    text=tip,
                    font=("Segoe UI", 9),
                    fg="#9499a8",
                    bg="#1a1d29",
                    wraplength=350,
                    justify=tk.LEFT).pack(side=tk.LEFT)
        
        tk.Frame(tips_card, bg="#1a1d29", height=15).pack()

    def _add_section(self, parent, title):
        """Add section header"""
        frame = tk.Frame(parent, bg="#252836")
        frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(frame,
                text=title,
                font=("Segoe UI", 13, "bold"),
                fg="#e4e6eb",
                bg="#252836").pack(anchor="w")

    def _apply_preset(self, mode, avatar, content_type="product"):
        """Apply quick preset"""
        self.video_mode.set(mode)
        self.use_ai_avatar.set(avatar)
        self.content_type.set(content_type)
        preset_name = f"{mode.title()} ({content_type.title()})"
        self.status_text.set(f"✅ Applied: {preset_name} preset")

    def _select_person_image(self):
        """Upload reviewer image"""
        path = filedialog.askopenfilename(
            title="Select Reviewer Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )
        if path:
            self.person_image_path = path
            filename = os.path.basename(path)
            self.image_label.config(text=f"✓ {filename[:25]}...", fg="#6c63ff")
            self.status_text.set(f"✅ Loaded: {filename}")

    def _generate_video(self):
        """Start video generation"""
        if self.is_processing:
            return
        
        url = self.url_text.get("1.0", tk.END).strip()
        if not url:
            msg = "Please enter a movie URL or product URL"
            messagebox.showwarning("Missing URL", msg)
            return
        
        self.is_processing = True
        self.generate_btn.config(state=tk.DISABLED, bg="#4a4a4a")
        self.progress_percent.set(0)
        self.status_text.set("🚀 Starting...")
        
        thread = threading.Thread(target=self._create_video_worker, args=(url,))
        thread.daemon = True
        thread.start()

    def _create_video_worker(self, url):
        """Background video creation"""
        try:
            content_type = self.content_type.get()
            scrape_msg = "📽️ Scraping movie..." if content_type == "movie" else "📥 Scraping product..."
            self._ui(scrape_msg, 10)
            
            scraper = get_scraper(url)
            if not scraper:
                raise ValueError("Unsupported platform")
            
            product_data = scraper.scrape(url)
            
            if not product_data or not product_data.get("title"):
                raise ValueError("Failed to scrape product")
            
            if not product_data.get("description"):
                raise ValueError("No description found")
            
            self._ui("🔄 Processing content...", 30)
            
            processor = ContentProcessor()
            processed = processor.process(product_data)
            
            if not processed.get("description"):
                processed["description"] = product_data["description"]
            
            self._ui("🎬 Rendering video...", 50)
            
            video_mode = self.video_mode.get()
            use_ai_avatar = self.use_ai_avatar.get()
            avatar_backend = self.avatar_backend.get()
            content_type = self.content_type.get()
            
            processed["person_image_path"] = self.person_image_path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/videos/video_{timestamp}.mp4"
            
            renderer = SmartVideoRenderer(
                video_mode=video_mode,
                use_ai_avatar=use_ai_avatar,
                avatar_backend=avatar_backend,
                content_type=content_type  # Pass content_type to renderer
            )
            
            success = renderer.render(
                processed,
                output_path,
                max_images=None,  # Use ALL available images, don't limit
                progress_callback=lambda msg, pct: self._ui(msg, pct)
            )
            
            if success:
                self.video_path = output_path
                self._ui("✅ Video created!", 100)
                self.root.after(100, lambda: messagebox.showinfo(
                    "Success",
                    f"Video saved:\n{output_path}"
                ))
            else:
                raise Exception("Rendering failed")
                
        except Exception as e:
            logger.exception("Video creation failed")
            error_msg = str(e)  # Capture error message
            self._ui(f"❌ Error: {error_msg}", 0)
            self.root.after(100, lambda msg=error_msg: messagebox.showerror(
                "Error",
                f"Failed: {msg}"
            ))
        finally:
            self.is_processing = False
            self.root.after(100, lambda: self.generate_btn.config(
                state=tk.NORMAL,
                bg="#6c63ff"
            ))

    def _ui(self, message, progress):
        """Update UI from worker thread"""
        def update():
            self.status_text.set(message)
            if progress is not None:
                self.progress_percent.set(progress)
        self.root.after(0, update)

    def run(self):
        """Start app"""
        self.root.mainloop()


if __name__ == "__main__":
    app = VideoCreatorApp()
    app.run()
