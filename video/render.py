import os
import tempfile
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import concatenate_videoclips, AudioFileClip, ImageClip, vfx
from gtts import gTTS
from .templates import TEMPLATE_DEFAULT
from utils.logger import get_logger
import textwrap

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
            images = processed_data.get("image_urls", [])  # Lấy trực tiếp list string
            title = processed_data.get("title", "Sản phẩm Hot")
            price = processed_data.get("price", "0")
            description = processed_data.get("description", "")

            logger.info(f"📝 Mô tả sản phẩm: {description}")

            if not description.strip():
                logger.warning("⚠️ Mô tả sản phẩm rỗng, dùng fallback.")
                description = "Sản phẩm này có các tính năng tuyệt vời mà bạn không thể bỏ qua!"

            if not images:
                logger.error("❌ Không có ảnh để render video!")
                return False

            # Phân đoạn mô tả thành các phần nhỏ
            description_parts = self.split_description(description)
            logger.info(f"📝 Phân đoạn mô tả thành {len(description_parts)} phần.")
            logger.info(f"🔹 Tổng ảnh nhận được: {len(images)}")

            clips = []

            # Clip tiêu đề
            title_clip = self._text_clip(title, 70, "#FFFFFF", 2.5, animation_type="fade_in")
            clips.append(title_clip)

            # Tạo các clip ảnh + mô tả
            success_img = 0
            for i, url in enumerate(images[:max_images]):
                desc = description_parts[i] if i < len(description_parts) else ""
                logger.info(f"📸 Đang tải ảnh {i + 1}: {url}")
                clip = self.render_image_clip(url, desc, 4)
                if clip:
                    clips.append(clip)
                    success_img += 1

            if success_img == 0:
                logger.error("❌ Không tải được ảnh nào từ internet.")
                return False

            # Tạo giọng đọc cho video (phân đoạn cho từng mô tả)
            voiceover_audio = None
            for part in description_parts:
                part_voiceover = self.create_voiceover(part)
                if part_voiceover:
                    if not voiceover_audio:
                        voiceover_audio = AudioFileClip(part_voiceover)
                    else:
                        voiceover_audio = concatenate_videoclips([voiceover_audio, AudioFileClip(part_voiceover)])

            # Đồng bộ thời gian audio với video
            video_duration = sum(c.duration for c in clips)
            audio_duration = voiceover_audio.duration if voiceover_audio else 0
            if voiceover_audio and audio_duration > video_duration:
                clips[-1] = clips[-1].set_duration(clips[-1].duration + (audio_duration - video_duration))

            # Kết hợp các clip
            final = concatenate_videoclips(clips)
            if voiceover_audio:
                final = final.set_audio(voiceover_audio)

            # Thêm nhạc nền nếu có
            if audio_path and os.path.exists(audio_path):
                audio_bg = AudioFileClip(audio_path).subclip(0, final.duration)
                final = final.set_audio(audio_bg)

            # Xuất video
            final.write_videofile(output_path, codec="libx264", audio=True, threads=4, fps=60)
            final.close()

            self._cleanup()  # Xóa các file tạm
            return True
        except Exception as e:
            logger.error(f"❌ Render FAILED: {e}")
            return False

    # -------------------------
    def split_description(self, description, max_length=150):
        """Phân đoạn mô tả sản phẩm thành các phần ngắn, tránh quá dài."""
        return textwrap.wrap(description, width=max_length)

    # -------------------------
    def render_image_clip(self, url, description, duration):
        """Render ảnh với mô tả và thời gian hợp lý."""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers)
            r.raise_for_status()

            img = Image.open(BytesIO(r.content)).convert("RGB")
            tw, th = self.template.width, self.template.height
            img.thumbnail((tw, th - 150), Image.Resampling.LANCZOS)

            canvas = Image.new("RGB", (tw, th), (0, 0, 0))
            canvas.paste(img, ((tw - img.width) // 2, (th - 150 - img.height) // 2))

            if description:
                draw = ImageDraw.Draw(canvas)
                try:
                    font = ImageFont.truetype("arial.ttf", 35)
                except:
                    font = ImageFont.load_default()
                draw.text((tw // 2, th - 80), description, fill="white", font=font, anchor="mm", align="center")

            path = self._save_temp(canvas)
            clip = ImageClip(path, duration=duration).fadein(0.5)
            return clip
        except Exception as e:
            logger.warning(f"⚠️ Lỗi tải ảnh: {url} - {e}")
            return None

    # -------------------------
    def create_voiceover(self, description, language='vi'):
        """Tạo giọng đọc cho từng phần mô tả."""
        try:
            tts = gTTS(description, lang=language)
            voiceover_path = tempfile.mktemp(suffix='.mp3')
            tts.save(voiceover_path)
            return voiceover_path
        except Exception as e:
            logger.error(f"❌ Lỗi khi tạo giọng đọc: {e}")
            return None

    # -------------------------
    def _text_clip(self, text, size, color, duration, animation_type="none"):
        img = Image.new("RGB", (self.template.width, self.template.height), (20, 20, 20))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        draw.text((self.template.width//2, self.template.height//2), text, fill=color, font=font, anchor="mm", align="center")
        clip = ImageClip(self._save_temp(img), duration=duration)
        if animation_type == "fade_in":
            clip = clip.fadein(0.5)
        elif animation_type == "fade_out":
            clip = clip.fadeout(0.5)
        elif animation_type == "slide_up":
            clip = clip.fx(vfx.scroll, 100, 0)
        return clip

    # -------------------------
    def _save_temp(self, img):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(f.name, quality=90)
        self._temp_files.append(f.name)
        return f.name

    # -------------------------
    def _ensure_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    # -------------------------
    def _cleanup(self):
        for f in self._temp_files:
            try:
                os.remove(f)
            except Exception as e:
                logger.warning(f"⚠️ Lỗi khi xóa file tạm: {f} - {e}")
