import os
import tempfile
import logging
import textwrap
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# =========================
# 1️⃣ SCRIPT GENERATOR
# =========================
class ScriptGenerator:
    def generate(self, title: str, description: str, price: str) -> List[str]:
        """Return 5-sentence script for video storytelling"""
        raise NotImplementedError

class HeuristicScriptGenerator(ScriptGenerator):
    """Fallback simple heuristic"""
    def generate(self, title: str, description: str, price: str):
        cta = f"Mua ngay hôm nay chỉ {price}!" if price else "Mua ngay!"
        return [
            f"Khám phá ngay: {title}",
            "Thoải mái, chất liệu co giãn, siêu nhẹ.",
            "Form ôm vừa vặn, tôn dáng nam tính.",
            "Thấm hút mồ hôi, tập luyện không giới hạn.",
            cta
        ]

# =========================
# 2️⃣ TTS PROVIDER
# =========================
class TTSProvider:
    def tts_to_file(self, text: str) -> Optional[str]:
        raise NotImplementedError

class GTTSProvider(TTSProvider):
    def tts_to_file(self, text: str) -> Optional[str]:
        try:
            from gtts import gTTS
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            gTTS(text=text, lang="vi").save(f.name)
            return f.name
        except Exception as e:
            logger.warning("gTTS failed: %s", e)
            return None

# =========================
# 3️⃣ VIDEO SCENE CREATOR
# =========================
class VideoScene:
    def __init__(self, width=720, height=1280):
        self.width = width
        self.height = height

    def make_scene(self, image_path: Optional[str], text: str) -> ImageClip:
        """Return a MoviePy ImageClip with overlaid text"""
        # 1. Prepare background
        canvas = Image.new("RGB", (self.width, self.height), (18, 18, 18))

        # 2. Paste product image
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path).convert("RGB")
                img.thumbnail((self.width-120, self.height-380))
                canvas.paste(img, ((self.width-img.width)//2, 120))
            except:
                pass

        # 3. Draw text
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 42)
        except:
            font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(text, 26))
        draw.rectangle((40, self.height-300, self.width-40, self.height-120), fill=(0,0,0,180))
        draw.multiline_text((self.width//2, self.height-210), wrapped, font=font, fill="white", anchor="mm", spacing=10)

        # 4. Save temp image
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        canvas.save(f.name, quality=90)
        return ImageClip(f.name)

# =========================
# 4️⃣ VIDEO RENDERER
# =========================
class SmartVideoRenderer:
    def __init__(self, width=720, height=1280, fps=24):
        self.width = width
        self.height = height
        self.fps = fps
        self.tts_provider = GTTSProvider()
        self.scene_creator = VideoScene(width, height)
        self.temp_files = []

    def render(self, title: str, description: str, price: str, images: List[str], output_path: str):
        # 1. Script
        sg = HeuristicScriptGenerator()
        script = sg.generate(title, description, price)
        logger.info("Generated script: %s", script)

        clips = []
        t_start = 0

        # 2. For each sentence → create scene + TTS
        for idx, sentence in enumerate(script):
            img_path = images[idx % len(images)] if images else None
            clip = self.scene_creator.make_scene(img_path, sentence)

            audio_file = self.tts_provider.tts_to_file(sentence)
            if audio_file and os.path.exists(audio_file):
                audio_clip = AudioFileClip(audio_file)
                duration = max(3.5, audio_clip.duration+0.2)
                clip = clip.set_audio(audio_clip.set_start(0)).set_duration(duration)
            else:
                duration = 3.5
                clip = clip.set_duration(duration)

            # motion effect: simple zoom/pan
            clip = clip.resize(lambda t: 1+0.02*t).set_position(lambda t: ("center", int(-10*t)))
            clips.append(clip.set_start(t_start))
            t_start += duration

        # 3. Compose video
        video = CompositeVideoClip(clips, size=(self.width, self.height))
        video.write_videofile(output_path, fps=self.fps, codec="libx264", audio_codec="aac", logger=None)

        # 4. Cleanup temp files
        self.cleanup()

    def cleanup(self):
        for f in self.temp_files:
            try: os.remove(f)
            except: pass
        self.temp_files.clear()
