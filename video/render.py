import os
import tempfile
import textwrap
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
)

from utils.logger import get_logger
from video.ai_providers import GTTSProvider

logger = get_logger()


# ======================================================
# 1️⃣ EXTRACT Ý THẬT (KHÔNG LẤY BẢNG THÔNG SỐ)
# ======================================================

def extract_points(desc: str) -> dict:
    d = desc.lower()

    def has(*keys):
        return any(k in d for k in keys)

    return {
        "problem": "Tập gym mà áo bí mồ hôi là tụt sức liền.",
        "solution": "Áo gym ARISMAN co giãn mạnh, mặc cực kỳ thoải mái.",
        "material": "Vải siêu nhẹ, thấm hút mồ hôi nhanh, không bị lộ vết ướt."
        if has("thấm", "mồ hôi", "ultralight") else "",
        "fit": "Form ôm body, tay raglan giúp vai nhìn to và gọn hơn."
        if has("ôm", "raglan") else "",
        "cta": "Có đủ size từ M đến XXL, inbox shop để được tư vấn nhé!"
    }


# ======================================================
# 2️⃣ BIẾN Ý → STORY (SCRIPT NGƯỜI THẬT)
# ======================================================

def build_story_script(title: str, points: dict) -> list[str]:
    script = []

    # HOOK
    script.append(points["problem"])

    # SOLUTION
    script.append(points["solution"])

    # BENEFITS
    for k in ("material", "fit"):
        if points.get(k):
            script.append(points[k])

    # CTA
    script.append(points["cta"])

    return script[:5]


# ======================================================
# 3️⃣ RENDERER
# ======================================================

class SmartVideoRenderer:

    def __init__(self, template=None):
        self.template = template or {"width": 720, "height": 1280, "fps": 24}
        self.temp_files = []
        self.tts = GTTSProvider()

    # =========================
    # MAIN
    # =========================

    def render(self, data: dict, output_path: str, max_images=5):
        title = data.get("title", "")
        desc = data.get("description", "")
        images = data.get("image_urls", [])[:max_images]

        logger.info("🎬 Render video: %s", title)

        points = extract_points(desc)
        script = build_story_script(title, points)

        logger.info("📝 Script story: %s", script)

        clips, audios = [], []
        t = 0

        try:
            for idx, text in enumerate(script):
                img = images[idx % len(images)] if images else None

                clip = self.make_scene(img, text)
                audio_path = self.tts.tts_to_file(text)

                if audio_path and os.path.exists(audio_path):
                    audio = AudioFileClip(audio_path)
                    duration = max(3.5, audio.duration + 0.4)
                    audios.append(audio.set_start(t))
                else:
                    duration = 3.5

                clips.append(
                    clip.set_duration(duration).set_start(t)
                )
                t += duration

            video = CompositeVideoClip(
                clips,
                size=(self.template["width"], self.template["height"])
            )

            if audios:
                video.audio = CompositeAudioClip(audios)

            video.write_videofile(
                output_path,
                fps=self.template["fps"],
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

        except Exception as e:
            logger.exception("Render failed: %s", e)
            self.cleanup()
            return False

        self.cleanup()
        return True

    # =========================
    # SCENE
    # =========================

    def make_scene(self, img_url, text):
        img = self.load_image(img_url) or self.text_image(text)

        w, h = self.template["width"], self.template["height"]
        canvas = Image.new("RGB", (w, h), (18, 18, 18))

        img.thumbnail((w - 120, h - 380))
        canvas.paste(img, ((w - img.width) // 2, 120))

        draw = ImageDraw.Draw(canvas)
        font = self.load_font(42)

        wrapped = "\n".join(textwrap.wrap(text, 26))
        draw.rectangle((40, h - 300, w - 40, h - 120), fill=(0, 0, 0))
        draw.multiline_text(
            (w // 2, h - 210),
            wrapped,
            font=font,
            fill="white",
            anchor="mm",
            spacing=10
        )

        path = self.save_temp(canvas)
        return ImageClip(path)

    # =========================
    # IMAGE
    # =========================

    def load_image(self, url):
        try:
            r = requests.get(url, timeout=10)
            return Image.open(BytesIO(r.content)).convert("RGB")
        except:
            return None

    def text_image(self, text):
        w, h = self.template["width"], self.template["height"]
        img = Image.new("RGB", (w, h), (30, 30, 30))
        draw = ImageDraw.Draw(img)
        font = self.load_font(50)
        wrapped = "\n".join(textwrap.wrap(text, 22))
        draw.multiline_text((w // 2, h // 2), wrapped, font=font, fill="white", anchor="mm")
        return img

    # =========================
    # UTILS
    # =========================

    def load_font(self, size):
        try:
            return ImageFont.truetype("fonts/Roboto-Bold.ttf", size)
        except:
            return ImageFont.load_default()

    def save_temp(self, img):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(f.name, quality=90)
        self.temp_files.append(f.name)
        return f.name

    def cleanup(self):
        for f in self.temp_files:
            try:
                os.remove(f)
            except:
                pass
        self.temp_files.clear()
