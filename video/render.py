import os
import re
import tempfile
import textwrap
import json
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    CompositeAudioClip,
    CompositeVideoClip,
)
from gtts import gTTS
from utils.logger import get_logger

logger = get_logger()


class SmartVideoRenderer:
    def __init__(self, template=None):
        self.template = template or {"width": 720, "height": 1280, "fps": 24}
        self._temp_files = []

    # ====================== RENDER CHÍNH ======================
    def render(self, processed_data: dict, output_path: str,
               max_images: int = 8, audio_path: str = None) -> bool:
        try:
            self._ensure_directory(os.path.dirname(output_path))

            images = processed_data.get("image_urls", [])
            title = processed_data.get("title", "Sản phẩm hot")
            description = processed_data.get("description") or ""
            price = str(processed_data.get("price", "")).strip()

            description = self._clean_text(description)
            script = self._generate_script(title, description, price)

            logger.info(f"🎬 Tạo video với {len(images[:max_images])} ảnh và {len(script)} câu thoại.")

            clips = []
            audio_segments = []
            current_time = 0

            # ================= INTRO =================
            intro_clip = self._make_intro(title)
            clips.append(intro_clip.set_start(current_time))
            current_time += intro_clip.duration

            # ================= SCENES =================
            for i, url in enumerate(images[:max_images]):
                sentence = script[i % len(script)]
                voice_file = self._create_tts(sentence)
                if not voice_file:
                    continue
                audio_clip = AudioFileClip(voice_file)
                duration = max(audio_clip.duration + 0.5, 3.0)

                img_clip = self._make_image_scene(url, sentence, duration, i)
                if img_clip:
                    clips.append(img_clip.set_start(current_time))
                    audio_segments.append(audio_clip.set_start(current_time))
                    current_time += duration
                    logger.info(f" + Scene {i+1}: {sentence[:50]}...")

            # ================= OUTRO =================
            cta_text = f"Chốt đơn ngay với giá {price}!\nNhanh tay kẻo hết!"
            outro_clip = self._make_cta(cta_text)
            clips.append(outro_clip.set_start(current_time))
            outro_voice = self._create_tts(cta_text)
            if outro_voice:
                audio_segments.append(AudioFileClip(outro_voice).set_start(current_time))
            current_time += outro_clip.duration

            # ================= MIX AUDIO/VIDEO =================
            video = CompositeVideoClip(clips, size=(self.template["width"], self.template["height"]))
            audio = CompositeAudioClip(audio_segments)

            if audio_path and os.path.exists(audio_path):
                bg_music = AudioFileClip(audio_path).volumex(0.08).set_duration(current_time)
                video = video.set_audio(CompositeAudioClip([audio, bg_music]))
            else:
                video = video.set_audio(audio)

            video.write_videofile(
                output_path, codec="libx264", audio_codec="aac", fps=self.template["fps"], threads=4, logger=None
            )

            video.close()
            self._cleanup()
            return True

        except Exception as e:
            logger.error(f"❌ Lỗi render video: {e}")
            return False

    # ====================== UTILS ======================
    def _clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _generate_script(self, title, description, price):
        sentences = re.split(r'[.?!;]\s*', description)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        script = [f"Khám phá ngay: {title}"] if title else []

        feature_map = {
            'cotton': "Chất liệu cotton mềm mại, thoáng mát!",
            'form': "Form áo rộng rãi, thoải mái nhưng vẫn đẹp.",
            'màu': "Đa dạng màu sắc, phối đồ dễ dàng.",
            'size': "Nhiều size phù hợp cả nam & nữ.",
        }

        used = 0
        for s in sentences:
            s_lower = s.lower()
            matched = False
            for k, v in feature_map.items():
                if k in s_lower:
                    script.append(v)
                    matched = True
                    break
            if not matched:
                script.append(s if len(s) < 50 else s[:50] + "...")
            used += 1
            if used >= 5:
                break

        if price and price != "0":
            script.append(f"Giá chỉ {price}, nhanh tay kẻo hết!")
        else:
            script.append("Mua ngay hôm nay để nhận ưu đãi!")

        return script

    def _make_intro(self, text):
        w, h = self.template["width"], self.template["height"]
        duration = 2.5
        img = Image.new("RGB", (w, h), (20, 20, 20))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(text, width=20))
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
        draw.multiline_text(
            ((w - (bbox[2]-bbox[0])//2), (h - (bbox[3]-bbox[1])//2)),
            wrapped, font=font, fill="#FFD700"
        )
        path = self._save_temp(img)
        clip = ImageClip(path, duration=duration).fadein(0.5).fadeout(0.5)
        return clip.resize(lambda t: 1 + 0.05*t)

    def _make_image_scene(self, url, text, duration, idx):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception as e:
            logger.warning(f"⚠️ Lỗi tải ảnh: {e}")
            return None

        w, h = self.template["width"], self.template["height"]
        canvas = Image.new("RGBA", (w, h), (15, 15, 15, 255))

        max_w, max_h = w-100, h-400
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        canvas.paste(img, ((w-img.width)//2, 100))

        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()

        lines = textwrap.wrap(text, width=30)[:4]
        wrapped = "\n".join(lines)

        bbox = draw.multiline_textbbox((w//2, h-180), wrapped, font=font, anchor="mm")
        pad = 24
        draw.rectangle((bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad), fill=(0,0,0,190))
        draw.multiline_text((w//2, h-180), wrapped, font=font, fill="white", anchor="mm", align="center", spacing=10)

        img_path = self._save_temp(canvas.convert("RGB"))
        clip = ImageClip(img_path, duration=duration)

        motion_type = idx % 5
        if motion_type == 0:
            clip = clip.resize(lambda t: 1 + 0.03*t)
        elif motion_type == 1:
            clip = clip.resize(lambda t: 1.05 - 0.03*t)
        elif motion_type == 2:
            clip = clip.set_position(lambda t: ("center", int(-15*t)))
        elif motion_type == 3:
            clip = clip.set_position(lambda t: ("center", int(15*t)))
        else:
            clip = clip.set_position(lambda t: (int(-10*t), "center"))
        return clip.fadein(0.4).fadeout(0.4)

    def _make_cta(self, text):
        w, h = self.template["width"], self.template["height"]
        duration = 3.0
        img = Image.new("RGB", (w, h), (30,30,30))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("fonts/Roboto-Bold.ttf", 50)
        except:
            font = ImageFont.load_default()
        wrapped = "\n".join(textwrap.wrap(text, width=20))
        bbox = draw.multiline_textbbox((0,0), wrapped, font=font)
        draw.multiline_text(
            ((w-(bbox[2]-bbox[0])//2), (h-(bbox[3]-bbox[1])//2)),
            wrapped, font=font, fill="#FFCC00"
        )
        path = self._save_temp(img)
        clip = ImageClip(path, duration=duration).fadein(0.6).fadeout(0.6)
        return clip.resize(lambda t: 1 + 0.06*t)

    def _create_tts(self, text):
        try:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            gTTS(text=text, lang="vi").save(f.name)
            self._temp_files.append(f.name)
            return f.name
        except Exception as e:
            logger.warning(f"TTS error: {e}")
            return None

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
