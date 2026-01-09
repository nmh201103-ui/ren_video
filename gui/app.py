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
        self.root.title("🎬 Affiliate Video Creator")
        self.root.geometry("900x750")
        self.root.resizable(False, False)

        self.is_processing = False
        self.video_path = None
        self.status_text = tk.StringVar(value="Sẵn sàng")
        self.thumbnail_img = None

        self._setup_style()
        self._setup_ui()
        ensure_directory("output/videos")

    # ================= STYLE =================
    def _setup_style(self):
        style = ttk.Style(self.root)
        style.configure("TButton", font=("Arial", 12, "bold"), padding=6)
        style.configure("TLabel", font=("Arial", 12))
        style.configure("Header.TLabel", font=("Arial", 18, "bold"))
        style.configure("Status.TLabel", foreground="#0066CC")
        style.configure("TProgressbar", thickness=20)

    # ================= UI =================
    def _setup_ui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Affiliate Video Creator", style="Header.TLabel").pack(pady=10)

        ttk.Label(frame, text="📥 Nhập link sản phẩm:").pack(anchor="w", pady=5)
        self.url_text = tk.Text(frame, height=5, font=("Arial", 12))
        self.url_text.pack(fill=tk.X)

        ttk.Button(frame, text="Tạo Video", command=self._on_create_video).pack(pady=10)

        ttk.Label(frame, text="🖼 Thumbnail sản phẩm:", padding=(0,5)).pack(anchor="w")
        self.thumbnail_label = ttk.Label(frame)
        self.thumbnail_label.pack(pady=5)

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(frame, textvariable=self.status_text, style="Status.TLabel", wraplength=850)
        self.status_label.pack(fill=tk.X, pady=5)

    # ================= CORE =================
    def _on_create_video(self):
        if self.is_processing:
            messagebox.showwarning("Đang chạy", "Đợi xong đã!")
            return

        urls = [u.strip() for u in self.url_text.get("1.0", tk.END).splitlines() if u.strip()]
        if not urls:
            messagebox.showerror("Lỗi", "Chưa nhập link")
            return

        self.is_processing = True
        self.progress.start()

        thread = threading.Thread(target=self._create_video_worker, args=(urls[0],))
        thread.daemon = True
        thread.start()

    def _create_video_worker(self, url):
        try:
            self._ui("🔍 Đang scrape sản phẩm...")
            scraper = get_scraper(url)
            product_data = scraper.scrape(url)

            if not product_data or not product_data.get("description"):
                raise ValueError("Scrape không có mô tả")

            # Hiển thị thumbnail sản phẩm (safe access)
            image_urls = product_data.get("image_urls") or []
            logger.info("Product has %d images", len(image_urls))
            img_url = image_urls[0] if image_urls else None
            if img_url:
                self._show_thumbnail(img_url)
            else:
                logger.debug("No thumbnail to show for this product")

            self._ui("📝 Đang xử lý nội dung...")
            processor = ContentProcessor()
            processed = processor.process(product_data)
            if not processed:
                logger.error("Processor returned None (processing failed) for product_data: %s", product_data)
                raise RuntimeError("Processor failed to process product data")

            if not processed.get("description"):
                logger.warning("⚠️ Processor làm rỗng mô tả → dùng lại mô tả gốc")
                processed["description"] = product_data["description"]

            if not processed["description"].strip():
                raise ValueError("Description rỗng – không render")

            self._ui("🎬 Đang render video...")
            renderer = SmartVideoRenderer()
            output_file = f"output/videos/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            ok = renderer.render(processed, output_file)

            if not ok:
                raise RuntimeError("Render thất bại")

            self._ui(f"✅ Video đã tạo xong: {output_file}")
            messagebox.showinfo("Thành công", f"Video đã tạo:\n{output_file}")

        except Exception as e:
            logger.exception("Error in _create_video_worker: %s", e)
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.progress.stop()
            self.is_processing = False

    # ================= UI HELPERS =================
    def _ui(self, text):
        self.root.after(0, lambda: self.status_text.set(text))

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
