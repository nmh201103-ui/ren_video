import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
from datetime import datetime
from moviepy.editor import VideoFileClip, TextClip, concatenate_videoclips
from PIL import Image, ImageTk

from utils.helpers import get_scraper, ensure_directory
from utils.logger import get_logger
from processor.content import ContentProcessor
from video.render import VideoRenderer
from video.templates import TEMPLATE_DEFAULT

logger = get_logger()


class VideoCreatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Affiliate Video Creator")
        self.root.geometry("800x700")

        self.is_processing = False
        self.video_path = None
        self.status_text = tk.StringVar(value="Sẵn sàng")

        self._setup_ui()

        ensure_directory("output/videos")

    # ================= UI =================
    def _setup_ui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="🎬 Affiliate Video Creator", font=("Arial", 22, "bold")).pack(pady=10)

        self.url_text = tk.Text(frame, height=6)
        self.url_text.pack(fill=tk.X)

        ttk.Button(frame, text="Tạo Video", command=self._on_create_video).pack(pady=10)

        self.status_label = ttk.Label(frame, textvariable=self.status_text, wraplength=700)
        self.status_label.pack(fill=tk.X)

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=5)

    # ================= CORE =================
    def _on_create_video(self):
        if self.is_processing:
            messagebox.showwarning("Đang chạy", "Đợi xong đã!")
            return

        urls = [u.strip() for u in self.url_text.get("1.0", tk.END).splitlines() if u.strip()]
        if not urls:
            messagebox.showerror("Lỗi", "Chưa nhập link")
            return

        # ❗ CHỈ XỬ LÝ 1 LINK / LẦN
        self.is_processing = True
        self.progress.start()

        thread = threading.Thread(target=self._create_video_worker, args=(urls[0],))
        thread.daemon = True
        thread.start()

    def _create_video_worker(self, url):
        try:
            self._ui("Đang scrape sản phẩm...")
            scraper = get_scraper(url)
            product_data = scraper.scrape(url)

            if not product_data or not product_data.get("description"):
                raise ValueError("Scrape không có mô tả")

            self._ui("Đang xử lý nội dung...")
            processor = ContentProcessor()
            processed = processor.process(product_data)

            # 🔥 CHỐT MẠNG: nếu processor làm rỗng → dùng lại gốc
            if not processed.get("description"):
                logger.warning("⚠️ Processor làm rỗng mô tả → dùng lại mô tả gốc")
                processed["description"] = product_data["description"]

            if not processed["description"].strip():
                raise ValueError("Description rỗng – không render")

            self._ui("Đang render video...")
            renderer = VideoRenderer(TEMPLATE_DEFAULT)

            output = f"output/videos/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            ok = renderer.render(processed, output)

            if not ok:
                raise RuntimeError("Render thất bại")

            self._ui(f"✅ Tạo video xong: {output}")
            messagebox.showinfo("Thành công", f"Video đã tạo:\n{output}")

        except Exception as e:
            logger.error(e)
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.progress.stop()
            self.is_processing = False

    # ================= UTIL =================
    def _ui(self, text):
        self.root.after(0, lambda: self.status_text.set(text))

    def run(self):
        self.root.mainloop()
