import os
import tempfile
import requests
import textwrap
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    CompositeAudioClip,
    CompositeVideoClip
)
from gtts import gTTS
from .templates import TEMPLATE_DEFAULT
from utils.logger import get_logger

logger = get_logger()

class VideoRenderer:
    def __init__(self, template=None):
        self.template = template or TEMPLATE_DEFAULT
        self._temp_files = []

    def render(self, processed_data: dict, output_path: str, max_images: int = 10, audio_path: str = None) -> bool:
        try:
            self._ensure_directory(os.path.dirname(output_path))

            # ================== 1. INPUT ==================
            images = processed_data.get("image_urls", [])
            title = str(processed_data.get("title", "Sản phẩm Hot"))

            raw_description = str(processed_data.get("description") or "").strip()

            print("\n" + "🧪" * 15)
            print(f"RENDERER DEBUG: Nhận được {len(raw_description)} ký tự mô tả (RAW).")
            print("🧪" * 15 + "\n")

            # ================== 2. CLEAN AN TOÀN ==================
            description = raw_description

            # Xóa hashtag
            description = re.sub(r'#\w+', '', description)

            # ⚠️ CHỈ CẮT CAM KẾT NẾU NÓ NẰM SÂU (tránh mất hết nội dung)
            for bad in ["Cửa hàng cam kết", "Cam kết mua sắm"]:
                idx = description.find(bad)
                if idx != -1 and idx > 200:
                    description = description[:idx]

            # Dọn ký tự trang trí
            description = description.replace('*', '').replace('+', '').replace('-', ' ')
            description = re.sub(r'\s+', ' ', description).strip()

            # FAIL-SAFE: nếu clean xong mà rỗng → dùng bản gốc
            if len(description) < 50:
                logger.warning("⚠️ Clean quá tay → dùng lại mô tả gốc")
                description = raw_description[:1000]

            logger.debug(f"CLEAN CHECK: after clean = {len(description)} ký tự")

            # ================== 3. TÁCH CÂU ==================
            raw_chunks = re.split(r'[\n.:;!?•]', description)
            sentences = [s.strip() for s in raw_chunks if len(s.strip()) > 10]

            if len(sentences) < 5:
                logger.info("⚠️ Văn bản đặc → chia theo độ dài")
                sentences = textwrap.wrap(description, width=80, break_long_words=False)

            if not sentences:
                sentences = [
                    title,
                    "Sản phẩm chất lượng cao",
                    "Thiết kế thời trang",
                    "Mua ngay tại giỏ hàng"
                ]

            logger.info(f"🎬 Sẵn sàng Render: {len(images[:max_images])} ảnh | {len(sentences)} câu thoại.")

            # ================== 4. BUILD VIDEO ==================
            clips = []
            audio_segments = []
            current_time = 0

            # INTRO
            intro = self._text_clip(title, 55, "#FFD700", 2.5)
            clips.append(intro.set_start(0))
            current_time += 2.5

            # IMAGE + VOICE LOOP
            for i, url in enumerate(images[:max_images]):
                text = sentences[i % len(sentences)]

                voice_path = self.create_voiceover(text)
                if not voice_path:
                    continue

                audio = AudioFileClip(voice_path)
                duration = max(audio.duration + 0.5, 3.0)

                img_clip = self.render_image_clip(url, text, duration)
                if img_clip:
                    clips.append(img_clip.set_start(current_time))
                    audio_segments.append(audio.set_start(current_time))
                    current_time += duration
                    print(f"   + Clip {i+1}: {text[:40]}...")

            # ================== 5. MIX ==================
            final_video = CompositeVideoClip(clips, size=(self.template.width, self.template.height))
            voice_audio = CompositeAudioClip(audio_segments)

            if audio_path and os.path.exists(audio_path):
                bg = AudioFileClip(audio_path).volumex(0.1).set_duration(current_time)
                final_video = final_video.set_audio(CompositeAudioClip([voice_audio, bg]))
            else:
                final_video = final_video.set_audio(voice_audio)

            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=24,
                threads=4,
                logger=None
            )

            final_video.close()
            self._cleanup()
            return True

        except Exception as e:
            logger.error(f"❌ Render Error: {e}")
            return False

    # ================== HELPERS ==================

    def render_image_clip(self, url, description, duration):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            img = Image.open(BytesIO(r.content)).convert("RGB")

            tw, th = self.template.width, self.template.height
            canvas = Image.new("RGB", (tw, th), (10, 10, 10))

            img.thumbnail((tw - 60, th - 550), Image.Resampling.LANCZOS)
            canvas.paste(img, ((tw - img.width) // 2, 150))

            if description:
                draw = ImageDraw.Draw(canvas)
                try:
                    font = ImageFont.truetype("arial.ttf", 38)
                except:
                    font = ImageFont.load_default()

                wrapped = "\n".join(textwrap.wrap(description, width=32))
                bbox = draw.multiline_textbbox((tw // 2, th - 300), wrapped, font=font, anchor="mm")
                pad = 20

                draw.rectangle(
                    [bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad],
                    fill=(0, 0, 0, 180)
                )

                draw.multiline_text(
                    (tw // 2, th - 300),
                    wrapped,
                    fill="white",
                    font=font,
                    anchor="mm",
                    align="center",
                    spacing=10
                )

            path = self._save_temp(canvas)
            return ImageClip(path, duration=duration).fadein(0.3)

        except Exception as e:
            logger.warning(f"⚠️ Render ảnh lỗi: {e}")
            return None

    def create_voiceover(self, text):
        try:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            gTTS(text=text, lang="vi").save(f.name)
            self._temp_files.append(f.name)
            return f.name
        except:
            return None

    def _text_clip(self, text, size, color, duration):
        tw, th = self.template.width, self.template.height
        img = Image.new("RGB", (tw, th), (15, 15, 15))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()

        wrapped = "\n".join(textwrap.wrap(text, width=22))
        draw.multiline_text((tw // 2, th // 2), wrapped, fill=color, font=font, anchor="mm", align="center")

        path = self._save_temp(img)
        return ImageClip(path, duration=duration).fadein(0.5).fadeout(0.5)

    def _save_temp(self, img):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(f.name, quality=90)
        self._temp_files.append(f.name)
        return f.name

    def _ensure_directory(self, directory):
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def _cleanup(self):
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        self._temp_files = []
