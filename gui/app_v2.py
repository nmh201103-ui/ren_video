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
from video.segments import VideoSegmenter, ProductSegmenter

logger = get_logger()


class VideoCreatorAppV2:
    """Enhanced app with separate tabs for Product vs Movie"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 NMH03 Video Pro v2")
        self.root.geometry("1400x850")
        self.root.resizable(True, True)
        self.root.configure(bg="#1a1d29")

        self.is_processing = False
        self.video_path = None
        self.status_text = tk.StringVar(value="Ready 🚀")
        self.progress_percent = tk.IntVar(value=0)
        self.person_image_path = None
        self.segments_data = []  # Store detected segments
        
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
                text="🎬 NMH03 Video Pro v2",
                font=("Segoe UI", 22, "bold"),
                fg="#6c63ff",
                bg="#252836").pack(side=tk.LEFT, padx=25, pady=20)
        
        tk.Label(header,
                text="Product • Movie • Auto Segments",
                font=("Segoe UI", 10),
                fg="#9499a8",
                bg="#252836").pack(side=tk.LEFT, padx=5)
        
        # Content area with tabs
        content = tk.Frame(main, bg="#1a1d29")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabs)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.TNotebook', background='#252836', borderwidth=0)
        style.configure('Custom.TNotebook.Tab', 
                       background='#252836', 
                       foreground='#9499a8',
                       padding=[20, 10],
                       font=('Segoe UI', 11, 'bold'))
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', '#6c63ff')],
                 foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(content, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Product Review
        self.product_tab = tk.Frame(self.notebook, bg="#252836")
        self.notebook.add(self.product_tab, text='📦 Product Review')
        
        # Tab 2: Movie Review
        self.movie_tab = tk.Frame(self.notebook, bg="#252836")
        self.notebook.add(self.movie_tab, text='📽️ Movie Review')
        
        # Setup tabs
        self._setup_product_tab()
        self._setup_movie_tab()

    def _setup_product_tab(self):
        """Setup Product Review tab"""
        # Split into left (settings) and right (preview)
        left = tk.Frame(self.product_tab, bg="#252836", width=750)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        
        right = tk.Frame(self.product_tab, bg="#252836", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 10), pady=10)
        
        # LEFT: Settings
        self._add_section(left, "🔗 Product URL (Shopee/TikTok)")
        self.product_url_text = tk.Text(left, height=3, font=("Segoe UI", 10),
                                       bg="#1a1d29", fg="#e4e6eb",
                                       insertbackground="#6c63ff", relief=tk.FLAT)
        self.product_url_text.pack(fill=tk.X, padx=20, pady=(0, 15), ipady=5)
        
        # Video Style
        self._add_section(left, "🎨 Video Style")
        style_frame = tk.Frame(left, bg="#1a1d29")
        style_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.product_mode = tk.StringVar(value="simple")
        for text, value, desc in [
            ("📹 Simple", "simple", "Product + voiceover"),
            ("🎙️ Reviewer", "reviewer", "Talking head + product"),
        ]:
            radio_frame = tk.Frame(style_frame, bg="#1a1d29")
            radio_frame.pack(fill=tk.X, pady=5)
            rb = tk.Radiobutton(radio_frame, text=text, variable=self.product_mode,
                              value=value, font=("Segoe UI", 11, "bold"),
                              bg="#1a1d29", fg="#e4e6eb", selectcolor="#252836")
            rb.pack(side=tk.LEFT, padx=10, pady=8)
            tk.Label(radio_frame, text=desc, font=("Segoe UI", 9),
                    fg="#9499a8", bg="#1a1d29").pack(side=tk.LEFT, padx=5)
        
        # AI Avatar
        self._add_section(left, "🤖 AI Avatar")
        avatar_frame = tk.Frame(left, bg="#1a1d29")
        avatar_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.product_use_avatar = tk.BooleanVar(value=False)
        tk.Checkbutton(avatar_frame, text="Enable Talking Avatar",
                      variable=self.product_use_avatar,
                      font=("Segoe UI", 11, "bold"),
                      bg="#1a1d29", fg="#e4e6eb", selectcolor="#252836").pack(anchor="w", padx=10)
        
        # Upload Image
        upload_btn = tk.Button(left, text="📁 Upload Reviewer Image",
                              font=("Segoe UI", 10, "bold"), bg="#6c63ff", fg="white",
                              relief=tk.FLAT, cursor="hand2",
                              command=self._select_person_image)
        upload_btn.pack(padx=20, pady=(0, 20), ipadx=15, ipady=8)
        
        # RIGHT: Preview & Actions
        gen_btn = tk.Button(right, text="🚀 Generate Product Video",
                           font=("Segoe UI", 16, "bold"), bg="#6c63ff", fg="white",
                           relief=tk.FLAT, cursor="hand2",
                           command=lambda: self._generate_video("product"))
        gen_btn.pack(fill=tk.X, padx=20, pady=20, ipady=18)
        
        self._add_status_widget(right)

    def _setup_movie_tab(self):
        """Setup Movie Review tab"""
        left = tk.Frame(self.movie_tab, bg="#252836", width=750)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        
        right = tk.Frame(self.movie_tab, bg="#252836", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 10), pady=10)
        
        # LEFT: Settings
        self._add_section(left, "🎬 Movie URL or Name")
        url_help = tk.Label(left, 
                           text="Enter: IMDb URL, Wikipedia link, or movie name (e.g., 'Oppenheimer')",
                           font=("Segoe UI", 9), fg="#6c757d", bg="#252836")
        url_help.pack(padx=20, pady=(0, 5))
        
        self.movie_url_text = tk.Text(left, height=3, font=("Segoe UI", 10),
                                     bg="#1a1d29", fg="#e4e6eb",
                                     insertbackground="#6c63ff", relief=tk.FLAT)
        self.movie_url_text.pack(fill=tk.X, padx=20, pady=(0, 15), ipady=5)
        
        # Segment Detection
        self._add_section(left, "✂️ Auto Segment Detection")
        segment_frame = tk.Frame(left, bg="#1a1d29")
        segment_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.enable_segments = tk.BooleanVar(value=True)
        tk.Checkbutton(segment_frame, 
                      text="Auto-detect chapters (intro, plot, highlights, review)",
                      variable=self.enable_segments,
                      font=("Segoe UI", 10),
                      bg="#1a1d29", fg="#e4e6eb", selectcolor="#252836").pack(anchor="w", padx=10)
        
        tk.Label(segment_frame,
                text="✓ Tự động phát hiện các phần trong review để tách video",
                font=("Segoe UI", 9), fg="#6c757d", bg="#1a1d29").pack(anchor="w", padx=30)
        
        # Clip Suggestions
        self._add_section(left, "📹 Clip Suggestions")
        clip_frame = tk.Frame(left, bg="#1a1d29")
        clip_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.suggest_clips = tk.BooleanVar(value=False)
        tk.Checkbutton(clip_frame,
                      text="Suggest short clips (60s) for TikTok/Reels",
                      variable=self.suggest_clips,
                      font=("Segoe UI", 10),
                      bg="#1a1d29", fg="#e4e6eb", selectcolor="#252836").pack(anchor="w", padx=10)
        
        # Segments List (will show detected segments)
        self._add_section(left, "📊 Detected Segments")
        self.segments_listbox = tk.Listbox(left, height=6, font=("Consolas", 9),
                                          bg="#1a1d29", fg="#e4e6eb",
                                          selectbackground="#6c63ff", relief=tk.FLAT)
        self.segments_listbox.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # RIGHT: Preview & Actions
        gen_btn = tk.Button(right, text="🎬 Generate Movie Review",
                           font=("Segoe UI", 16, "bold"), bg="#FF8C00", fg="white",
                           relief=tk.FLAT, cursor="hand2",
                           command=lambda: self._generate_video("movie"))
        gen_btn.pack(fill=tk.X, padx=20, pady=20, ipady=18)
        
        self._add_status_widget(right)

    def _add_status_widget(self, parent):
        """Add status and progress widgets"""
        status_card = tk.Frame(parent, bg="#1a1d29")
        status_card.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        tk.Label(status_card, text="📊 Status", font=("Segoe UI", 12, "bold"),
                fg="#e4e6eb", bg="#1a1d29").pack(anchor="w", padx=15, pady=(15, 5))
        
        self.status_label = tk.Label(status_card, textvariable=self.status_text,
                                     font=("Segoe UI", 10), fg="#9499a8", bg="#1a1d29",
                                     wraplength=450, justify=tk.LEFT)
        self.status_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        progress_style = ttk.Style()
        progress_style.configure("Custom.Horizontal.TProgressbar",
                                troughcolor="#252836", background="#6c63ff", thickness=25)
        
        self.progress_bar = ttk.Progressbar(status_card, variable=self.progress_percent,
                                           maximum=100, style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=15, pady=(0, 15))

    def _add_section(self, parent, title):
        """Add section header"""
        tk.Label(parent, text=title, font=("Segoe UI", 13, "bold"),
                fg="#e4e6eb", bg="#252836").pack(anchor="w", padx=20, pady=(15, 10))

    def _select_person_image(self):
        """Upload reviewer image"""
        path = filedialog.askopenfilename(
            title="Select Reviewer Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )
        if path:
            self.person_image_path = path
            self.status_text.set(f"✅ Loaded: {os.path.basename(path)}")

    def _generate_video(self, content_type):
        """Start video generation"""
        if self.is_processing:
            return
        
        # Get URL from appropriate tab
        if content_type == "product":
            url = self.product_url_text.get("1.0", tk.END).strip()
        else:
            url = self.movie_url_text.get("1.0", tk.END).strip()
        
        if not url:
            messagebox.showwarning("Missing Input", 
                                  f"Please enter a {content_type} URL or name")
            return
        
        self.is_processing = True
        self.progress_percent.set(0)
        self.status_text.set("🚀 Starting...")
        
        thread = threading.Thread(target=self._create_video_worker, 
                                 args=(url, content_type))
        thread.daemon = True
        thread.start()

    def _create_video_worker(self, url, content_type):
        """Background video creation"""
        try:
            msg = "📽️ Scraping movie..." if content_type == "movie" else "📥 Scraping product..."
            self._ui(msg, 10)
            
            scraper = get_scraper(url)
            if not scraper:
                raise ValueError("Unsupported platform")
            
            product_data = scraper.scrape(url)
            
            if not product_data or not product_data.get("title"):
                raise ValueError("Failed to scrape data")
            
            self._ui("🔄 Processing content...", 30)
            
            processor = ContentProcessor()
            processed = processor.process(product_data)
            
            if not processed.get("description"):
                processed["description"] = product_data["description"]
            
            self._ui("📝 Generating script...", 40)
            
            # Get settings based on tab
            if content_type == "product":
                video_mode = self.product_mode.get()
                use_ai_avatar = self.product_use_avatar.get()
            else:
                video_mode = "simple"
                use_ai_avatar = False
            
            processed["person_image_path"] = self.person_image_path
            
            # Initialize renderer
            renderer = SmartVideoRenderer(
                video_mode=video_mode,
                use_ai_avatar=use_ai_avatar,
                avatar_backend="wav2lip",
                content_type=content_type
            )
            
            # Generate script
            title = processed.get("title", "")
            desc = processed.get("description", "")
            price = processed.get("price", "")
            script = renderer.script_gen.generate(title, desc, price)
            
            # SEGMENT DETECTION
            if content_type == "movie" and self.enable_segments.get():
                self._ui("✂️ Detecting segments...", 45)
                segmenter = VideoSegmenter()
                segments = segmenter.detect_segments(script)
                self.segments_data = segments
                
                # Update segments listbox
                self.root.after(0, lambda: self._update_segments_display(segments))
                
                # Optional: suggest clips
                if self.suggest_clips.get():
                    clips = segmenter.suggest_clips(segments, target_duration=60)
                    logger.info(f"💡 Clip suggestions: {[c['title'] for c in clips]}")
            
            self._ui("🎬 Rendering video...", 50)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/videos/{content_type}_{timestamp}.mp4"
            
            success = renderer.render(
                processed,
                output_path,
                max_images=5,
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
            self._ui(f"❌ Error: {str(e)}", 0)
            self.root.after(100, lambda: messagebox.showerror(
                "Error",
                f"Failed: {str(e)}"
            ))
        finally:
            self.is_processing = False

    def _update_segments_display(self, segments):
        """Update segments listbox with detected segments"""
        self.segments_listbox.delete(0, tk.END)
        for i, seg in enumerate(segments):
            seg_type = seg['type'].upper()
            duration = seg['duration_estimate']
            num_sentences = len(seg['sentences'])
            self.segments_listbox.insert(tk.END, 
                f"{i+1}. [{seg_type}] {num_sentences} câu (~{duration:.1f}s)")

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
    app = VideoCreatorAppV2()
    app.run()
