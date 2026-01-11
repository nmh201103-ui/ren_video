import os
import tempfile
import textwrap
from io import BytesIO
import random
import math

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    CompositeAudioClip,
    vfx,
)

from utils.logger import get_logger
from video.ai_providers import (
    GTTSProvider, 
    HeuristicScriptGenerator, 
    OllamaScriptGenerator, 
    OpenAIScriptGenerator
)

logger = get_logger()
# ======================================================
# Fix MoviePy + Pillow 10+ compatibility
# ======================================================
if not hasattr(Image, "ANTIALIAS") and hasattr(Image, "Resampling"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

class SmartVideoRenderer:

    def __init__(self, template=None, video_mode="reviewer"):
        self.template = template or {"width": 720, "height": 1280, "fps": 24}
        self.temp_files = []
        self.tts = GTTSProvider()
        self.video_mode = video_mode  # "simple", "reviewer", "demo"
        self.person_image_path = None  # For demo mode
        self.reviewer_avatar = None  # Cache reviewer avatar
        
        # Initialize script generator based on env
        provider = os.getenv("LLM_PROVIDER", "default").lower()
        if provider == "openai" and os.getenv("OPENAI_API_KEY"):
            self.script_gen = OpenAIScriptGenerator(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            )
            logger.info("Using OpenAI script generator")
        elif provider == "ollama" or (not os.getenv("OPENAI_API_KEY") and self._has_ollama()):
            self.script_gen = OllamaScriptGenerator(
                model=os.getenv("OLLAMA_MODEL", "gemma3:4b")
            )
            logger.info("Using Ollama script generator")
        else:
            self.script_gen = HeuristicScriptGenerator()
            logger.info("Using Heuristic script generator")

    def _has_ollama(self):
        try:
            import subprocess
            subprocess.run(["ollama", "--version"], capture_output=True, check=True)
            return True
        except:
            return False

    # =========================
    # MAIN
    # =========================

    def render(self, data: dict, output_path: str, max_images=5, progress_callback=None):
        title = data.get("title", "")
        desc = data.get("description", "")
        price = data.get("price", "")
        images = data.get("image_urls", [])[:max_images]

        logger.info("🎤 Render video: %s", title)
        logger.info("📸 Images available: %d", len(images))
        if not images:
            logger.warning("⚠️ No images! Will use text slides instead")
        
        if progress_callback:
            progress_callback("Generating script...", 10)

        # Capture optional person image for demo mode
        self.person_image_path = data.get("person_image_path")

        # Use AI to generate script instead of hardcoded rules
        script = self.script_gen.generate(title, desc, price)

        logger.info("📝 Script story: %s", script)
        
        if progress_callback:
            progress_callback(f"Creating {len(script)} scenes...", 20)

        clips, audios = [], []
        t = 0

        try:
            for idx, text in enumerate(script):
                if progress_callback:
                    progress = 20 + (idx + 1) * 60 // len(script)
                    progress_callback(f"Scene {idx+1}/{len(script)}: {text[:50]}...", progress)
                    
                img = images[idx % len(images)] if images else None

                # generate audio first to decide scene duration
                audio_path = self.tts.tts_to_file(text)

                if audio_path and os.path.exists(audio_path):
                    audio = AudioFileClip(audio_path)
                    duration = max(4.0, audio.duration + 0.5)  # Longer scenes
                    audios.append(audio.set_start(t))
                else:
                    duration = 4.0

                # create premium animated scene
                clip = self.make_premium_scene(img, text, duration, idx)
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
            
            if progress_callback:
                progress_callback("Encoding video...", 85)

            video.write_videofile(
                output_path,
                fps=self.template["fps"],
                codec="libx264",
                audio_codec="aac",
                logger=None,
                preset="medium"
            )
            
            if progress_callback:
                progress_callback("Video complete!", 100)

        except Exception as e:
            logger.exception("Render failed: %s", e)
            self.cleanup()
            return False

        self.cleanup()
        return True

    # =========================
    # SCENE
    # =========================

    def make_premium_scene(self, img_url, text, duration=4.0, scene_idx=0):
        """Create simple scene with image. Audio only, no text overlay."""
        img = self.load_image(img_url) or self.text_image(text)
        w, h = self.template["width"], self.template["height"]
        
        # DEMO MODE: Create person holding product for all scenes
        if self.video_mode == "demo":
            img = self.get_person_holding_image(img)
            logger.info(f"🤝 Applied DEMO MODE: person holding product in scene {scene_idx}")

        # Create blur background fill
        bg_img = img.copy().resize((w, h), Image.LANCZOS)
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))
        
        # Add overlay
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
        bg_img = Image.alpha_composite(bg_img.convert("RGBA"), overlay).convert("RGB")
        
        # Main product image (centered, aspect preserved)
        img_aspect = img.width / img.height
        if img_aspect > (w/h):  # Wide image
            new_w = int(w * 0.8)
            new_h = int(new_w / img_aspect)
        else:  # Tall image  
            new_h = int(h * 0.6)
            new_w = int(new_h * img_aspect)
        
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Paste product on background
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        bg_img.paste(img_resized, (x, y))
        
        # Save and create clip - STATIC IMAGE (no text, no zoom)
        img_path = self.save_temp(bg_img)
        clip = ImageClip(img_path).set_duration(duration)
        
        # Only fade in/out - no zoom, no pan, no motion
        clip = clip.fx(vfx.fadein, 0.3).fx(vfx.fadeout, 0.3)
        
        return clip

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
