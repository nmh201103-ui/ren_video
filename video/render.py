import os
import tempfile
import textwrap
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
)
import moviepy.video.fx.all as vfx

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

    def __init__(self, template=None):
        self.template = template or {"width": 720, "height": 1280, "fps": 24}
        self.temp_files = []
        self.tts = GTTSProvider()
        
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

    def render(self, data: dict, output_path: str, max_images=5):
        title = data.get("title", "")
        desc = data.get("description", "")
        price = data.get("price", "")
        images = data.get("image_urls", [])[:max_images]

        logger.info("🎤 Render video: %s", title)

        # Use AI to generate script instead of hardcoded rules
        script = self.script_gen.generate(title, desc, price)

        logger.info("📝 Script story: %s", script)

        clips, audios = [], []
        t = 0

        try:
            for idx, text in enumerate(script):
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

            video.write_videofile(
                output_path,
                fps=self.template["fps"],
                codec="libx264",
                audio_codec="aac",
                logger=None,
                preset="medium"
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

    def make_premium_scene(self, img_url, text, duration=4.0, scene_idx=0):
        """Create premium animated scene with blur overlay and smooth motion like veo3/sora."""
        img = self.load_image(img_url) or self.text_image(text)
        w, h = self.template["width"], self.template["height"]

        # Create blur background fill
        bg_img = img.copy().resize((w, h), Image.LANCZOS)
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))
        
        # Add dark overlay for better text contrast
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 120))
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
        y = (h - new_h) // 2 - 100  # Slightly up
        bg_img.paste(img_resized, (x, y))
        
        # Add gradient text box at bottom
        text_img = self._create_text_overlay(text, w, scene_idx)
        text_h = text_img.height
        bg_img.paste(text_img, (0, h - text_h), text_img.convert("RGBA"))
        
        # Save and create clip
        img_path = self.save_temp(bg_img)
        clip = ImageClip(img_path).set_duration(duration)
        
        # Premium motion effects based on scene
        if scene_idx == 0:  # Hook scene - dramatic zoom
            clip = clip.resize(lambda t: 1.15 - 0.1 * (t / duration))
        elif scene_idx == 1:  # Solution - gentle pan right
            clip = clip.set_position(lambda t: (int(-30 + 50 * (t / duration)), 'center'))
        elif scene_idx == 2:  # Benefit - slow zoom in
            clip = clip.resize(lambda t: 1 + 0.05 * (t / duration))
        else:  # CTA - pulse effect
            clip = clip.resize(lambda t: 1 + 0.02 * abs(t - duration/2) / (duration/2))
            
        # Smooth fade transitions
        clip = clip.fx(vfx.fadein, 0.3).fx(vfx.fadeout, 0.3)
        
        return clip

    def _create_text_overlay(self, text, width, scene_idx):
        """Create stylized text overlay with gradient background."""
        # Gradient colors by scene type
        colors = [
            (255, 87, 87, 200),   # Red for hook
            (74, 144, 226, 200),  # Blue for solution  
            (104, 201, 176, 200), # Green for benefit
            (255, 193, 7, 220)    # Yellow for CTA
        ]
        
        color = colors[scene_idx % len(colors)]
        height = 200
        
        # Create gradient background
        gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        for i in range(height):
            alpha = int(color[3] * (1 - i / height * 0.6))
            line_color = (*color[:3], alpha)
            gradient.paste(line_color, (0, i, width, i+1))
        
        draw = ImageDraw.Draw(gradient)
        
        # Load font
        try:
            font = ImageFont.truetype("arial.ttf", 42)
        except:
            try:
                font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 42) 
            except:
                font = ImageFont.load_default()
        
        # Word wrap and center text
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if draw.textbbox((0, 0), test_line, font=font)[2] < width - 60:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
        
        # Draw text centered
        y_offset = (height - len(lines) * 50) // 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_offset + i * 50
            
            # Text shadow
            draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 180))
            # Main text
            draw.text((x, y), line, font=font, fill="white")
            
        return gradient

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
