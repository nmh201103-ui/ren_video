"""Video Clipper Tab - Auto video highlight extraction"""
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from threading import Thread
import os
import time

from utils.logger import get_logger

logger = get_logger()


class VideoClipperTab:
    """Tab for auto-cutting videos into highlights"""
    
    def __init__(self, parent_frame):
        """
        Initialize Video Clipper Tab
        Args:
            parent_frame: tk.Frame - Parent widget
        """
        self.parent = parent_frame
        self.is_processing = False
        self.clipper_file_path = tk.StringVar(value="")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the Video Clipper tab UI"""
        container = tk.Frame(self.parent, bg="#161b22")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left = tk.Frame(container, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(container, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # LEFT - Settings
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
        
        # URL Input
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
        
        # File Browser
        self.clipper_file_frame = tk.Frame(scrollable, bg="#0d1117")
        
        file_help = tk.Label(self.clipper_file_frame,
                            text="Click to browse video files (MP4, AVI, MOV, MKV)",
                            font=("Segoe UI", 9),
                            fg="#8b949e", bg="#0d1117")
        file_help.pack(padx=5, pady=(0, 5), anchor="w")
        
        file_btn_frame = tk.Frame(self.clipper_file_frame, bg="#21262d", padx=15, pady=15)
        file_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
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
        
        self.clip_duration = tk.IntVar(value=30)
        
        duration_display = tk.Frame(format_frame, bg="#21262d")
        duration_display.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(duration_display, text="⏱️ Clip Duration:", 
                font=("Segoe UI", 11, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        self.duration_label = tk.Label(duration_display, text="30s", 
                                       font=("Segoe UI", 12, "bold"),
                                       fg="#58a6ff", bg="#21262d")
        self.duration_label.pack(side=tk.LEFT, padx=10)
        
        # Slider
        slider_frame = tk.Frame(format_frame, bg="#21262d")
        slider_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(slider_frame, text="10s", font=("Segoe UI", 9),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        duration_slider = tk.Scale(slider_frame, from_=10, to=7200,
                                  variable=self.clip_duration,
                                  orient=tk.HORIZONTAL,
                                  font=("Segoe UI", 9),
                                  bg="#161b22", fg="#c9d1d9",
                                  troughcolor="#0d1117",
                                  highlightthickness=0,
                                  showvalue=0,
                                  command=self._update_duration_label)
        duration_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        tk.Label(slider_frame, text="2h", font=("Segoe UI", 9),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        # Quick duration presets
        suggestion_frame = tk.Frame(format_frame, bg="#21262d")
        suggestion_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(suggestion_frame, text="💡 Quick:", font=("Segoe UI", 9),
                fg="#8b949e", bg="#21262d").pack(side=tk.LEFT, padx=5)
        
        for duration, label in [(15, "15s"), (30, "30s"), (60, "1m"), (120, "2m"), (300, "5m"), (600, "10m")]:
            btn = tk.Button(suggestion_frame, text=label,
                          font=("Segoe UI", 9),
                          bg="#238636", fg="white",
                          relief=tk.FLAT, padx=10, pady=3,
                          cursor="hand2",
                          command=lambda d=duration: self._set_duration(d))
            btn.pack(side=tk.LEFT, padx=3)
        
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
        
        # Detected Highlights
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
        
        # RIGHT - Status & Generate button
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
    
    def _toggle_clipper_source(self):
        """Toggle between URL and file input"""
        source_type = self.clipper_source_type.get()
        
        if source_type == 'url':
            self.clipper_file_frame.pack_forget()
            self.clipper_url_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        else:
            self.clipper_url_frame.pack_forget()
            self.clipper_file_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
    
    def _update_duration_label(self, value):
        """Update duration label with h:m:s format"""
        duration = int(float(value))
        
        if duration >= 3600:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            if minutes > 0 or seconds > 0:
                self.duration_label.config(text=f"{hours}h {minutes}m {seconds}s")
            else:
                self.duration_label.config(text=f"{hours}h")
        elif duration >= 60:
            minutes = duration // 60
            seconds = duration % 60
            if seconds > 0:
                self.duration_label.config(text=f"{minutes}m {seconds}s")
            else:
                self.duration_label.config(text=f"{minutes}m")
        else:
            self.duration_label.config(text=f"{duration}s")
    
    def _set_duration(self, duration):
        """Set duration from quick buttons"""
        self.clip_duration.set(duration)
        self.duration_label.config(text=f"{duration}s")
    
    def _browse_video_file(self):
        """Browse for video file"""
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
        """Start video clipping"""
        if self.is_processing:
            return
        
        source_type = self.clipper_source_type.get()
        
        if source_type == 'url':
            video_source = self.clipper_url.get("1.0", tk.END).strip()
            if not video_source:
                messagebox.showwarning("Missing URL", "Please paste a video URL")
                return
        else:
            video_source = self.clipper_file_path.get()
            if not video_source:
                messagebox.showwarning("Missing File", "Please select a video file")
                return
        
        num_clips = self.num_clips.get()
        clip_duration = self.clip_duration.get()
        method = self.detection_method.get()
        
        self.is_processing = True
        self.clipper_btn.config(state=tk.DISABLED, bg="#6e7681")
        self.status_label.config(text="🔄 Processing video...")
        self.progress_var.set(0)
        
        Thread(target=self._clip_video_worker, 
               args=(video_source, source_type, num_clips, clip_duration, method),
               daemon=True).start()
    
    def _clip_video_worker(self, video_source, source_type, num_clips, clip_duration, method):
        """Background worker for clipping"""
        try:
            from video.clipper import SmartClipper, VideoHighlightDetector
            
            start_time = time.time()
            
            if clip_duration <= 30:
                format_str = 'short'
            elif clip_duration <= 60:
                format_str = 'medium'
            else:
                format_str = 'long'
            
            if source_type == 'url':
                self._ui("📥 Downloading video...", 20)
                
                clipper = SmartClipper()
                result = clipper.clip_from_url(
                    url=video_source,
                    num_clips=num_clips,
                    format=format_str,
                    method=method,
                    clip_duration=clip_duration,
                    cleanup=True
                )
                
                if result.get('error'):
                    raise Exception(result['error'])
                
                clips = result.get('clips', [])
                highlights = result.get('highlights', [])
            
            else:  # local file
                self._ui("📂 Loading video...", 20)
                
                detector = VideoHighlightDetector()
                
                try:
                    if method == 'semantic':
                        self._ui("🧠 Understanding content...", 40)
                    else:
                        self._ui("🔍 Analyzing audio...", 40)
                    
                    highlights = detector.detect_highlights(video_source, num_clips, method=method)
                    
                    self._ui("✂️ Cutting clips...", 60)
                    output_dir = "output/clips"
                    clips = detector.auto_clip(video_source, output_dir, num_clips, format_str, 
                                              method, clip_duration=clip_duration)
                finally:
                    detector.cleanup()
            
            if not clips:
                self._ui("❌ No clips generated", 0)
                messagebox.showerror("Error", "Failed to generate clips")
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
            
            self._ui(f"✅ Done! ({elapsed:.1f}s)", 100)
            messagebox.showinfo("Success", 
                f"✅ Created {len(clips)} clips in {elapsed:.1f}s!\n"
                f"📁 Saved to: output/clips/")
        
        except ImportError as e:
            error_msg = str(e)
            self._ui("❌ Missing dependencies", 0)
            
            if 'yt_dlp' in error_msg and source_type == 'url':
                messagebox.showerror("Error", 
                    "yt-dlp not installed!\n\n"
                    "Install: pip install yt-dlp")
            else:
                messagebox.showerror("Error", f"Missing: {error_msg}")
        
        except Exception as e:
            error_msg = str(e)
            self._ui(f"❌ Error: {error_msg}", 0)
            logger.exception("Clip video failed")
            messagebox.showerror("Error", f"Failed:\n{error_msg}")
        
        finally:
            def enable_button():
                self.clipper_btn.config(state=tk.NORMAL, bg="#f85149")
                self.is_processing = False
            
            self.parent.after(0, enable_button)
    
    def _ui(self, message, progress):
        """Update UI status"""
        def update():
            self.status_label.config(text=message)
            if progress is not None:
                self.progress_var.set(progress)
        
        self.parent.after(0, update)
