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
    OpenAIScriptGenerator,
    MovieScriptGenerator
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

    def __init__(self, template=None, video_mode="simple", use_ai_avatar=False, avatar_backend="wav2lip", content_type="product"):
        # HIGH QUALITY: 1080p @ 30fps cho TikTok/Shorts (giống Sora/Veo)
        self.template = template or {"width": 1080, "height": 1920, "fps": 30}
        self.temp_files = []
        self.tts = GTTSProvider()
        self.video_mode = video_mode  # "simple", "demo"
        self.person_image_path = None  # For demo mode
        self.use_ai_avatar = use_ai_avatar  # Enable AI talking avatar
        self.avatar_backend = avatar_backend  # "wav2lip" (free local) or "did" (paid)
        self.content_type = content_type  # "product" or "movie"
        
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
        
        # Initialize script generator based on content type + env
        if content_type == "story":
            # Story generator handles narrative
            from video.story_generator import StoryScriptGenerator
            self.script_gen = StoryScriptGenerator()
            logger.info("Using Story script generator")
        elif content_type == "movie":
            # Use MovieScriptGenerator for movie reviews
            use_llm = os.getenv("OPENAI_API_KEY") is not None
            self.script_gen = MovieScriptGenerator(
                use_llm=use_llm,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            logger.info("Using Movie script generator")
        elif content_type == "video":
            # Video scene render uses pre-generated script; keep a lightweight fallback
            self.script_gen = HeuristicScriptGenerator()
            logger.info("Using heuristic script generator (video mode fallback)")
        else:
            # Use product script generator
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

    def render(self, data: dict, output_path: str, max_images=None, target_duration=None, progress_callback=None):
        """
        Render video to file
        Args:
            data: Content data (title, description, etc.)
            output_path: Where to save video
            max_images: Max product images to use (None = use all available)
            target_duration: Target video duration in seconds (optional, for web story mode)
            progress_callback: Progress callback function
        """
        title = data.get("title", "")
        desc = data.get("description", "")
        price = data.get("price", "")

        # If we are rendering from original video scenes, use dedicated path
        if self.content_type == "video" or data.get("video_path"):
            return self._render_video_with_scenes(data, output_path, progress_callback)
        
        # Use ALL available images (don't limit to 5)
        images = data.get("image_urls", [])
        if max_images:
            images = images[:max_images]

        logger.info("🎤 Render video: %s", title)
        logger.info("📸 Images available: %d - %s", len(images), images[:3] if images else "no images")
        if not images:
            logger.warning("⚠️ No images! Will use text slides instead")
        
        if progress_callback:
            progress_callback("Generating script...", 10)

        # Capture optional person image for demo mode
        self.person_image_path = data.get("person_image_path")

        # Use AI to generate script instead of hardcoded rules
        # BUT: if script already provided (e.g., from StoryScriptGenerator in GUI), use that
        if "script" in data and data["script"]:
            script = data["script"]
            logger.info("📝 Using pre-generated script from GUI")
        else:
            script = self.script_gen.generate(title, desc, price)
            logger.info("📝 Generated script from renderer")
        
        logger.info(f"📊 Script has {len(script)} scenes, images available: {len(images)}")
        
        if progress_callback:
            progress_callback(f"Creating {len(script)} scenes...", 20)

        clips, audios = [], []
        t = 0
        total_duration = 0  # Track actual duration

        try:
            for idx, text in enumerate(script):
                if progress_callback:
                    progress = 20 + (idx + 1) * 60 // len(script)
                    progress_callback(f"Scene {idx+1}/{len(script)}: {text[:50]}...", progress)
                    
                # Use images in rotation, but ensure we use them all
                img = images[idx % len(images)] if images else None
                
                if img:
                    logger.info(f"🖼️ Scene {idx+1}: Using image {(idx % len(images)) + 1}/{len(images)}")

                # generate audio first to decide scene duration
                audio_path = self.tts.tts_to_file(text)

                if audio_path and os.path.exists(audio_path):
                    audio = AudioFileClip(audio_path)
                    if target_duration:
                        duration = max(2.0, audio.duration + 0.2)
                    else:
                        duration = max(4.0, audio.duration + 0.5)  # Longer scenes
                    audios.append(audio.set_start(t))
                else:
                    duration = 2.0 if target_duration else 4.0
                
                total_duration += duration

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
            
            # Log actual duration achieved
            logger.info(f"📊 Video duration: {total_duration:.1f}s (target: {target_duration if target_duration else 'auto'}s)")
            
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

    def _render_video_with_scenes(self, data: dict, output_path: str, progress_callback=None):
        """Render using original video scenes + generated voice-over."""
        try:
            video_path = data.get("video_path")
            scenes = data.get("scenes", [])
            script_items = data.get("script", [])

            if not video_path or not os.path.exists(video_path):
                raise ValueError("video_path missing or not found")
            if not scenes or not script_items:
                raise ValueError("Scenes or script missing for video render")

            base_clip = VideoFileClip(video_path)
            clips, audios = [], []
            t = 0

            total = min(len(scenes), len(script_items))

            for idx in range(total):
                scene = scenes[idx]
                text_item = script_items[idx]
                narration = text_item.get("text", text_item if isinstance(text_item, str) else "")
                scene_start = float(scene.get("start", 0))
                scene_end = float(scene.get("end", scene_start + scene.get("duration", 3)))
                scene_dur = max(1.0, scene_end - scene_start)

                if progress_callback:
                    progress = 20 + (idx + 1) * 60 // max(1, total)
                    progress_callback(f"Scene {idx+1}/{total}: voice-over", progress)

                # Generate narration audio
                audio_path = self.tts.tts_to_file(narration)
                if audio_path:
                    self.temp_files.append(audio_path)
                audio_clip = AudioFileClip(audio_path) if audio_path and os.path.exists(audio_path) else None
                audio_dur = audio_clip.duration if audio_clip else 0

                desired_dur = max(scene_dur, audio_dur + 0.3)

                # Extract original scene
                sub = base_clip.subclip(scene_start, min(scene_end, base_clip.duration))

                # If narration longer than scene, freeze last frame to pad
                if desired_dur > sub.duration:
                    pad = desired_dur - sub.duration
                    sub = sub.fx(vfx.freeze, t=sub.duration - 0.05, freeze_duration=pad)
                else:
                    sub = sub.set_duration(desired_dur)

                if audio_clip:
                    audios.append(audio_clip.set_start(t))

                clips.append(sub.set_start(t))
                t += desired_dur

            video = CompositeVideoClip(clips, size=(self.template["width"], self.template["height"]))
            if audios:
                video.audio = CompositeAudioClip(audios)

            if progress_callback:
                progress_callback("Encoding video...", 90)

            video.write_videofile(
                output_path,
                fps=self.template["fps"],
                codec="libx264",
                audio_codec="aac",
                bitrate="8000k",
                audio_bitrate="320k",
                preset="slow",
                ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2", "-movflags", "+faststart"],
                logger=None,
            )

            if progress_callback:
                progress_callback("Video complete!", 100)

            return True

        except Exception as e:
            logger.exception("Video scene render failed: %s", e)
            self.cleanup()
            return False
        finally:
            # Ensure video file handle is released to allow cleanup of source files
            try:
                if 'base_clip' in locals() and base_clip:
                    base_clip.close()
            except Exception:
                pass
            self.cleanup()

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
        img = self.load_image(img_url) if img_url else None
        if not img:
            img = self.text_image(text)
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
        """Load image from URL or local file path"""
        try:
            # Skip if URL is None or empty
            if not url:
                return None
            
            # Check if it's a local file path
            # Try both relative and absolute paths
            filepath = url
            if not os.path.isabs(filepath):
                # Try relative to current directory
                if not os.path.exists(filepath):
                    # Try relative to project root
                    filepath = os.path.join(os.getcwd(), url)
            
            if os.path.exists(filepath):
                logger.info(f"📁 Loading local image: {os.path.basename(filepath)}")
                img = Image.open(filepath).convert("RGB")
                logger.info(f"✅ Image loaded successfully: {os.path.getsize(filepath)} bytes")
                return img
            else:
                logger.warning(f"⚠️ Image file not found: {filepath} (url was: {url})")
            
            # Otherwise treat as URL
            logger.info(f"🌐 Downloading image from URL: {url}")
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert("RGB")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load image: {e}")
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
