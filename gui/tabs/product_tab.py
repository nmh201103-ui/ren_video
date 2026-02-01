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
        self.videos_folder = None  # None = dùng output/videos; set khi user chọn thư mục
        
        if video_formats:
            self.VIDEO_FORMATS = video_formats
        
        self._setup_ui()
        ensure_directory("output/videos")
    
    def _setup_ui(self):
        """Build the Product Review tab UI"""
        from tkinter import ttk
        container = tk.Frame(self.parent, bg="#161b22")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        left = tk.Frame(container, bg="#0d1117", width=800)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right = tk.Frame(container, bg="#0d1117", width=600)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # === RIGHT PANEL (scrollable) ===
        right_scroll_frame = tk.Frame(right, bg="#0d1117")
        right_scroll_frame.pack(fill=tk.BOTH, expand=True)
        right_canvas = tk.Canvas(right_scroll_frame, bg="#0d1117", highlightthickness=0)
        right_scrollbar = ttk.Scrollbar(right_scroll_frame, orient="vertical", command=right_canvas.yview)
        right_inner = tk.Frame(right_canvas, bg="#0d1117")
        right_inner.bind("<Configure>", lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))
        right_canvas.create_window((0, 0), window=right_inner, anchor="nw")
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def _scroll_right(evt):
            right_canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")
        right_canvas.bind("<MouseWheel>", _scroll_right)
        right_inner.bind("<MouseWheel>", _scroll_right)
        
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
        
        self._add_tiktok_upload_section(right_inner)
        self._add_status_panel(right_inner)
        self._add_tips_panel(right_inner, [
            "📌 Video affiliate: slide ảnh + giọng đọc, không hiệu ứng — hợp xu hướng",
            "🔗 Shopee: phải mở Chrome với Remote Debugging (port 9222) trước khi Generate",
            "⚡ Short: TikTok/Reels | 📹 Medium: Shorts | 🎬 Long: YouTube"
        ])
    
    def _add_tiktok_upload_section(self, parent):
        """TikTok: chọn video, tài khoản, link (tùy chọn), đẩy video (ADB/emulator)."""
        card = tk.Frame(parent, bg="#21262d", padx=16, pady=14)
        card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(card, text="📤 Đăng video TikTok", font=("Segoe UI", 11, "bold"),
                 fg="#c9d1d9", bg="#21262d").pack(anchor="w", pady=(0, 2))
        tk.Label(card, text="Emulator + ADB. Link sản phẩm tùy chọn (không nhập = đăng video thường).", font=("Segoe UI", 8),
                 fg="#8b949e", bg="#21262d", wraplength=420).pack(anchor="w", pady=(0, 10))
        # --- Video: chọn file + thư mục ---
        row_video = tk.Frame(card, bg="#21262d")
        row_video.pack(fill=tk.X, pady=(0, 6))
        tk.Label(row_video, text="Video", font=("Segoe UI", 9), fg="#8b949e", bg="#21262d", width=6, anchor="w").pack(side=tk.LEFT, padx=(0, 6))
        self.tiktok_video_display_var = tk.StringVar(value="Chưa chọn / dùng video vừa tạo")
        lbl = tk.Label(row_video, textvariable=self.tiktok_video_display_var, font=("Consolas", 8), bg="#0d1117", fg="#8b949e", anchor="w")
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 4))
        tk.Button(row_video, text="Chọn video", font=("Segoe UI", 8), bg="#388bfd", fg="#ffffff", relief=tk.FLAT, cursor="hand2", command=self._choose_video_file).pack(side=tk.LEFT, ipadx=6, ipady=2)
        tk.Button(row_video, text="Thư mục", font=("Segoe UI", 8), bg="#30363d", fg="#c9d1d9", relief=tk.FLAT, cursor="hand2", command=self._choose_videos_folder).pack(side=tk.LEFT, padx=(4, 0), ipadx=4, ipady=2)
        tk.Button(row_video, text="Mở", font=("Segoe UI", 8), bg="#30363d", fg="#c9d1d9", relief=tk.FLAT, cursor="hand2", command=self._open_videos_folder).pack(side=tk.LEFT, padx=(2, 0), ipadx=4, ipady=2)
        # --- Tài khoản ---
        row_user = tk.Frame(card, bg="#21262d")
        row_user.pack(fill=tk.X, pady=4)
        tk.Label(row_user, text="Tài khoản", font=("Segoe UI", 9), fg="#8b949e", bg="#21262d", width=6, anchor="w").pack(side=tk.LEFT, padx=(0, 6))
        self.tiktok_username_var = tk.StringVar(value=self._load_tiktok_username())
        tk.Entry(row_user, textvariable=self.tiktok_username_var, font=("Consolas", 9), bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        row_pass = tk.Frame(card, bg="#21262d")
        row_pass.pack(fill=tk.X, pady=4)
        tk.Label(row_pass, text="Mật khẩu", font=("Segoe UI", 9), fg="#8b949e", bg="#21262d", width=6, anchor="w").pack(side=tk.LEFT, padx=(0, 6))
        self.tiktok_password_var = tk.StringVar(value=self._load_tiktok_password())
        tk.Entry(row_pass, textvariable=self.tiktok_password_var, show="*", font=("Consolas", 9), bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.tiktok_save_creds_var = tk.BooleanVar(value=True)
        tk.Checkbutton(card, text="Lưu vào .env", variable=self.tiktok_save_creds_var, font=("Segoe UI", 8), fg="#8b949e", bg="#21262d", selectcolor="#161b22").pack(anchor="w", pady=(0, 6))
        # --- Link sản phẩm (tùy chọn) ---
        row_link = tk.Frame(card, bg="#21262d")
        row_link.pack(fill=tk.X, pady=4)
        tk.Label(row_link, text="Link SP", font=("Segoe UI", 9), fg="#8b949e", bg="#21262d", width=6, anchor="w").pack(side=tk.LEFT, padx=(0, 6))
        self.tiktok_link_var = tk.StringVar()
        tk.Entry(row_link, textvariable=self.tiktok_link_var, font=("Consolas", 8), bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        tk.Button(row_link, text="Mở", font=("Segoe UI", 8), bg="#30363d", fg="#c9d1d9", relief=tk.FLAT, cursor="hand2", command=self._open_tiktok_link).pack(side=tk.RIGHT, padx=(2, 0), ipadx=4, ipady=2)
        tk.Button(row_link, text="Copy", font=("Segoe UI", 8), bg="#30363d", fg="#c9d1d9", relief=tk.FLAT, cursor="hand2", command=self._copy_tiktok_link).pack(side=tk.RIGHT, padx=(2, 0), ipadx=4, ipady=2)
        # --- Nút đẩy ---
        row_btn = tk.Frame(card, bg="#21262d")
        row_btn.pack(fill=tk.X, pady=(12, 0))
        tk.Button(row_btn, text="📤 Đẩy video lên TikTok (ADB/emulator)", font=("Segoe UI", 10, "bold"), bg="#238636", fg="#ffffff", relief=tk.FLAT, cursor="hand2", command=self._upload_to_tiktok).pack(fill=tk.X, ipady=8)

    def _load_tiktok_username(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv("TIKTOK_USERNAME", "") or ""
        except Exception:
            return os.getenv("TIKTOK_USERNAME", "") or ""

    def _load_tiktok_password(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv("TIKTOK_PASSWORD", "") or ""
        except Exception:
            return os.getenv("TIKTOK_PASSWORD", "") or ""

    def _save_tiktok_credentials_if_needed(self):
        if not self.tiktok_save_creds_var.get():
            return
        uname = (self.tiktok_username_var.get() or "").strip()
        pwd = (self.tiktok_password_var.get() or "").strip()
        if not uname:
            return
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_path = os.path.abspath(env_path)
        try:
            lines = []
            if os.path.isfile(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("TIKTOK_USERNAME=") or line.strip().startswith("TIKTOK_PASSWORD="):
                            continue
                        lines.append(line)
            lines.append("TIKTOK_USERNAME=%s\n" % uname)
            lines.append("TIKTOK_PASSWORD=%s\n" % pwd)
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            logger.warning("Could not save TikTok credentials to .env: %s", e)

    def _choose_video_file(self):
        """Chọn file video để đẩy lên TikTok (Generate hoặc chọn file đều được)."""
        initial = getattr(self, "videos_folder", None) or os.path.abspath("output/videos")
        path = filedialog.askopenfilename(
            title="Chọn video đăng TikTok",
            initialdir=initial if os.path.isdir(initial) else None,
            filetypes=[("Video", "*.mp4 *.mov *.MP4 *.MOV"), ("All", "*.*")]
        )
        if path and os.path.isfile(path):
            self.video_path = path
            self.tiktok_video_display_var.set(os.path.basename(path))
            self.status_label.config(text="✅ Đã chọn video: %s" % os.path.basename(path))

    def _choose_videos_folder(self):
        """Chọn thư mục chứa video (dùng cho Mở thư mục và Chọn video)."""
        initial = getattr(self, "videos_folder", None) or os.path.abspath("output/videos")
        folder = filedialog.askdirectory(title="Chọn thư mục video", initialdir=initial if os.path.isdir(initial) else None)
        if folder:
            self.videos_folder = folder
            self.status_label.config(text="✅ Thư mục: %s" % folder)

    def _open_videos_folder(self):
        """Mở thư mục video: nếu đã chọn thì mở thư mục đã chọn, không thì mở output/videos."""
        folder = getattr(self, "videos_folder", None) or os.path.abspath("output/videos")
        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        else:
            import subprocess
            subprocess.run(["xdg-open", folder] if os.path.exists("/usr/bin/xdg-open") else ["open", folder], check=False)

    def _open_tiktok_link(self):
        """Mở link trong trình duyệt để kiểm tra đúng sản phẩm TikTok Shop chưa."""
        link = (self.tiktok_link_var.get() or "").strip()
        if not link:
            messagebox.showinfo("Link sản phẩm", "Dán link TikTok Shop vào ô phía trên rồi bấm 'Mở link' để kiểm tra có đúng trang sản phẩm không.")
            return
        if not (link.startswith("http://") or link.startswith("https://")):
            link = "https://" + link
        try:
            import webbrowser
            webbrowser.open(link)
            self.status_label.config(text="✅ Đã mở link trong trình duyệt — kiểm tra đúng sản phẩm thì dùng link này khi đăng TikTok.")
        except Exception as e:
            messagebox.showerror("Lỗi", "Không mở được link: %s" % e)

    def _copy_tiktok_link(self):
        link = (self.tiktok_link_var.get() or "").strip()
        if not link:
            messagebox.showinfo("Link sản phẩm", "Dán link vào ô phía trên rồi bấm Copy.")
            return
        root = self.parent.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(link)
        self.status_label.config(text="✅ Đã copy link sản phẩm — dán vào TikTok khi đăng (Thêm link/Sản phẩm).")
        messagebox.showinfo("Đã copy", "Link đã copy. Trong app TikTok (emulator): khi đăng video bấm 'Thêm link' hoặc 'Sản phẩm' → dán (Ctrl+V).")

    def _upload_to_tiktok(self):
        """Gọi module đẩy video lên TikTok qua ADB/emulator."""
        video_path = getattr(self, "video_path", None)
        if not video_path or not os.path.isfile(video_path):
            messagebox.showwarning("Chưa có video", "Generate video trước, hoặc bấm 'Chọn video' để chọn file video.")
            return
        self._save_tiktok_credentials_if_needed()
        username = (self.tiktok_username_var.get() or "").strip()
        password = (self.tiktok_password_var.get() or "").strip()
        product_link = (self.tiktok_link_var.get() or "").strip()
        try:
            from scripts.tiktok_upload_adb import upload_video_to_tiktok
            ok, msg = upload_video_to_tiktok(video_path, username=username, password=password, product_link=product_link)
            if ok:
                self.status_label.config(text="✅ %s" % (msg or "Đã gửi lệnh đẩy TikTok."))
                messagebox.showinfo("TikTok", msg or "Xem emulator để hoàn tất đăng video + gắn link.")
            else:
                self.status_label.config(text="⚠️ %s" % (msg or "Lỗi đẩy TikTok."))
                messagebox.showwarning("TikTok", msg or "Kiểm tra ADB và emulator. Xem docs/TIKTOK_UPLOAD.md.")
        except ImportError:
            self.status_label.config(text="⚠️ Chạy script tiktok_upload_adb thủ công.")
            messagebox.showinfo("TikTok", "Module scripts.tiktok_upload_adb chưa có hoặc lỗi. Mở thư mục output/videos, copy video vào emulator rồi đăng thủ công trong app TikTok (Thêm link).\n\nXem docs/TIKTOK_UPLOAD.md.")

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
        status_card = tk.Frame(parent, bg="#21262d", padx=16, pady=14)
        status_card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(status_card, text="📊 Status", font=("Segoe UI", 11, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(anchor="w", pady=(0, 6))
        self.status_label = tk.Label(status_card, text="Ready 🚀",
                                     font=("Segoe UI", 9), fg="#8b949e", bg="#21262d",
                                     wraplength=420, justify=tk.LEFT)
        self.status_label.pack(anchor="w", pady=(0, 8))
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(status_card, variable=self.progress_var,
                                           maximum=100, length=420)
        self.progress_bar.pack(fill=tk.X)

    def _add_tips_panel(self, parent, tips):
        """Add tips panel"""
        tips_card = tk.Frame(parent, bg="#21262d", padx=16, pady=14)
        tips_card.pack(fill=tk.X)
        tk.Label(tips_card, text="💡 Tips", font=("Segoe UI", 11, "bold"),
                fg="#c9d1d9", bg="#21262d").pack(anchor="w", pady=(0, 6))
        for tip in tips:
            tk.Label(tips_card, text=tip, font=("Segoe UI", 8),
                    fg="#8b949e", bg="#21262d", wraplength=420,
                    justify=tk.LEFT).pack(anchor="w", pady=1)
    
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
            # Scraper lỗi (vd: Chrome chưa mở port 9222) → trả về data rỗng, không tiếp tục
            if data.get("_scrape_failed"):
                err = data.get("_scrape_error", "")
                if "ECONNREFUSED" in err or "9222" in err:
                    raise ValueError(
                        "Không kết nối được Chrome. Mở Chrome với Remote Debugging (port 9222) rồi thử lại.\n"
                        "Cách mở: đóng hết Chrome → chạy: chrome.exe --remote-debugging-port=9222"
                    )
                raise ValueError(f"Scraper lỗi: {err}")
            if not data.get("title") or (not data.get("image_urls") and not (data.get("description") or "").strip()):
                raise ValueError("Không lấy được thông tin sản phẩm (title hoặc ảnh). Thử mở lại trang Shopee trong Chrome đã bật debug.")
            
            self._ui("🔄 Processing content...", 30)
            
            processor = ContentProcessor()
            processed = processor.process(data)
            processed["person_image_path"] = self.person_image_path
            # Affiliate: slide ảnh + giọng đọc only — không hiệu ứng zoom/pan, không caption chữ đọc
            processed["no_motion"] = True
            processed["show_caption"] = False
            
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
            # Đảm bảo đủ num_scenes (pad bằng heuristic nếu LLM trả về ít hơn)
            if len(script) < num_scenes:
                from video.ai_providers import HeuristicScriptGenerator
                fallback = HeuristicScriptGenerator().generate(
                    processed['title'], processed['description'], processed.get('price', '')
                )
                for i in range(len(script), num_scenes):
                    script.append(fallback[i % len(fallback)])
            processed["script"] = script[:num_scenes]
            
            # Render video
            self._ui(f"🎬 Rendering video ({target_duration}s)...", 50)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/videos/product_{format_key}_{timestamp}.mp4"
            
            image_count = len(processed.get("image_urls") or [])
            max_images = max(num_scenes, image_count) if image_count else None
            success = renderer.render(
                processed,
                output_path,
                max_images=max_images,
                target_duration=target_duration,
                progress_callback=lambda msg, pct: self._ui(msg, pct)
            )
            
            if success:
                self.video_path = output_path
                if getattr(self, "tiktok_video_display_var", None):
                    self.tiktok_video_display_var.set(os.path.basename(output_path))
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
