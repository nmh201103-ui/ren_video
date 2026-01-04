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
            images = processed_data.get("image_data", [])
            title = processed_data.get("title", "Sản phẩm Hot")
            price = processed_data.get("price", "0")
            cta = processed_data.get("cta_text", "Mua ngay!")
            description = processed_data.get("description", "")

            # Log mô tả sản phẩm để kiểm tra
            logger.info(f"📝 Mô tả sản phẩm: {description}")

            if not description:
                logger.warning("⚠️ Mô tả sản phẩm không có hoặc không được lấy.")
                description = "Sản phẩm này có các tính năng tuyệt vời mà bạn không thể bỏ qua!"

            # Phân đoạn mô tả thành các phần nhỏ hơn
            description_parts = self.split_description(description)

            logger.info(f"📝 Phân đoạn mô tả thành {len(description_parts)} phần.")

            # Kiểm tra các trường cần thiết
            if not images:
                logger.warning("⚠️ Không có dữ liệu ảnh.")
                images = []

            logger.info(f"🚀 Renderer bắt đầu với {len(images)} ảnh.")

            if not images:
                logger.error("❌ Không có dữ liệu ảnh để render!")
                return False

            clips = []
            # 1. Clip Tiêu đề với hiệu ứng fade-in
            title_clip = self._text_clip(title, 70, "#FFFFFF", 2.5, animation_type="fade_in")
            clips.append(title_clip)

            # 2. Tạo các clips hình ảnh và mô tả
            total_duration = 0  # Tổng thời gian cho video
            success_img = 0

            for i, img_obj in enumerate(images[:max_images]):
                url = img_obj.get('url')
                description = description_parts[i] if i < len(description_parts) else ""
                logger.info(f"📸 Đang tải ảnh {i + 1}: {url}")

                # Tạo clip ảnh với mô tả
                clip = self.render_image_clip(url, description, 4)  # Điều chỉnh thời gian cho phù hợp
                if clip:
                    clips.append(clip)
                    total_duration += 4
                    success_img += 1

            if success_img == 0:
                logger.error("❌ Không tải được ảnh nào từ internet.")
                return False

            # 3. Giọng đọc cho video (phân đoạn cho từng mô tả)
            voiceover_audio = None
            for part in description_parts:
                part_voiceover = self.create_voiceover(part)
                if part_voiceover:
                    if not voiceover_audio:
                        voiceover_audio = AudioFileClip(part_voiceover)
                    else:
                        voiceover_audio = concatenate_videoclips([voiceover_audio, AudioFileClip(part_voiceover)])

            # Cập nhật thời gian giọng đọc
            if voiceover_audio:
                audio_duration = voiceover_audio.duration
            video_duration = sum(c.duration for c in clips)

            if audio_duration > video_duration:
                # Kéo dài clip cuối
                diff = audio_duration - video_duration
                clips[-1] = clips[-1].set_duration(clips[-1].duration + diff)


            # 4. Kết hợp các clip
            final = concatenate_videoclips(clips).set_audio(voiceover_audio)

            # Thêm nhạc nền nếu có
            if audio_path and os.path.exists(audio_path):
                audio = AudioFileClip(audio_path).subclip(0, final.duration)
                final = final.set_audio(audio)

            # Xuất video với FPS 60
            final.write_videofile(output_path, codec="libx264", audio=True, threads=4, fps=60)
            final.close()

            self._cleanup()  # Xóa các file tạm
            return True
        except Exception as e:
            logger.error(f"❌ Render FAILED: {e}")
            return False

    def split_description(self, description, max_length=150):
        """Phân đoạn mô tả sản phẩm thành các phần ngắn, tránh quá dài."""
        return textwrap.wrap(description, width=max_length)

    def render_image_clip(self, url, description, duration):
        """Render ảnh với mô tả và thời gian hợp lý để tương thích với giọng đọc."""
        try:
            # Tải ảnh từ URL
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers)
            r.raise_for_status()

            img = Image.open(BytesIO(r.content)).convert("RGB")
            tw, th = self.template.width, self.template.height
            img.thumbnail((tw, th - 150), Image.Resampling.LANCZOS)

            # Tạo nền và chèn ảnh vào
            canvas = Image.new("RGB", (tw, th), (0, 0, 0))
            canvas.paste(img, ((tw - img.width) // 2, (th - 150 - img.height) // 2))

            # Chèn mô tả vào dưới ảnh
            if description:
                draw = ImageDraw.Draw(canvas)
                font = ImageFont.truetype("arial.ttf", 35)
                draw.text((tw // 2, th - 80), description, fill="white", font=font, anchor="mm", align="center")

            path = self._save_temp(canvas)
            clip = ImageClip(path, duration=duration)
            return clip.fadein(0.5)  # Đảm bảo các clip này chuyển động mượt mà hơn
        except Exception as e:
            logger.warning(f"⚠️ Lỗi tải ảnh: {url} - {e}")
            return None

    def create_voiceover(self, description, language='vi'):
        """Tạo giọng đọc cho từng phần mô tả sản phẩm."""
        try:
            tts = gTTS(description, lang=language)
            voiceover_path = tempfile.mktemp(suffix='.mp3')
            tts.save(voiceover_path)
            return voiceover_path
        except Exception as e:
            logger.error(f"❌ Lỗi khi tạo giọng đọc: {e}")
            return None

    def _text_clip(self, text, size, color, duration, animation_type="none"):
        """Tạo clip văn bản với các hiệu ứng"""
        img = Image.new("RGB", (self.template.width, self.template.height), (20, 20, 20))
        draw = ImageDraw.Draw(img)

        # Chọn font chữ phù hợp
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()

        # Chèn text vào giữa ảnh
        draw.text((self.template.width//2, self.template.height//2), text, fill=color, font=font, anchor="mm", align="center")

        # Tạo clip từ ảnh với text
        text_clip = ImageClip(self._save_temp(img), duration=duration)

        # Thêm hiệu ứng di chuyển cho văn bản
        if animation_type == "fade_in":
            text_clip = text_clip.fadein(0.5)
        elif animation_type == "fade_out":
            text_clip = text_clip.fadeout(0.5)
        elif animation_type == "slide_up":
            text_clip = text_clip.fx(vfx.scroll, 100, 0)  # Text di chuyển từ dưới lên

        return text_clip

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
       
