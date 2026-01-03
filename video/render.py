import os
import tempfile
import requests
from io import BytesIO
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from utils.helpers import ensure_directory
from utils.logger import get_logger

logger = get_logger()

class VideoRenderer:
    def __init__(self, template=None):
        from .templates import TEMPLATE_DEFAULT
        self.template = template or TEMPLATE_DEFAULT
        self._temp_files = []

    def render(self, processed_data: dict, output_path: str, max_images: int = 5, audio_path: str = None) -> bool:
        try:
            ensure_directory(os.path.dirname(output_path))
            
            # Lấy image_data từ ContentProcessor
            images = processed_data.get("image_data", [])
            title = processed_data.get("title", "Sản phẩm Hot")
            price = processed_data.get("price", "0")
            cta = processed_data.get("cta_text", "Mua ngay!")

            # Kiểm tra các giá trị để tránh None
            if not images:
                logger.warning("⚠️ Không có dữ liệu ảnh.")
                images = []

            if not title:
                logger.warning("⚠️ Không có tiêu đề sản phẩm, sử dụng mặc định: Sản phẩm Hot")
                title = "Sản phẩm Hot"
            
            if not price or price == "None":
                logger.warning("⚠️ Không có giá, sử dụng mặc định: 0")
                price = "0"
            
            if not cta:
                logger.warning("⚠️ Không có CTA, sử dụng mặc định: Mua ngay!")
                cta = "Mua ngay!"
            
            logger.info(f"🚀 Renderer bắt đầu với {len(images)} ảnh.")

            if not images:
                logger.error("❌ Không có dữ liệu ảnh để render!")
                return False

            clips = []
            # 1. Clip Tiêu đề
            clips.append(self._text_clip(title, 70, "#FFFFFF", 2.5))

            # 2. Clips Ảnh
            success_img = 0
            for i, img_obj in enumerate(images[:max_images]):
                url = img_obj.get('url')
                desc = img_obj.get('description', '')
                logger.info(f"📸 Đang tải ảnh {i+1}: {url}")
                
                clip = self._image_clip(url, desc, 3.5)
                if clip:
                    clips.append(clip)
                    success_img += 1

            if success_img == 0:
                logger.error("❌ Không tải được ảnh nào từ internet.")
                return False

            # 3. Clip Giá & CTA
            clips.append(self._text_clip(f"Giá cực sốc: {price}đ\n{cta}", 65, "#FFD700", 3))

            final = concatenate_videoclips(clips).set_fps(self.template.fps)
            logger.info("🎬 Video clips đã được ghép nối thành công.")

            # Thêm nhạc nền nếu có
            if audio_path and os.path.exists(audio_path):
                try:
                    audio = AudioFileClip(audio_path).subclip(0, final.duration)
                    final = final.set_audio(audio)
                    logger.info(f"🎶 Thêm nhạc nền từ: {audio_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Lỗi thêm nhạc nền: {e}")

            final.write_videofile(output_path, codec="libx264", audio=True, logger=None, threads=4)
            final.close()
            self._cleanup()
            logger.info(f"✅ Render video thành công! File được lưu tại: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Render FAILED: {e}")
            return False

    def _image_clip(self, url, description, duration):
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://shopee.vn/"}
            r = requests.get(url, timeout=10, headers=headers)
            r.raise_for_status()

            img = Image.open(BytesIO(r.content)).convert("RGB")
            tw, th = self.template.width, self.template.height
            
            # Kiểm tra xem chiều cao và chiều rộng ảnh có hợp lệ không
            if not tw or not th:
                logger.warning(f"⚠️ Kích thước video không hợp lệ, sử dụng mặc định 1280x720")
                tw, th = 1280, 720  # Giá trị mặc định nếu không hợp lệ

            # Resize ảnh
            img.thumbnail((tw, th - 150), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (tw, th), (0, 0, 0))
            canvas.paste(img, ((tw - img.width)//2, (th - 150 - img.height)//2))

            # Vẽ mô tả lên ảnh nếu có
            if description:
                draw = ImageDraw.Draw(canvas)
                try: 
                    font = ImageFont.truetype("arial.ttf", 35)
                except: 
                    font = ImageFont.load_default()
                draw.text((tw//2, th - 80), description, fill="white", font=font, anchor="mm", align="center")

            path = self._save_temp(canvas)
            logger.info(f"📸 Ảnh đã được tải và xử lý thành công: {url}")
            return ImageClip(path, duration=duration)
        except Exception as e:
            logger.warning(f"⚠️ Lỗi tải ảnh: {url} - {e}")
            return None

    def _text_clip(self, text, size, color, duration):
        img = Image.new("RGB", (self.template.width, self.template.height), (20, 20, 20))
        draw = ImageDraw.Draw(img)
        try: 
            font = ImageFont.truetype("arial.ttf", size)
        except: 
            font = ImageFont.load_default()
        draw.text((self.template.width//2, self.template.height//2), text, fill=color, font=font, anchor="mm", align="center")
        path = self._save_temp(img)
        return ImageClip(path, duration=duration)

    def _save_temp(self, img):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(f.name, quality=90)
        self._temp_files.append(f.name)
        return f.name

    def _cleanup(self):
        for f in self._temp_files:
            try: 
                os.remove(f)
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi xóa file tạm: {f} - {e}")
        self._temp_files.clear()
