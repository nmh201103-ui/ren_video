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
        self.root.title("🎬 Affiliate Video Creator Pro")
        self.root.geometry("1200x950")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f2f5")

        self.is_processing = False
        self.video_path = None
        self.status_text = tk.StringVar(value="Sẵn sàng tạo video 🎥")
        self.progress_percent = tk.IntVar(value=0)
        self.thumbnail_img = None
        self.video_mode = tk.StringVar(value="simple")  # video mode: simple or demo

        self._setup_style()
        self._setup_ui()
        ensure_directory("output/videos")

    # ================= STYLE =================
    def _setup_style(self):
        style = ttk.Style(self.root)
        
        # Modern button style
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Primary.TButton", foreground="white", background="#0066CC")
        
        # Labels
        style.configure("TLabel", font=("Segoe UI", 11), background="#f0f2f5")
        style.configure("Header.TLabel", font=("Segoe UI", 22, "bold"), 
                       foreground="#1a1a1a", background="#f0f2f5")
        style.configure("Status.TLabel", foreground="#0066CC", background="#f0f2f5")
        
        # Radio buttons
        style.configure("TRadiobutton", font=("Segoe UI", 10), background="#ffffff")
        
        # Progress bar
        style.configure("TProgressbar", thickness=25, troughcolor="#e0e0e0", 
                       background="#0066CC")

    # ================= UI =================
    def _setup_ui(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg="#f0f2f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="🎬 Affiliate Video Creator Pro", 
                 style="Header.TLabel").pack(pady=15)
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.RAISED, bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_inner = tk.Frame(content_frame, bg="#ffffff")
        content_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # URL Input Section
        url_section = tk.LabelFrame(content_inner, text="📥 Link Sản Phẩm", 
                                   font=("Segoe UI", 11, "bold"), bg="#ffffff", 
                                   fg="#333", relief=tk.GROOVE, bd=2)
        url_section.pack(fill=tk.X, pady=(0, 15))
        
        self.url_text = tk.Text(url_section, height=4, font=("Segoe UI", 10), 
                               relief=tk.FLAT, bg="#f9f9f9", wrap=tk.WORD)
        self.url_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Video Mode Section - NEW!
        mode_section = tk.LabelFrame(content_inner, text="🎨 Chế Độ Video", 
                                    font=("Segoe UI", 11, "bold"), bg="#ffffff", 
                                    fg="#333", relief=tk.GROOVE, bd=2)
        mode_section.pack(fill=tk.X, pady=(0, 15))
        
        mode_inner = tk.Frame(mode_section, bg="#ffffff")
        mode_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Radio buttons for video modes
        modes = [
            ("simple", "📹 Video Đơn Giản", "Sản phẩm + giọng đọc", "#e3f2fd"),
            ("demo", "🤝 Video Demo", "Người cầm sản phẩm + giọng đọc", "#fff3e0"),
            ("reviewer", "🎙️ Video Reviewer", "Người review + sản phẩm (cần bật AI Avatar)", "#f3e5f5")
        ]
        
        self.mode_frames = {}  # Store frames for highlighting
        
        for idx, (mode_val, title, desc, color) in enumerate(modes):
            mode_frame = tk.Frame(mode_inner, bg="#f9f9f9", relief=tk.RAISED, bd=2)
            mode_frame.pack(fill=tk.X, pady=5)
            self.mode_frames[mode_val] = mode_frame
            
            rb = tk.Radiobutton(mode_frame, text=title, variable=self.video_mode, 
                               value=mode_val, font=("Segoe UI", 11, "bold"),
                               bg="#f9f9f9", activebackground=color,
                               selectcolor="#0066CC", indicatoron=1,
                               command=lambda m=mode_val, c=color: self._on_mode_change(m, c))
            rb.pack(anchor="w", padx=10, pady=(10, 2))
            
            desc_label = tk.Label(mode_frame, text=desc, font=("Segoe UI", 9),
                                 fg="#666", bg="#f9f9f9", wraplength=750)
            desc_label.pack(anchor="w", padx=30, pady=(0, 10))
        
        # Demo person picker
        self.person_image_path = None
        picker_frame = tk.Frame(content_inner, bg="#ffffff")
        picker_frame.pack(fill=tk.X, pady=(0, 10))
        
        # AI Avatar toggle (checkbox)
        self.use_ai_avatar = tk.BooleanVar(value=False)
        ai_frame = tk.Frame(content_inner, bg="#ffffff", relief=tk.GROOVE, bd=2)
        ai_frame.pack(fill=tk.X, pady=(0, 15))
        
        ai_check = tk.Checkbutton(
            ai_frame, 
            text="🤖 Sử dụng AI Avatar (Talking Head - D-ID)", 
            variable=self.use_ai_avatar,
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            activebackground="#e8f5e9",
            selectcolor="#4CAF50"
        )
        ai_check.pack(anchor="w", padx=10, pady=10)
        
        # Avatar backend selector (Colab vs Wav2Lip vs D-ID)
        backend_frame = tk.Frame(ai_frame, bg="#ffffff")
        backend_frame.pack(anchor="w", padx=30, pady=(0, 10))
        
        self.avatar_backend = tk.StringVar(value="wav2lip")
        
        wav2lip_rb = tk.Radiobutton(
            backend_frame,
            text="🆓 Wav2Lip (Miễn phí - local, fast)",
            variable=self.avatar_backend,
            value="wav2lip",
            font=("Segoe UI", 9),
            bg="#ffffff"
        )
        wav2lip_rb.pack(anchor="w")
        
        colab_rb = tk.Radiobutton(
            backend_frame,
            text="🆓 Colab SadTalker (Miễn phí - API)",
            variable=self.avatar_backend,
            value="colab",
            font=("Segoe UI", 9),
            bg="#ffffff"
        )
        colab_rb.pack(anchor="w")
        
        did_rb = tk.Radiobutton(
            backend_frame,
            text="💳 D-ID API (Trả phí - high quality)",
            variable=self.avatar_backend,
            value="did",
            font=("Segoe UI", 9),
            bg="#ffffff"
        )
        did_rb.pack(anchor="w")
        
        ai_note = tk.Label(
            ai_frame, 
            text="ℹ️ Wav2Lip: Cài sẵn, không cần setup\n   Colab: Upload notebook, chạy cell 5, copy URL ngrok\n   D-ID: Set DID_API_KEY env variable",
            font=("Segoe UI", 8),
            fg="#666",
            bg="#ffffff",
            justify="left"
        )
        ai_note.pack(anchor="w", padx=30, pady=(0, 10))
        
        self.pick_person_btn = tk.Button(picker_frame, text="👤 Chọn ảnh người (Demo + Reviewer)",
                                        font=("Segoe UI", 10), bg="#eeeeee", fg="#333",
                                        relief=tk.RAISED, bd=2,
                                        command=self._pick_person_image, cursor="hand2")
        self.pick_person_btn.pack(side=tk.LEFT, padx=10)
        self.pick_person_btn.config(state=tk.DISABLED)
        
        self.person_label = tk.Label(picker_frame, text="Chưa chọn ảnh",
                                    font=("Segoe UI", 9), fg="#666", bg="#ffffff")
        self.person_label.pack(side=tk.LEFT, padx=10)
        
        # Create Button
        btn_frame = tk.Frame(content_inner, bg="#ffffff")
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        create_btn = tk.Button(btn_frame, text="🚀 Tạo Video Ngay", 
                              command=self._on_create_video,
                              font=("Segoe UI", 12, "bold"),
                              bg="#0066CC", fg="white", 
                              activebackground="#0052A3",
                              relief=tk.RAISED, bd=3,
                              cursor="hand2", pady=12)
        create_btn.pack(fill=tk.X)
        
        # Thumbnail Section
        thumb_section = tk.LabelFrame(content_inner, text="🖼 Preview Sản Phẩm",
                                     font=("Segoe UI", 11, "bold"), bg="#ffffff",
                                     fg="#333", relief=tk.GROOVE, bd=2)
        thumb_section.pack(fill=tk.X, pady=(0, 15))
        
        self.thumbnail_label = tk.Label(thumb_section, bg="#f9f9f9", 
                                       text="Chưa có ảnh", fg="#999",
                                       font=("Segoe UI", 10))
        self.thumbnail_label.pack(pady=20)
        
        # Progress Section
        progress_frame = tk.LabelFrame(content_inner, text="📊 Tiến Độ",
                                      font=("Segoe UI", 11, "bold"), bg="#ffffff",
                                      fg="#333", relief=tk.GROOVE, bd=2)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        progress_inner = tk.Frame(progress_frame, bg="#ffffff")
        progress_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Progress bar with percentage
        self.progress = ttk.Progressbar(progress_inner, mode="determinate", 
                                       variable=self.progress_percent, maximum=100)
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        # Percentage label
        self.percent_label = tk.Label(progress_inner, textvariable=self.progress_percent,
                                     font=("Segoe UI", 10, "bold"), fg="#0066CC",
                                     bg="#ffffff")
        self.percent_label.pack()
        
        # Status Label
        status_frame = tk.Frame(content_inner, bg="#e8f4ff", relief=tk.FLAT, bd=1)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, textvariable=self.status_text,
                                    font=("Segoe UI", 10), fg="#0066CC",
                                    bg="#e8f4ff", wraplength=880, pady=10)
        self.status_label.pack()
        
        # Log Section - NEW!
        log_section = tk.LabelFrame(content_inner, text="📋 Log Chi Tiết",
                                   font=("Segoe UI", 11, "bold"), bg="#ffffff",
                                   fg="#333", relief=tk.GROOVE, bd=2)
        log_section.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        log_inner = tk.Frame(log_section, bg="#ffffff")
        log_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrolled text widget for logs
        log_scroll = tk.Scrollbar(log_inner)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_inner, height=8, font=("Consolas", 9),
                               bg="#1e1e1e", fg="#00ff00", wrap=tk.WORD,
                               yscrollcommand=log_scroll.set, relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Make log read-only
        self.log_text.config(state=tk.DISABLED)
        
        # Set initial mode highlight
        self.root.after(100, lambda: self._on_mode_change("simple", "#e3f2fd"))

    # ================= CORE =================
    def _on_create_video(self):
        if self.is_processing:
            messagebox.showwarning("Đang chạy", "Đợi xong đã!")
            return

        urls = [u.strip() for u in self.url_text.get("1.0", tk.END).splitlines() if u.strip()]
        if not urls:
            messagebox.showerror("Lỗi", "Chưa nhập link")
            return
        
        # Check if AI Avatar is enabled but not configured
        if self.use_ai_avatar.get():
            avatar_backend = self.avatar_backend.get()
            if avatar_backend == "colab":
                colab_url = os.getenv("COLAB_API_URL")
                if not colab_url:
                    messagebox.showerror(
                        "⚠️ Colab API chưa setup",
                        "Hướng dẫn setup Colab:\n\n"
                        "1. Mở file: SadTalker_Colab_Free.ipynb\n"
                        "2. Upload lên Google Colab\n"
                        "3. Chạy Cell 5 (API Server)\n"
                        "4. Copy URL ngrok từ output\n"
                        "5. Chạy lệnh (thay URL):\n"
                        "   $env:COLAB_API_URL='https://denny-pseudospiritual-stomachically.ngrok-free.dev'\n\n"
                        "Hoặc tắt AI Avatar nếu chỉ muốn dùng ảnh tĩnh"
                    )
                    return
            elif avatar_backend == "did":
                did_api_key = os.getenv("DID_API_KEY")
                if not did_api_key:
                    messagebox.showerror(
                        "⚠️ D-ID API chưa setup",
                        "Set DID_API_KEY environment variable:\n\n"
                        "$env:DID_API_KEY='your-api-key-here'\n\n"
                        "Hoặc đăng ký free trial tại:\n"
                        "https://www.d-id.com"
                    )
                    return

        self.is_processing = True
        self.progress_percent.set(0)

        thread = threading.Thread(target=self._create_video_worker, args=(urls[0],))
        thread.daemon = True
        thread.start()

    def _create_video_worker(self, url):
        try:
            self._ui("🔍 Đang scrape sản phẩm...", 5)
            self._append_log(f"🔗 URL: {url}")
            
            scraper = get_scraper(url)
            product_data = scraper.scrape(url)

            if not product_data or not product_data.get("description"):
                raise ValueError("Scrape không có mô tả")
            
            self._append_log(f"✅ Scrape thành công: {product_data.get('title', 'N/A')[:50]}...")
            self._append_log(f"📸 Có {len(product_data.get('image_urls', []))} ảnh từ scraper")

            # Hiển thị thumbnail sản phẩm (safe access)
            image_urls = product_data.get("image_urls") or []
            logger.info("Product has %d images from scraper", len(image_urls))
            img_url = image_urls[0] if image_urls else None
            if img_url:
                self._show_thumbnail(img_url)
            else:
                logger.debug("No thumbnail to show for this product")

            self._ui("📝 Đang xử lý nội dung...", 8)
            processor = ContentProcessor()
            processed = processor.process(product_data)
            
            logger.info("After processing: %d images in 'image_urls'", len(processed.get("image_urls", [])))
            self._append_log(f"📸 Sau xử lý: {len(processed.get('image_urls', []))} ảnh")
            
            if not processed:
                logger.error("Processor returned None (processing failed) for product_data: %s", product_data)
                raise RuntimeError("Processor failed to process product data")

            if not processed.get("description"):
                logger.warning("⚠️ Processor làm rỗng mô tả → dùng lại mô tả gốc")
                processed["description"] = product_data["description"]

            if not processed["description"].strip():
                raise ValueError("Description rỗng – không render")

            self._ui("🎬 Đang render video...", 0)
            video_mode = self.video_mode.get()
            use_ai_avatar = self.use_ai_avatar.get()
            avatar_backend = self.avatar_backend.get()
            
            # Đính kèm ảnh người (nếu có) cho chế độ Demo/AI Avatar
            processed["person_image_path"] = self.person_image_path
            
            # Show mode in status
            mode_names = {
                "simple": "Video Đơn Giản",
                "demo": "Video Demo (người cầm sản phẩm)",
                "reviewer": "Video Reviewer (người nói)"
            }
            mode_text = mode_names.get(video_mode, video_mode)
            if use_ai_avatar:
                if avatar_backend == "wav2lip":
                    backend_emoji = "🆓 (Local)"
                elif avatar_backend == "colab":
                    backend_emoji = "🆓 (API)"
                else:
                    backend_emoji = "💳"
                mode_text += f" + AI Avatar {backend_emoji}"
            self._ui(f"🎬 Render {mode_text}...", 0)
            
            renderer = SmartVideoRenderer(
                video_mode=video_mode, 
                use_ai_avatar=use_ai_avatar,
                avatar_backend=avatar_backend
            )
            logger.info(f"Using video mode: {video_mode}, AI Avatar: {use_ai_avatar}, Backend: {avatar_backend}")
            output_file = f"output/videos/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            
            # Render with progress callback
            ok = renderer.render(processed, output_file, progress_callback=self._render_progress)

            if not ok:
                raise RuntimeError("Render thất bại")

            self._ui(f"✅ Video đã tạo xong: {output_file}", 100)
            messagebox.showinfo("Thành công", f"Video đã tạo:\n{output_file}")

        except Exception as e:
            logger.exception("Error in _create_video_worker: %s", e)
            messagebox.showerror("Lỗi", str(e))
            self._ui("❌ Lỗi: " + str(e), 0)
        finally:
            self.progress_percent.set(0)
            self.is_processing = False

    # ================= UI HELPERS =================
    def _on_mode_change(self, mode, color):
        """Highlight selected mode frame."""
        # Persist selected mode
        self.video_mode.set(mode)
        # Enable/disable person picker based on mode
        if mode in ("demo", "reviewer"):  # Both demo and reviewer need person image
            self.pick_person_btn.config(state=tk.NORMAL)
            self.person_label.config(text=self.person_label.cget("text"))
        else:
            self.pick_person_btn.config(state=tk.DISABLED)
            self.person_image_path = None
            self.person_label.config(text="Chưa chọn ảnh")
        
        # Reset all frames
        for m, frame in self.mode_frames.items():
            if m == mode:
                frame.config(bg=color, bd=3, relief=tk.SUNKEN)
            else:
                frame.config(bg="#f9f9f9", bd=2, relief=tk.RAISED)
        
        # Update status
        mode_names = {
            "simple": "Video Đơn Giản",
            "demo": "Video Demo"
        }
        self.status_text.set(f"✅ Đã chọn: {mode_names.get(mode, mode)}")
    
    def _ui(self, text, percent=None):
        self.root.after(0, lambda: self.status_text.set(text))
        if percent is not None:
            self.root.after(0, lambda: self.progress_percent.set(percent))
        
        # Also append to log window
        self._append_log(text)
    
    def _append_log(self, message):
        """Append message to log text widget."""
        def update():
            self.log_text.config(state=tk.NORMAL)
            timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)  # Auto-scroll to bottom
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, update)
    
    def _render_progress(self, message, percent):
        """Callback for real-time render progress."""
        self._ui(f"🎬 {message}", percent)

    def _pick_person_image(self):
        path = filedialog.askopenfilename(title="Chọn ảnh người (jpg/png)",
                                          filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if path:
            self.person_image_path = path
            name = os.path.basename(path)
            self.person_label.config(text=f"Đã chọn: {name}")
            self._append_log(f"👤 Ảnh người: {path}")

    def _show_thumbnail(self, url):
        try:
            import requests
            from io import BytesIO
            response = requests.get(url, timeout=15)
            img = Image.open(BytesIO(response.content))
            img.thumbnail((300, 300))
            self.thumbnail_img = ImageTk.PhotoImage(img)
            self.root.after(0, lambda: self.thumbnail_label.config(image=self.thumbnail_img))
        except Exception as e:
            logger.warning(f"Lỗi load thumbnail: {e}")

    # ================= RUN =================
    def run(self):
        self.root.mainloop()
