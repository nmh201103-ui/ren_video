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
from video.did_avatar import DIDTalkingAvatar
from video.wav2lip_avatar import Wav2LipAvatar

try:
    from rembg import remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

logger = get_logger()
# ======================================================
# Fix MoviePy + Pillow 10+ compatibility
# ======================================================
if not hasattr(Image, "ANTIALIAS") and hasattr(Image, "Resampling"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

class SmartVideoRenderer:

    def __init__(self, template=None, video_mode="simple", use_ai_avatar=False, avatar_backend="wav2lip"):
        # HIGH QUALITY: 1080p @ 30fps cho TikTok/Shorts (giống Sora/Veo)
        self.template = template or {"width": 1080, "height": 1920, "fps": 30}
        self.temp_files = []
        self.tts = GTTSProvider()
        self.video_mode = video_mode  # "simple", "demo"
        self.person_image_path = None  # For demo mode
        self.use_ai_avatar = use_ai_avatar  # Enable AI talking avatar
        self.avatar_backend = avatar_backend  # "wav2lip" (free local) or "did" (paid)
        
        # Initialize avatar generator based on backend
        if use_ai_avatar:
            if avatar_backend == "wav2lip":
                self.avatar_gen = Wav2LipAvatar()
                logger.info("Using FREE Wav2Lip (local) backend")
            elif avatar_backend == "did":
                self.avatar_gen = DIDTalkingAvatar()
                logger.info("Using D-ID API backend (paid)")
            else:
                logger.warning("Unknown avatar backend: %s", avatar_backend)
                self.avatar_gen = None
        else:
            self.avatar_gen = None
        
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

                # AI AVATAR MODE: Tạo talking avatar video từ ảnh + audio
                if self.use_ai_avatar and self.person_image_path and audio_path:
                    avatar_video_path = self._create_avatar_scene(
                        self.person_image_path, 
                        audio_path, 
                        idx,
                        progress_callback
                    )
                    if avatar_video_path:
                        # Use avatar video instead of static image
                        clip = VideoFileClip(avatar_video_path)
                        clip = clip.set_duration(duration)
                        logger.info("✅ Using AI avatar video for scene %d", idx)
                    else:
                        # Fallback to static scene
                        logger.warning("⚠️ Avatar failed, using static scene")
                        clip = self.make_premium_scene(img, text, duration, idx)
                else:
                    # Normal static scene
                    clip = self.make_premium_scene(img, text, duration, idx)
                
                clips.append(clip.set_start(t))
                t += duration

            video = CompositeVideoClip(
                clips,
                size=(self.template["width"], self.template["height"])
            )

            if audios:
                video.audio = CompositeAudioClip(audios)
            
            if progress_callback:
                progress_callback("Encoding video...", 85)

            # HIGH QUALITY ENCODING: Chất lượng cao như Sora/Veo
            video.write_videofile(
                output_path,
                fps=self.template["fps"],
                codec="libx264",
                audio_codec="aac",
                bitrate="8000k",  # 8 Mbps cho 1080p - chất lượng cao
                audio_bitrate="320k",  # AAC 320kbps - audio HD
                preset="slow",  # Slow preset = chất lượng tốt hơn (trade-off: render lâu hơn)
                ffmpeg_params=[
                    "-crf", "18",  # CRF 18 = near-lossless quality (18-23 là sweet spot)
                    "-pix_fmt", "yuv420p",  # Color space tương thích TikTok/YouTube
                    "-profile:v", "high",  # H.264 High Profile cho chất lượng tốt
                    "-level", "4.2",
                    "-movflags", "+faststart"  # Web optimization
                ],
                logger=None
            )
            
            if progress_callback:
                progress_callback("Video complete!", 100)

        except Exception as e:
            logger.exception("Render failed: %s", e)
            self.cleanup()
            return False

        self.cleanup()
        return True

    def _create_avatar_scene(self, image_path, audio_path, scene_idx, progress_callback=None):
        """Create AI talking avatar video using Wav2Lip/D-ID"""
        try:
            if not self.avatar_gen:
                logger.warning("⚠️ Avatar generator not initialized")
                return None
            
            if progress_callback:
                if self.avatar_backend == "wav2lip":
                    backend_name = "Wav2Lip (FREE-LOCAL)"
                else:
                    backend_name = "D-ID (PAID)"
                progress_callback(f"🤖 Creating AI avatar ({backend_name}) for scene {scene_idx+1}...", None)
            
            # Output path for avatar video
            output_path = f"assets/temp/avatar_scene_{scene_idx}.mp4"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate talking avatar with retry
            success = self.avatar_gen.create_talking_video(
                image_path=image_path,
                audio_path=audio_path,
                output_path=output_path,
                max_wait=180,  # Longer timeout for Colab
                retry_count=1  # Only retry once to avoid long waits
            )
            
            if success and os.path.exists(output_path):
                self.temp_files.append(output_path)  # Track for cleanup
                return output_path
            return None
            
        except Exception as e:
            logger.error("Failed to create avatar scene: %s", e)
            return None

    # =========================
    # SCENE
    # =========================

    def make_premium_scene(self, img_url, text, duration=4.0, scene_idx=0):
        """Create simple scene with image. Audio only, no text overlay."""
        img = self.load_image(img_url) or self.text_image(text)
        w, h = self.template["width"], self.template["height"]
        
        # REVIEWER MODE: Remove background from product image for cleaner look
        if self.video_mode == "reviewer" and img and HAS_REMBG:
            try:
                img = self._remove_background(img)
                logger.info(f"✅ Background removed for reviewer scene {scene_idx}")
            except Exception as e:
                logger.warning(f"⚠️ Background removal failed: {e}, using original image")
        
        # DEMO MODE: Disabled - method not implemented
        # if self.video_mode == "demo":
        #     img = self.get_person_holding_image(img)
        #     logger.info(f"🤝 Applied DEMO MODE: person holding product in scene {scene_idx}")

        # REVIEWER MODE: Add talking avatar in corner
        if self.video_mode == "reviewer" and self.person_image_path:
            img = self._add_reviewer_avatar(img, self.person_image_path)
            logger.info(f"🎙️ Applied REVIEWER MODE: added avatar to scene {scene_idx}")

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

    def _add_reviewer_avatar(self, product_img, person_path):
        """Add reviewer avatar to bottom-right corner for reviewer mode."""
        try:
            # Load person image
            if person_path.startswith("http"):
                person_img = self.load_image(person_path)
            else:
                person_img = Image.open(person_path).convert("RGB")
            
            if not person_img:
                return product_img
            
            # Create composite with person in circular frame at bottom right
            w, h = product_img.size
            avatar_size = min(w // 4, h // 4, 200)  # 25% of image or max 200px
            
            # Resize and crop person to square
            person_aspect = person_img.width / person_img.height
            if person_aspect > 1:
                new_h = avatar_size
                new_w = int(new_h * person_aspect)
            else:
                new_w = avatar_size
                new_h = int(new_w / person_aspect)
            
            person_resized = person_img.resize((new_w, new_h), Image.LANCZOS)
            
            # Crop to center square
            left = (new_w - avatar_size) // 2
            top = (new_h - avatar_size) // 2
            person_square = person_resized.crop((left, top, left + avatar_size, top + avatar_size))
            
            # Create circular mask
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            # Apply mask to person image
            person_circle = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
            person_circle.paste(person_square, (0, 0))
            person_circle.putalpha(mask)
            
            # Add white border
            border_size = 5
            bordered = Image.new('RGBA', (avatar_size + border_size*2, avatar_size + border_size*2), (255, 255, 255, 255))
            bordered.paste(person_circle, (border_size, border_size), person_circle)
            
            # Paste onto product image (bottom right corner)
            result = product_img.convert('RGBA')
            padding = 20
            x = w - bordered.width - padding
            y = h - bordered.height - padding
            result.paste(bordered, (x, y), bordered)
            
            return result.convert('RGB')
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to add reviewer avatar: {e}")
            return product_img

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Remove background from product image using rembg AI."""
        if not HAS_REMBG:
            return img
        
        try:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Remove background using rembg
            img_no_bg = remove(img)
            
            return img_no_bg
            
        except Exception as e:
            logger.warning(f"⚠️ Background removal failed: {e}")
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
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        # PNG lossless thay vì JPEG quality 90 → không mất chi tiết
        img.save(f.name, format="PNG", optimize=True)
        self.temp_files.append(f.name)
        return f.name

    def cleanup(self):
        for f in self.temp_files:
            try:
                os.remove(f)
            except:
                pass
        self.temp_files.clear()
