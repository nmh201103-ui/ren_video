"""Movie Review Tab - Movie/Story review video creator"""
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from threading import Thread
from datetime import datetime
import math
import os

from utils.helpers import get_scraper, ensure_directory
from utils.logger import get_logger
from processor.content import ContentProcessor
from video.render import SmartVideoRenderer
from video.segments import VideoSegmenter

logger = get_logger()


class MovieReviewTab:
    """Tab for creating movie/story review videos"""
    
    def __init__(self, parent_frame, status_callback):
        self.parent = parent_frame
        self.status_callback = status_callback
        self.is_processing = False
        self.video_path = None
        self.segments_data = []
        self.progress_var = tk.IntVar(value=0)
        
        left = tk.Frame(parent_frame, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(parent_frame, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # LEFT - Scrollable settings
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
        
        # Content Type
        self._add_card(scrollable, "📚 Content Type", "Choose what to create")
        content_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        content_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.movie_content_type = tk.StringVar(value='movie')
        for ctype, label, desc in [
            ('movie', '🎬 Movie Review', 'IMDb, Wikipedia movie'),
            ('story', '📖 Web Story/Article', 'Blog, news, any webpage'),
            ('video', '🎥 Video Film (NEW!)', 'Upload .mp4 film + AI analysis')
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
        
        # Movie/Video Input
        self._add_card(scrollable, "🎬 Movie Source", "IMDb, Wikipedia, video URL, or upload .mp4")
        
        # URL Input Frame
        self.movie_url_frame = tk.Frame(scrollable, bg="#0d1117")
        self.movie_url_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        url_label = tk.Label(self.movie_url_frame,
                            text="IMDb/Wikipedia URL or Video Link:",
                            font=("Segoe UI", 9),
                            fg="#8b949e", bg="#0d1117")
        url_label.pack(padx=5, pady=(0, 5), anchor="w")
        
        self.movie_url = tk.Text(self.movie_url_frame, height=2, font=("Consolas", 10),
                                bg="#21262d", fg="#c9d1d9", insertbackground="#58a6ff",
                                relief=tk.FLAT, wrap=tk.WORD, padx=10, pady=10)
        self.movie_url.pack(fill=tk.X, pady=(0, 5))
        
        help_text = tk.Label(self.movie_url_frame,
                            text="Examples: 'https://imdb.com/title/tt123', 'Oppenheimer', 'https://youtube.com/watch?v=...', 'https://vimeo.com/...'",
                            font=("Segoe UI", 8),
                            fg="#8b949e", bg="#0d1117", wraplength=400, justify=tk.LEFT)
        help_text.pack(padx=5, pady=(5, 0), anchor="w")
        
        # Film Upload Frame (hidden by default)
        self.movie_file_frame = tk.Frame(scrollable, bg="#0d1117")
        
        file_help = tk.Label(self.movie_file_frame,
                            text="Upload MP4 video file for AI scene analysis",
                            font=("Segoe UI", 9),
                            fg="#8b949e", bg="#0d1117")
        file_help.pack(padx=5, pady=(0, 5), anchor="w")
        
        file_btn_frame = tk.Frame(self.movie_file_frame, bg="#21262d", padx=15, pady=15)
        file_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.movie_file_path = tk.StringVar(value="")
        tk.Button(file_btn_frame,
                 text="📁 Upload Film (MP4)",
                 font=("Segoe UI", 11, "bold"),
                 bg="#238636", fg="#ffffff",
                 activebackground="#2ea043",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._browse_film_file).pack(side=tk.LEFT, padx=5, ipadx=20, ipady=10)
        
        self.movie_file_label = tk.Label(file_btn_frame,
                                        text="No file selected",
                                        font=("Segoe UI", 10),
                                        fg="#8b949e", bg="#21262d")
        self.movie_file_label.pack(side=tk.LEFT, padx=15)
        
        # Video Duration Slider
        self._add_card(scrollable, "⏱️ Video Duration", "Drag to set video length")
        slider_frame = tk.Frame(scrollable, bg="#21262d", padx=20, pady=15)
        slider_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        duration_label_frame = tk.Frame(slider_frame, bg="#21262d")
        duration_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(duration_label_frame, text="Duration:", font=("Segoe UI", 10, "bold"),
                 fg="#c9d1d9", bg="#21262d").pack(side=tk.LEFT)
        
        self.movie_duration_var = tk.IntVar(value=60)
        self.movie_duration_label = tk.Label(duration_label_frame, 
                                             text="1m", 
                                             font=("Segoe UI", 12, "bold"),
                                             fg="#58a6ff", bg="#21262d")
        self.movie_duration_label.pack(side=tk.LEFT, padx=10)
        
        # Slider container
        slider_container = tk.Frame(slider_frame, bg="#21262d")
        slider_container.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(slider_container, text="10s", font=("Segoe UI", 9),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        self.movie_duration_slider = tk.Scale(slider_container,
                                             from_=10, to=7200,
                                             orient=tk.HORIZONTAL,
                                             variable=self.movie_duration_var,
                                             font=("Segoe UI", 10),
                                             bg="#161b22", fg="#c9d1d9",
                                             highlightthickness=0,
                                             troughcolor="#0d1117",
                                             activebackground="#58a6ff",
                                             command=self._update_movie_duration_label,
                                             showvalue=0)
        self.movie_duration_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        tk.Label(slider_container, text="2h", font=("Segoe UI", 9),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        # Quick presets
        preset_frame = tk.Frame(slider_frame, bg="#21262d")
        preset_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(preset_frame, text="💡 Quick:", font=("Segoe UI", 9),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        for label, seconds in [("30s", 30), ("1m", 60), ("2m", 120), ("5m", 300), ("10m", 600), ("30m", 1800)]:
            tk.Button(preset_frame, text=label,
                     font=("Segoe UI", 9),
                     bg="#238636", fg="#ffffff",
                     relief=tk.FLAT, cursor="hand2",
                     command=lambda s=seconds: self.movie_duration_var.set(s),
                     padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        
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
        
        # RIGHT - Status & Generate button
        btn_frame = tk.Frame(right, bg="#21262d", padx=25, pady=25)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame,
                 text="🎬 Generate Movie Review",
                 font=("Segoe UI", 16, "bold"),
                 bg="#da3633", fg="#ffffff",
                 activebackground="#b62324",
                 relief=tk.FLAT, cursor="hand2",
                 command=self._generate).pack(fill=tk.X, ipady=20)
        
        self._add_status_panel(right)
        self._add_tips_panel(right, [
            "✂️ Auto-detects Intro/Plot/Review",
            "📤 Export segments separately",
            "📋 Copy timestamps for YouTube"
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
    
    def _toggle_movie_input_type(self):
        """Toggle between Movie, Story, and Video input"""
        content_type = self.movie_content_type.get()
        
        # All types use URL input field - no need to toggle help text
        # Video mode accepts video URLs, Movie accepts IMDb, Story accepts article URLs
        if content_type == 'video':
            # Video mode: URL input visible (for video URLs or upload)
            self.movie_file_frame.pack_forget()
            self.movie_url_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        else:
            # Movie/Story mode: URL input visible
            self.movie_file_frame.pack_forget()
            self.movie_url_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            self.movie_url_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
    
    def _browse_film_file(self):
        """Browse for film file"""
        path = filedialog.askopenfilename(
            title="Select Film File",
            filetypes=[
                ("Video files", "*.mp4 *.mkv *.avi *.mov"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.movie_file_path.set(path)
            filename = os.path.basename(path)
            self.movie_file_label.config(
                text=f"✓ {filename[:30]}..." if len(filename) > 30 else f"✓ {filename}",
                fg="#3fb950"
            )
    
    def _update_movie_duration_label(self, value):
        """Update duration label with h:m:s format"""
        seconds = int(float(value))
        
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if minutes > 0 or secs > 0:
                self.movie_duration_label.config(text=f"{hours}h {minutes}m {secs}s")
            else:
                self.movie_duration_label.config(text=f"{hours}h")
        elif seconds >= 60:
            minutes = seconds // 60
            secs = seconds % 60
            if secs > 0:
                self.movie_duration_label.config(text=f"{minutes}m {secs}s")
            else:
                self.movie_duration_label.config(text=f"{minutes}m")
        else:
            self.movie_duration_label.config(text=f"{seconds}s")
    
    def _display_segments(self, segments):
        """Display detected segments in text widget"""
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
    
    def _copy_timestamps(self):
        """Copy timestamps to clipboard"""
        if not self.segments_data:
            messagebox.showwarning("No Segments", "Generate a movie review first")
            return
        
        text = self.segments_text.get("1.0", tk.END)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(text)
        messagebox.showinfo("Copied", "Timestamps copied to clipboard!")
    
    def _generate(self):
        """Start video generation"""
        if self.is_processing:
            return
        
        content_type = self.movie_content_type.get()
        
        # Validate input based on type
        if content_type == 'video':
            # Check URL first, then file path
            url_input = self.movie_url.get("1.0", tk.END).strip()
            file_path = self.movie_file_path.get()
            
            if url_input:
                # URL provided - use it
                video_path = url_input
            elif file_path and os.path.exists(file_path):
                # Local file provided - use it
                video_path = file_path
            else:
                messagebox.showwarning("Missing Film", "Please enter video URL or upload .mp4 file")
                return
        else:
            url = self.movie_url.get("1.0", tk.END).strip()
            if not url:
                messagebox.showwarning("Missing Input", "Please enter movie URL or name")
                return
            video_path = url
        
        self.is_processing = True
        self.progress_var.set(0)
        Thread(target=self._generate_worker, args=(video_path, content_type), daemon=True).start()
    
    def _generate_worker(self, source, content_type):
        """Background worker for video generation"""
        downloaded_video = None  # Track if we downloaded a video for cleanup
        try:
            self._ui("🔄 Starting...", 5)
            
            actual_type = content_type
            target_duration = self.movie_duration_var.get()
            avg_per_scene = 15
            num_scenes = max(3, min(12, math.ceil(target_duration / avg_per_scene)))
            
            # Handle video film with scene analysis
            if actual_type == "video":
                # Check if source is URL or file path
                if source.startswith("http://") or source.startswith("https://"):
                    # Download video from URL
                    self._ui("📥 Downloading video from URL...", 10)
                    from utils.video_downloader import VideoURLDownloader
                    downloader = VideoURLDownloader()
                    try:
                        downloaded_video = downloader.download(source, max_duration=3600)
                        video_file = downloaded_video
                        logger.info(f"✅ Video downloaded to: {video_file}")
                    except Exception as e:
                        raise ValueError(f"Failed to download video: {str(e)}")
                else:
                    # Local file path
                    video_file = source
                
                self._ui("📹 Analyzing film...", 15)
                
                from video.scene_detector import SceneDetector
                from video.scene_analyzer import SceneAnalyzer
                
                # Detect scenes
                detector = SceneDetector()
                scenes = detector.detect_scenes(video_file, max_scenes=num_scenes)
                
                if not scenes:
                    raise ValueError("No scenes detected in video")
                
                # Extract scene frames
                self._ui("🎬 Extracting scene frames...", 20)
                detector.extract_scene_frames(video_file, scenes)
                
                # Analyze scenes with AI
                self._ui("🧠 AI analyzing scenes...", 40)
                analyzer = SceneAnalyzer()
                scenes = analyzer.analyze_scenes(scenes)
                
                # Generate review script from scenes
                self._ui("📝 Generating review script...", 60)
                script = analyzer.generate_review_script(scenes, video_file)
                
                # Create processed data for renderer
                processed = {
                    'title': os.path.splitext(os.path.basename(video_file))[0],
                    'description': script,
                    'content': '',
                    'image_urls': [s.get('frame_path', '') for s in scenes if 'frame_path' in s],
                    'script': [{'text': s.get('analysis', {}).get('review_script', ''), 'duration': s.get('duration', target_duration / num_scenes)} for s in scenes],
                    'video_path': video_file,
                    'scenes': scenes
                }
            
            else:
                # Original logic for IMDb/Web scraping
                self._ui(f"📥 Fetching {actual_type} data...", 10)
                
                if actual_type == "story":
                    try:
                        import sys
                        sys.path.insert(0, 'scraper')
                        from web_story import WebStoryCScraper
                        scraper = WebStoryCScraper()
                    except ImportError as e:
                        raise ValueError(f"Web story scraper not found: {e}")
                else:
                    scraper = get_scraper(source)
                    if not scraper:
                        raise ValueError("Unsupported platform")
                
                data = scraper.scrape(source)
                if not data.get("title"):
                    raise ValueError("Failed to fetch data")
            
            self._ui("🔄 Processing content...", 30)
            
            if actual_type != "video":
                if actual_type == "story":
                    processed = {
                        'title': data.get('title', 'Story'),
                        'description': data.get('description', ''),
                        'content': data.get('content', ''),
                        'image_urls': data.get('image_urls', [])
                    }
                    logger.info(f"📸 Story processing: {len(processed.get('image_urls', []))} images available")
                else:
                    processor = ContentProcessor()
                    processed = processor.process(data)
            
            # Create renderer
            renderer = SmartVideoRenderer(
                video_mode="simple",
                use_ai_avatar=False,
                avatar_backend="wav2lip",
                content_type="movie" if actual_type != "video" else "video"
            )
            
            # Skip script generation for video type (already done)
            if actual_type != "video":
                self._ui(f"📝 Generating {actual_type} script ({target_duration}s)...", 40)
            
                if actual_type == "story":
                    from video.story_generator import StoryScriptGenerator
                    # Try Gemma 3.4B model (better quality than 2B)
                    # If still generates trash, change to: StoryScriptGenerator(use_llm=None)
                    story_gen = StoryScriptGenerator()  # Auto-detect: will use Ollama gemma3:4b
                    script = story_gen.generate(
                        processed['title'],
                        processed.get('description', ''),
                        processed.get('content', ''),
                        max_scenes=num_scenes,
                        target_duration=target_duration
                    )
                else:
                    script = renderer.script_gen.generate(
                        processed['title'],
                        processed['description'],
                        processed.get('price', '')
                    )
                
                # ✅ AUTO-DOWNLOAD ĐỦ ẢNH TRƯỚC KHI EXPAND SCRIPT
                # Với story mode, bỏ toàn bộ ảnh cũ (scraper tải sẵn) để tránh lệch thứ tự scene
                # Đảm bảo mỗi scene có 1 ảnh (dùng text gốc, chưa có elaboration)
                current_images = [] if actual_type == "story" else processed.get('image_urls', [])
                if len(current_images) < len(script):
                    logger.info(f"🔍 Pre-downloading images: {len(current_images)} → {len(script)} scenes")
                    from video.image_searcher import ImageSearcher
                    searcher = ImageSearcher()
                    for scene_idx in range(len(current_images) + 1, len(script) + 1):
                        scene_text = script[scene_idx - 1]
                        query = " ".join(scene_text.split()[:15])  # Use original scene text
                        paths = searcher.search_google_images(query, num_images=1, output_dir="assets/temp/web_story_images", index=scene_idx)
                        if paths:
                            current_images.extend(paths)
                            logger.info(f"✅ Scene {scene_idx}: Downloaded image")
                        else:
                            # Fallback placeholder
                            placeholder = [f"https://picsum.photos/1080/1920?random={scene_idx}"]
                            paths = searcher._download_batch(placeholder, "assets/temp/web_story_images", scene_idx)
                            if paths:
                                current_images.extend(paths)
                    processed['image_urls'] = current_images
                    # Lock images so renderer won't auto-download again (avoid mismatch)
                    processed['images_locked'] = True
                    logger.info(f"✅ Images ready: {len(current_images)} for {len(script)} scenes")
                
                # Optimize script duration (expand/compress)
                from video.script_optimizer import ScriptDurationOptimizer
                optimizer = ScriptDurationOptimizer()
                script = optimizer.optimize(script[:num_scenes], target_duration)
                logger.info(f"✅ GUI: Final script after optimization ({len(script)} scenes)")
                for i, s in enumerate(script[:10], 1):
                    logger.info(f"   [{i}] {s[:80]}...")
                processed["script"] = script
            else:
                # For video type, script already generated in scene analysis
                self._ui("📺 Preparing video segments...", 65)
            
            # Segment detection
            if "movie" in actual_type and self.enable_segments.get():
                self._ui("✂️ Detecting segments...", 45)
                segmenter = VideoSegmenter()
                segments = segmenter.detect_segments(script)
                self.segments_data = segments
                self.parent.after(0, lambda: self._display_segments(segments))
                
                if self.suggest_clips.get():
                    clips = segmenter.suggest_clips(segments, 60)
                    logger.info(f"💡 Suggested {len(clips)} clips")
            
            # Render
            self._ui(f"🎬 Rendering video ({target_duration}s)...", 50)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/videos/movie_{actual_type}_{timestamp}.mp4"
            
            script_items = processed.get("script", [])
            success = renderer.render(
                processed,
                output_path,
                max_images=len(script_items),
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
            # Cleanup downloaded video if any
            if downloaded_video:
                try:
                    from utils.video_downloader import VideoURLDownloader
                    downloader = VideoURLDownloader()
                    downloader.cleanup(downloaded_video)
                except Exception as e:
                    logger.warning(f"Failed to cleanup downloaded video: {e}")
            
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
