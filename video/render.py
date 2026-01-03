import os
import tempfile
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import concatenate_videoclips, AudioFileClip, ImageClip
from gtts import gTTS
from .templates import TEMPLATE_DEFAULT
from utils.logger import get_logger

logger = get_logger()

class VideoRenderer:
    def __init__(self, template=None):
        self.template = template or TEMPLATE_DEFAULT
        self._temp_files = []

    def render(self, processed_data: dict, output_path: str, max_images: int = 5, audio_path: str = None) -> bool:
        try:
            # Đảm bảo thư mục output tồn tại
            self._ensure_directory(os.path.dirname(output_path))

            # Lấy dữ liệu từ processed_data
            images = processed_data.get("image_data", [])
            title = processed_data.get("title", "Sản phẩm Hot")
            price = processed_data.get("price", "0")
            cta = processed_data.get("cta_text", "Mua ngay!")

            # Kiểm tra nếu không có ảnh
            if not images:
                logger.warning("⚠️ Không có dữ liệu ảnh.")
                images = []

            # Kiểm tra các trường cần thiết
            if not title:
                title = "Sản phẩm Hot"
            
            if not price or price == "None":
                price = "0"
            
            if not cta:
                cta = "Mua ngay!"
            
            logger.info(f"🚀 Renderer bắt đầu với {len(images)} ảnh.")

            if not images:
                logger.error("❌ Không có dữ liệu ảnh để render!")
                return False

            clips = []
            # 1. Clip Tiêu đề
            clips.append(self._text_clip(title, 70, "#FFFFFF", 2.5))

            # 2. Clips Ảnh (Thêm hiệu ứng giật giật)
            success_img = 0
            for i, img_obj in enumerate(images[:max_images]):
                url = img_obj.get('url')
                desc = img_obj.get('description', '')
                logger.info(f"📸 Đang tải ảnh {i+1}: {url}")
                
                clip = self._image_clip(url, desc, 0.7)  # Tốc độ thấp để tạo hiệu ứng "giật giật"
                if clip:
                    clips.append(clip)
                    success_img += 1

            if success_img == 0:
                logger.error("❌ Không tải được ảnh nào từ internet.")
                return False

            # 3. Clip Giá & CTA
            clips.append(self._text_clip(f"Giá cực sốc: {price}đ\n{cta}", 65, "#FFD700", 3))

            # Kết hợp tất cả các clip
            final = concatenate_videoclips(clips).set_fps(self.template.fps)

            # Thêm giọng đọc vào video
            voiceover_path = self._generate_voiceover(title, price, cta)
            audio = AudioFileClip(voiceover_path)
            final = final.set_audio(audio)

            # Thêm nhạc nền nếu có
            if audio_path and os.path.exists(audio_path):
                audio = AudioFileClip(audio_path).subclip(0, final.duration)
                final = final.set_audio(audio)

            # Xuất video
            final.write_videofile(output_path, codec="libx264", audio=True, logger=None, threads=4)
            final.close()

            self._cleanup()  # Xóa các file tạm
            return True
        except Exception as e:
            logger.error(f"❌ Render FAILED: {e}")
            return False

    def _generate_voiceover(self, title, price, cta):
        """Tạo giọng đọc cho video"""
        try:
            text = f"Sản phẩm: {title}. Giá: {price}. {cta}"
            tts = gTTS(text, lang='vi')
            voiceover_path = tempfile.mktemp(suffix='.mp3')
            tts.save(voiceover_path)
            logger.info(f"🎙️ Giọng đọc được tạo thành công: {voiceover_path}")
            return voiceover_path
        except Exception as e:
            logger.error(f"❌ Lỗi khi tạo giọng đọc: {e}")
            return None

    def _image_clip(self, url, description, duration):
        """Tạo clip từ ảnh với hiệu ứng giật giật"""
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://shopee.vn/"}
            r = requests.get(url, timeout=10, headers=headers)
            r.raise_for_status()

            img = Image.open(BytesIO(r.content)).convert("RGB")
            tw, th = self.template.width, self.template.height

            # Thêm hiệu ứng giật giật: thay đổi tốc độ mỗi ảnh
            img.thumbnail((tw, th - 150), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (tw, th), (0, 0, 0))
            canvas.paste(img, ((tw - img.width)//2, (th - 150 - img.height)//2))

            if description:
                draw = ImageDraw.Draw(canvas)
                try: font = ImageFont.truetype("arial.ttf", 35)
                except: font = ImageFont.load_default()
                draw.text((tw//2, th - 80), description, fill="white", font=font, anchor="mm", align="center")

            path = self._save_temp(canvas)
            return ImageClip(path, duration=duration)
        except Exception as e:
            logger.warning(f"⚠️ Lỗi tải ảnh: {url} - {e}")
            return None

    def _text_clip(self, text, size, color, duration):
        """Tạo clip văn bản"""
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
        """Lưu ảnh tạm"""
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(f.name, quality=90)
        self._temp_files.append(f.name)
        return f.name

    def _ensure_directory(self, directory):
        """Đảm bảo thư mục tồn tại"""
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _cleanup(self):
        """Xóa các file tạm"""
        for f in self._temp_files:
            try: 
                os.remove(f)
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi xóa file tạm: {f} - {e}")
        self._temp_files.clear()
