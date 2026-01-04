import os
import tempfile
import requests
import textwrap
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

            # 1. TRUY XUẤT DỮ LIỆU
            images = processed_data.get("image_urls", [])
            title = str(processed_data.get("title", "Sản phẩm Hot"))
            desc_raw = processed_data.get("description") or processed_data.get("short_description") or ""
            description = str(desc_raw).strip()

            # 2. PHÂN ĐOẠN MÔ TẢ THÔNG MINH
            raw_sentences = re.split(r'[\n✅📌✔️•\-\t]|(?<=[.!?])\s+', description)
            sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]

            # --- BỔ SUNG: Nếu lấy được quá ít câu, tự động chặt nhỏ câu dài ---
            if len(sentences) < 3 and len(description) > 100:
                logger.info("⚠️ Nội dung quá ít câu, đang tự động chia nhỏ theo độ dài...")
                sentences = textwrap.wrap(description, width=80) # Chặt mỗi 80 ký tự thành 1 câu thoại

            if not sentences:
                sentences = [title] # Cuối cùng nếu vẫn rỗng thì lấy Title làm thoại

            logger.info(f"🎬 Bắt đầu Render: {len(images)} ảnh | Phân tách thành {len(sentences)} câu thoại.")

            clips = []
            audio_segments = []
            current_time = 0

            # 3. CLIP TIÊU ĐỀ (INTRO)
            title_clip = self._text_clip(title, 65, "#FFD700", 3.0, is_intro=True)
            clips.append(title_clip.set_start(0))
            current_time += 3.0

            # 4. VÒNG LẶP TẠO CLIP ẢNH + VOICE
            target_images = images[:max_images]
            for i, url in enumerate(target_images):
                # Lấy câu thoại theo vòng lặp nếu ảnh nhiều hơn câu
                part_text = sentences[i % len(sentences)]
                
                # Tạo Voiceover
                voice_path = self.create_voiceover(part_text)
                if not voice_path:
                    continue
                    
                audio_clip = AudioFileClip(voice_path)
                # Thời lượng = tiếng nói + 0.8s nghỉ để video không bị dồn dập
                duration = max(audio_clip.duration + 0.8, 2.5) 
                
                img_clip = self.render_image_clip(url, part_text, duration)
                if img_clip:
                    img_clip = img_clip.set_start(current_time)
                    audio_clip = audio_clip.set_start(current_time)
                    
                    clips.append(img_clip)
                    audio_segments.append(audio_clip)
                    
                    current_time += duration
                    logger.info(f"✅ Đã xử lý Clip {i+1}: {part_text[:30]}...")

            if len(clips) <= 1:
                logger.error("❌ Không đủ dữ liệu để tạo video.")
                return False

            # 5. MIXING & EXPORT
            final_video = CompositeVideoClip(clips, size=(self.template.width, self.template.height))
            
            voice_audio = CompositeAudioClip(audio_segments)
            if audio_path and os.path.exists(audio_path):
                bg_music = AudioFileClip(audio_path).volumex(0.12).set_duration(current_time)
                final_audio = CompositeAudioClip([voice_audio, bg_music])
            else:
                final_audio = voice_audio

            final_video = final_video.set_audio(final_audio).set_duration(current_time)
            
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

    def render_image_clip(self, url, description, duration):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            img = Image.open(BytesIO(r.content)).convert("RGB")
            tw, th = self.template.width, self.template.height
            
            # 1. Tạo nền (Phông nền tối cho TikTok)
            canvas = Image.new("RGB", (tw, th), (20, 20, 20))
            
            # 2. Xử lý ảnh sản phẩm (Nằm ở nửa trên)
            img.thumbnail((tw - 100, th - 650), Image.Resampling.LANCZOS)
            img_pos = ((tw - img.width) // 2, 180)
            canvas.paste(img, img_pos)

            # 3. Chèn Text với Box nền mờ (Để luôn đọc được chữ)
            if description:
                draw = ImageDraw.Draw(canvas)
                try: font = ImageFont.truetype("arial.ttf", 42)
                except: font = ImageFont.load_default()
                
                wrapped_text = "\n".join(textwrap.wrap(description, width=28))
                
                # Tính toán kích thước Box nền
                bbox = draw.multiline_textbbox((tw // 2, th - 350), wrapped_text, font=font, anchor="mm")
                padding = 25
                # Vẽ hình chữ nhật bo góc/mờ (giả lập mờ bằng rectangle xám đen)
                draw.rectangle(
                    [bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding], 
                    fill=(0, 0, 0, 180)
                )
                
                # Vẽ text chính
                draw.multiline_text(
                    (tw // 2, th - 350), 
                    wrapped_text, 
                    fill="white", 
                    font=font, 
                    anchor="mm", 
                    align="center",
                    spacing=10
                )

            path = self._save_temp(canvas)
            return ImageClip(path, duration=duration).fadein(0.4)
        except Exception as e:
            logger.warning(f"⚠️ Lỗi render ảnh: {e}")
            return None

    def create_voiceover(self, text):
        if not text: return None
        try:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang='vi')
            tts.save(f.name)
            self._temp_files.append(f.name)
            return f.name
        except: return None

    def _text_clip(self, text, size, color, duration, is_intro=False):
        tw, th = self.template.width, self.template.height
        img = Image.new("RGB", (tw, th), (15, 15, 15))
        draw = ImageDraw.Draw(img)
        
        try: font = ImageFont.truetype("arial.ttf", size)
        except: font = ImageFont.load_default()
        
        wrapped_text = "\n".join(textwrap.wrap(text, width=22))
        
        # Tiêu đề chính giữa cho Intro
        draw.multiline_text((tw // 2, th // 2), wrapped_text, fill=color, font=font, anchor="mm", align="center")
        
        path = self._save_temp(img)
        clip = ImageClip(path, duration=duration)
        return clip.fadein(0.8).fadeout(0.5)

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