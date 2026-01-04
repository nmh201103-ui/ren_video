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

            # 1. TRUY XUẤT DỮ LIỆU ĐA KÊNH (CHỐNG MẤT DỮ LIỆU)
            images = processed_data.get("image_urls", [])
            title = str(processed_data.get("title", "Sản phẩm Hot"))
            
            # Ưu tiên lấy 'description', nếu không có thì lấy 'short_description'
            desc_raw = processed_data.get("description") or processed_data.get("short_description") or ""
            description = str(desc_raw).strip()

            # --- LOG KIỂM TRA ĐẦU VÀO ---
            print("\n" + "🎬" * 10 + " [RENDERER PROCESS] " + "🎬" * 10)
            print(f"TITLE: {title}")
            print(f"MÔ TẢ NHẬN ĐƯỢC: {len(description)} ký tự")
            
            if len(description) < 20:
                logger.warning("⚠️ Mô tả quá ngắn hoặc rỗng, dùng nội dung dự phòng.")
                description = f"Chào mừng bạn đến với {title}. Đây là sản phẩm tuyệt vời nhất với chất lượng vượt trội, giá cả phải chăng. Đừng bỏ lỡ cơ hội sở hữu ngay hôm nay!"
            
            print("🎬" * 30 + "\n")

            # 2. PHÂN ĐOẠN MÔ TẢ THÔNG MINH
            # Tách theo dấu chấm, xuống dòng và lọc bỏ câu quá ngắn
            sentences = [s.strip() for s in re.split(r'[.!?\n]\s*', description) if len(s.strip()) > 10]
            
            if not sentences:
                sentences = textwrap.wrap(description, width=80)

            clips = []
            audio_segments = []
            current_time = 0

            # 3. CLIP TIÊU ĐỀ (INTRO - 3 GIÂY)
            title_clip = self._text_clip(title, 60, "#FFD700", 3.0, animation_type="fade_in")
            title_clip = title_clip.set_start(0)
            clips.append(title_clip)
            current_time += 3.0

            # 4. VÒNG LẶP TẠO CLIP ẢNH + GIỌNG ĐỌC
            target_images = images[:max_images]
            for i, url in enumerate(target_images):
                # Lấy câu mô tả tương ứng, nếu hết câu thì dùng câu cuối cùng
                part_text = sentences[i] if i < len(sentences) else sentences[-1]
                
                # Tạo Voiceover
                voice_path = self.create_voiceover(part_text)
                if not voice_path:
                    continue
                    
                audio_clip = AudioFileClip(voice_path)
                # Thời lượng clip = độ dài giọng nói + 0.6s nghỉ
                duration = audio_clip.duration + 0.6
                
                # Tạo Image Clip với Text chèn đè
                img_clip = self.render_image_clip(url, part_text, duration)
                
                if img_clip:
                    # Thiết lập thời điểm bắt đầu cho cả audio và video
                    img_clip = img_clip.set_start(current_time)
                    audio_clip = audio_clip.set_start(current_time)
                    
                    clips.append(img_clip)
                    audio_segments.append(audio_clip)
                    
                    current_time += duration
                    logger.info(f"✅ Đã tạo Clip {i+1}/{len(target_images)}")

            if len(clips) <= 1:
                logger.error("❌ Không đủ tài nguyên (ảnh/text) để xuất video.")
                return False

            # 5. MIX AUDIO & EXPORT
            # Dùng CompositeVideoClip để khớp timeline chính xác hơn concatenate
            final_video = CompositeVideoClip(clips).set_duration(current_time)
            
            voice_audio = CompositeAudioClip(audio_segments)
            
            # Nhạc nền (nếu có)
            if audio_path and os.path.exists(audio_path):
                bg_music = AudioFileClip(audio_path).volumex(0.12).set_duration(current_time)
                final_audio = CompositeAudioClip([voice_audio, bg_music])
            else:
                final_audio = voice_audio

            final_video = final_video.set_audio(final_audio)
            
            # Xuất video chất lượng cao
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                fps=24, 
                threads=4, 
                preset="medium",
                logger=None
            )
            
            final_video.close()
            self._cleanup()
            return True

        except Exception as e:
            logger.error(f"❌ Render Error: {e}")
            return False

    def render_image_clip(self, url, description, duration):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            img = Image.open(BytesIO(r.content)).convert("RGB")
            tw, th = self.template.width, self.template.height
            
            # Canvas đen chuẩn TikTok (9:16)
            canvas = Image.new("RGB", (tw, th), (18, 18, 18))
            
            # Resize ảnh sản phẩm (để chừa chỗ cho text ở dưới)
            img.thumbnail((tw - 80, th - 600), Image.Resampling.LANCZOS)
            
            # Paste ảnh vào giữa phần trên
            offset = ((tw - img.width) // 2, (th - 600 - img.height) // 2 + 150)
            canvas.paste(img, offset)

            # Vẽ Text
            if description:
                draw = ImageDraw.Draw(canvas)
                try: 
                    # Ưu tiên font Arial, nếu không có dùng font mặc định
                    font = ImageFont.truetype("arial.ttf", 38)
                except: 
                    font = ImageFont.load_default()
                
                # Wrap text để không bị tràn màn hình
                wrapped_text = "\n".join(textwrap.wrap(description, width=30))
                
                # Căn lề text ở 1/4 dưới màn hình
                draw.text((tw // 2, th - 300), wrapped_text, fill="white", font=font, anchor="mm", align="center")

            path = self._save_temp(canvas)
            return ImageClip(path, duration=duration).fadein(0.4)
        except Exception as e:
            logger.warning(f"⚠️ Lỗi render ảnh {url}: {e}")
            return None

    def create_voiceover(self, text):
        if not text or len(text.strip()) < 2: return None
        try:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang='vi')
            tts.save(f.name)
            self._temp_files.append(f.name)
            return f.name
        except: return None

    def _text_clip(self, text, size, color, duration, animation_type="none"):
        # Tạo clip tiêu đề nghệ thuật hơn
        tw, th = self.template.width, self.template.height
        img = Image.new("RGB", (tw, th), (25, 25, 25))
        draw = ImageDraw.Draw(img)
        
        try: font = ImageFont.truetype("arial.ttf", size)
        except: font = ImageFont.load_default()
        
        wrapped_text = "\n".join(textwrap.wrap(text, width=22))
        
        # Vẽ tiêu đề ở chính giữa màn hình
        draw.text((tw // 2, th // 2), wrapped_text, fill=color, font=font, anchor="mm", align="center")
        
        path = self._save_temp(img)
        clip = ImageClip(path, duration=duration)
        if animation_type == "fade_in": clip = clip.fadein(0.8)
        return clip

    def _save_temp(self, img):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(f.name, quality=95)
        self._temp_files.append(f.name)
        return f.name

    def _ensure_directory(self, directory):
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def _cleanup(self):
        for f in self._temp_files:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
        self._temp_files = []