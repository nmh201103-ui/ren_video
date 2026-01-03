import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
from datetime import datetime
from moviepy.editor import VideoFileClip, TextClip, concatenate_videoclips, AudioFileClip
from PIL import Image, ImageTk

from utils.helpers import get_scraper, ensure_directory
from utils.logger import get_logger
from processor.content import ContentProcessor
from video.render import VideoRenderer
from video.templates import TEMPLATE_DEFAULT

logger = get_logger()


class VideoCreatorApp:
    """Main application class"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Affiliate Video Creator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Variables
        self.product_urls = tk.StringVar()
        self.status_text = tk.StringVar(value="Sẵn sàng")
        self.is_processing = False
        self.audio_path = tk.StringVar(value="")  # optional background audio
        self.video_path = None  # To store the path of the video after rendering

        # Setup UI
        self._setup_ui()

        # Ensure directories exist
        ensure_directory('output/videos')
        ensure_directory('assets/fonts')
        ensure_directory('assets/music')
        ensure_directory('assets/images')

    def _setup_ui(self):
        """Setup giao diện"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="🎬 Affiliate Video Creator",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Create tabbed interface
        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True)

        # URL input (Multiple links)
        url_tab = ttk.Frame(tab_control)
        tab_control.add(url_tab, text="Nhập Link")

        url_label = ttk.Label(url_tab, text="Link sản phẩm (Shopee/TikTok Shop), mỗi link trên một dòng:")
        url_label.pack(anchor=tk.W, pady=(0, 5))

        self.url_text = tk.Text(url_tab, width=60, height=6)
        self.url_text.pack(fill=tk.X, pady=(0, 10))

        # Buttons for creating video
        button_frame = ttk.Frame(url_tab)
        button_frame.pack(fill=tk.X)

        create_btn = ttk.Button(button_frame, text="Tạo Video", command=self._on_create_video)
        create_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(button_frame, text="Xóa", command=self._clear_input)
        clear_btn.pack(side=tk.LEFT)

        # Status
        status_frame = ttk.LabelFrame(url_tab, text="Trạng thái", padding="15")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.status_label = ttk.Label(status_frame, textvariable=self.status_text, font=("Arial", 11), wraplength=700)
        self.status_label.pack(anchor=tk.W, fill=tk.X)

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=(10, 0), fill=tk.X)

        # Output info
        output_frame = ttk.LabelFrame(url_tab, text="Output", padding="15")
        output_frame.pack(fill=tk.X)

        output_label = ttk.Label(output_frame, text="Video sẽ được lưu vào: output/videos/", font=("Arial", 10))
        output_label.pack(anchor=tk.W)

        open_folder_btn = ttk.Button(output_frame, text="Mở thư mục output", command=self._open_output_folder)
        open_folder_btn.pack(pady=(10, 0), anchor=tk.W)

        # Optional audio
        audio_frame = ttk.LabelFrame(url_tab, text="Nhạc nền (tùy chọn)", padding="15")
        audio_frame.pack(fill=tk.X, pady=(15, 0))

        audio_path_frame = ttk.Frame(audio_frame)
        audio_path_frame.pack(fill=tk.X, pady=(0, 10))

        audio_entry = ttk.Entry(audio_path_frame, textvariable=self.audio_path, width=50)
        audio_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(audio_path_frame, text="Chọn file nhạc", command=self._select_audio_file).pack(side=tk.LEFT)
        ttk.Button(audio_path_frame, text="Xóa", command=lambda: self.audio_path.set("")).pack(side=tk.LEFT, padx=(5, 0))

        # Edit Video Tab
        edit_tab = ttk.Frame(tab_control)
        tab_control.add(edit_tab, text="Chỉnh Sửa Video")

        # Add Canvas to display video thumbnail
        self.video_canvas = tk.Canvas(edit_tab, width=320, height=180, bg="lightgray")
        self.video_canvas.pack(pady=20)

        self.video_listbox = tk.Listbox(edit_tab, width=60, height=6)
        self.video_listbox.pack(pady=20)

        edit_btn = ttk.Button(edit_tab, text="Chỉnh sửa video vừa tạo", command=self._edit_video)
        edit_btn.pack(pady=10)

    def _clear_input(self):
        self.product_urls.set("")
        self.status_text.set("Sẵn sàng")
        self.url_text.delete(1.0, tk.END)

    def _select_audio_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file nhạc",
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.aac"), ("All files", "*.*")],
            initialdir="assets/music"
        )
        if file_path:
            self.audio_path.set(file_path)

    def _on_create_video(self):
        if self.is_processing:
            messagebox.showwarning("Đang xử lý", "Vui lòng đợi quá trình hiện tại hoàn thành!")
            return

        urls = self.url_text.get("1.0", tk.END).strip().split("\n")
        urls = [url.strip() for url in urls if url.strip()]  # Remove empty lines and strip URLs

        if not urls:
            messagebox.showerror("Lỗi", "Vui lòng nhập ít nhất một link sản phẩm!")
            return

        self.is_processing = True
        self.root.after(0, lambda: self.progress.start())
        self.root.after(0, lambda: self.status_text.set("Đang phát hiện platform..."))

        # Lặp qua các link và xử lý từng link
        for url in urls:
            thread = threading.Thread(target=self._create_video_worker, args=(url,))
            thread.daemon = True
            thread.start()

    def _create_video_worker(self, url: str):
        self.root.after(0, lambda: self.status_text.set(f"Đang xử lý: {url}"))
        try:
            scraper = get_scraper(url)
            if not scraper:
                self.root.after(0, lambda: self._show_error("Không hỗ trợ platform này! Chỉ hỗ trợ Shopee và TikTok Shop."))
                return

            platform = 'shopee' if 'shopee' in url.lower() else 'tiktok'
            self.root.after(0, lambda: self.status_text.set(f"Đã phát hiện: {platform}. Đang lấy thông tin sản phẩm..."))

            product_data = scraper.scrape(url)
            if not product_data:
                self.root.after(0, lambda: self._show_error("Không thể lấy thông tin sản phẩm! Vui lòng kiểm tra lại link."))
                return

            self.root.after(0, lambda: self.status_text.set(
                f"Đã lấy được: {product_data.get('title','N/A')[:50]}... ({len(product_data.get('image_urls',[]))} ảnh)"))

            self.root.after(0, lambda: self.status_text.set("Đang xử lý nội dung..."))
            processor = ContentProcessor()
            processed_data = processor.process(product_data)

            self.root.after(0, lambda: self.status_text.set("Đang tạo video..."))
            renderer = VideoRenderer(TEMPLATE_DEFAULT)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            platform_name = processed_data.get('platform', 'unknown')
            output_filename = f"video_{platform_name}_{timestamp}.mp4"
            output_path = os.path.join("output", "videos", output_filename)

            # Render video (TTS auto, optional background audio not used)
            success = renderer.render(processed_data, output_path)

            if success:
                self.video_path = output_path
                self.root.after(0, lambda: self._show_success(f"Tạo video thành công!\nĐã lưu vào: {output_path}", output_path))
                # Update the listbox with the new video
                self._update_video_listbox(output_path)
                self._update_video_thumbnail(output_path)
            else:
                self.root.after(0, lambda: self._show_error("Có lỗi xảy ra khi tạo video!"))

        except Exception as e:
            import traceback
            logger.error(f"Error in video creation worker:\n{traceback.format_exc()}")
            self.root.after(0, lambda e=e: self._show_error(
                f"Lỗi: {str(e)}\n\nChi tiết xem trong file logs/app.log hoặc console"
            ))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.progress.stop())

    def _update_video_listbox(self, video_path):
        """Update the Listbox with the newly created video"""
        self.video_listbox.insert(tk.END, video_path)

    def _update_video_thumbnail(self, video_path):
        """Update the canvas with a thumbnail of the video"""
        try:
            video = VideoFileClip(video_path)
            thumbnail = video.get_frame(0)  # Get the first frame of the video
            img = Image.fromarray(thumbnail)
            img = img.resize((320, 180), Image.Resampling.LANCZOS)

            # Convert to PhotoImage and display on the canvas
            photo = ImageTk.PhotoImage(img)
            self.video_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.video_canvas.image = photo
        except Exception as e:
            logger.error(f"❌ Lỗi khi tạo thumbnail: {e}")

    def _edit_video(self):
        if not self.video_path:
            messagebox.showerror("Lỗi", "Chưa có video để chỉnh sửa!")
            return

        # Get selected video path from listbox
        selected_video = self.video_listbox.curselection()
        if not selected_video:
            messagebox.showerror("Lỗi", "Vui lòng chọn một video để chỉnh sửa.")
            return

        video_path = self.video_listbox.get(selected_video)
        
        # Open video file for editing (MoviePy functions)
        video = VideoFileClip(video_path)
        video = video.subclip(0, 10)  # Just a simple edit: cut the first 10 seconds

        # Optionally: Add text to video
        txt_clip = TextClip("Chỉnh sửa video", fontsize=70, color='white')
        txt_clip = txt_clip.set_pos('center').set_duration(5)

        # Combine text with video
        video = concatenate_videoclips([video, txt_clip])

        # Save the edited video
        edited_video_path = video_path.replace(".mp4", "_edited.mp4")
        video.write_videofile(edited_video_path)

        messagebox.showinfo("Chỉnh sửa thành công", f"Video đã được chỉnh sửa và lưu vào: {edited_video_path}")

    def _show_success(self, message: str, output_path: str):
        self.status_text.set(message)
        self.status_label.config(foreground='green')

        if messagebox.askyesno("Thành công", f"{message}\n\nBạn có muốn mở thư mục chứa video?"):
            self._open_output_folder()

    def _show_error(self, message: str):
        self.status_text.set(message)
        self.status_label.config(foreground='red')
        messagebox.showerror("Lỗi", message)

    def _open_output_folder(self):
        output_dir = os.path.abspath("output/videos")
        os.makedirs(output_dir, exist_ok=True)

        if os.name == 'nt':
            os.startfile(output_dir)
        elif os.name == 'posix':
            os.system(f'open "{output_dir}"' if sys.platform == 'darwin' else f'xdg-open "{output_dir}"')

    def run(self):
        self.root.mainloop()
