import os
import re
import tempfile
import logging
import json
import subprocess
from typing import List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Từ/cụm cần nhấn mạnh khi đọc (chậm hơn một chút)
PROSODY_EMPHASIS_KEYWORDS = (
    "chỉ", "đặc biệt", "quan trọng", "nhất", "ngay", "giá", "ưu đãi",
    "miễn phí", "giảm", "sale", "hot", "mới", "chính hãng", "chất lượng",
    "đáng", "tuyệt", "đừng bỏ lỡ", "hãy", "ngay bây giờ", "hôm nay",
)

# Edge-TTS Vietnamese voices (Microsoft Neural)
EDGE_TTS_VI_FEMALE = "vi-VN-HoaiMyNeural"
EDGE_TTS_VI_MALE = "vi-VN-NamMinhNeural"

# =========================
# 1️⃣ SCRIPT GENERATOR
# =========================

class ScriptGenerator:
    def generate(self, title: str, description: str, price: str) -> List[str]:
        """Return 4-sentence script for video storytelling"""
        raise NotImplementedError

class HeuristicScriptGenerator(ScriptGenerator):
    """Fallback: script chuyên nghiệp, không nhắc tên sàn/shop."""
    def generate(self, title: str, description: str, price: str):
        # Bỏ tên sàn/shop trong title (vd "Sản phẩm Shopee" -> dùng mô tả hoặc "sản phẩm")
        product_name = (title or "").strip()
        if not product_name or product_name.lower() in ("sản phẩm shopee", "shopee"):
            product_name = (description or "Sản phẩm")[:40].strip() or "Sản phẩm"
        else:
            product_name = product_name[:50]
        p = price if price and str(price).strip() != "0" else "giá tốt"
        return [
            f"Bạn đang tìm sản phẩm chất lượng? {product_name} là lựa chọn đáng cân nhắc.",
            "Thiết kế tinh tế, chất liệu cao cấp, độ bền tốt.",
            "Phù hợp nhu cầu hàng ngày, dễ phối đồ.",
            f"Chỉ {p} — mua ngay để nhận ưu đãi."
        ]

class OpenAIScriptGenerator(ScriptGenerator):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            self.client = None

    def generate(self, title: str, description: str, price: str) -> List[str]:
        if not self.client:
            return HeuristicScriptGenerator().generate(title, description, price)

        style = os.getenv("LLM_STYLE", "default")
        prompt = f"""
        Tạo kịch bản video ngắn (4 câu) quảng cáo sản phẩm. Giọng chuyên nghiệp, tự nhiên.
        Tên sản phẩm: {title}
        Mô tả: {description[:600]}
        Giá: {price}
        
        QUAN TRỌNG:
        - KHÔNG nhắc tên sàn (Shopee, Lazada...), KHÔNG nhắc tên shop trong lời đọc.
        - Chỉ nói tên sản phẩm và lợi ích. CTA chỉ cần giá + "mua ngay", không gắn tên sàn.
        
        Yêu cầu:
        1. Hook gây chú ý (theo sản phẩm, không theo sàn).
        2. Giới thiệu sản phẩm / giải pháp.
        3. Lợi ích chính.
        4. Kêu gọi hành động kèm giá (vd: "Chỉ X — mua ngay.").
        
        Trả về ĐÚNG một mảng JSON 4 chuỗi tiếng Việt. Chỉ JSON, không giải thích.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            # Clean up content if it has markdown code blocks
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return HeuristicScriptGenerator().generate(title, description, price)

class OllamaScriptGenerator(ScriptGenerator):
    def __init__(self, model: str = "gemma3:4b"):
        self.model = model
        # Allow longer/shorter timeouts via env to avoid frequent 60s kills
        try:
            self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
        except ValueError:
            self.timeout = 60

    def _run_cli(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Ollama timed out after {self.timeout}s")
            return ""
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return ""

    def generate(self, title: str, description: str, price: str) -> List[str]:
        style = os.getenv("LLM_STYLE", "default")
        prompt = f"""
        Generate a 4-sentence TikTok/Shorts script in Vietnamese. Professional tone.
        Product title: {title}
        Desc: {description[:500]}
        Price: {price}
        Style: {style}
        
        RULES:
        - Do NOT mention platform name (Shopee, Lazada) or shop name in the script.
        - Only mention product name and benefits. CTA: price + "mua ngay" only.
        
        Structure: 1) Hook (product-focused) 2) Product/solution 3) Benefits 4) CTA with price.
        Return ONLY a JSON list of 4 strings. Example: ["...", "...", "...", "..."]
        """
        resp = self._run_cli(prompt)
        try:
            import re
            match = re.search(r"\[.*\]", resp, re.DOTALL)
            if match:
                return json.loads(match.group())
            return HeuristicScriptGenerator().generate(title, description, price)
        except:
            return HeuristicScriptGenerator().generate(title, description, price)

class MovieScriptGenerator(ScriptGenerator):
    """Generate review script cho phim (style kể chuyện/giới thiệu)"""
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        self.use_llm = use_llm and api_key
        if self.use_llm:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            except ImportError:
                self.client = None
        else:
            self.client = None
    
    def generate(self, title: str, description: str, price: str = "") -> List[str]:
        """
        Generate 4-5 câu review phim:
        1. Hook (giới thiệu tên + genre/thể loại)
        2. Plot twist/conflict (điều gì khiến phim hay)
        3. Cảm xúc/khoảnh khắc đáng nhớ
        4. Lời đánh giá + rating
        5. (Optional) Kêu gọi xem
        """
        if self.use_llm and self.client:
            return self._generate_with_llm(title, description, price)
        else:
            return self._generate_heuristic(title, description, price)
    
    def _generate_heuristic(self, title: str, description: str, price: str = "") -> List[str]:
        """Fallback heuristic nếu không có LLM"""
        # Detect genre từ description
        description_lower = description.lower()
        
        genre_hints = {
            "hành động": "action",
            "tình cảm": "romance",
            "kinh dị": "horror",
            "hài": "comedy",
            "viễn tưởng": "sci-fi",
            "phim hoạt hình": "animation",
            "tài liệu": "documentary"
        }
        
        detected_genre = "phim"
        for vn, en in genre_hints.items():
            if vn in description_lower:
                detected_genre = vn
                break
        
        # Extract rating if present
        rating_match = re.search(r'(\d+\.?\d*)/10|rating:\s*(\d+\.?\d*)', description_lower)
        rating = rating_match.group(1) or rating_match.group(2) if rating_match else "8.0"
        
        return [
            f"🎬 {title} - {detected_genre} đầy kịch tính, bạn xem chưa?",
            f"Phim kể về {description[:80]}...",
            f"Những khoảnh khắc cảm xúc sâu sắc khiến bạn rơi lệ.",
            f"Đánh giá: {rating}/10 ⭐ - Bạn nên xem ngay! #Netflix #MovieReview"
        ]
    
    def _generate_with_llm(self, title: str, description: str, price: str = "") -> List[str]:
        """Generate với OpenAI"""
        try:
            prompt = f"""
            Tạo script review phim 4-5 câu cho video Shorts/TikTok:
            
            Tên phim: {title}
            Mô tả: {description[:500]}
            
            Yêu cầu:
            1. Câu 1: Hook gây chú ý (giới thiệu tên + thể loại + tại sao hay).
            2. Câu 2: Kể tóm tắt sơ bộ (không spoil quá).
            3. Câu 3: Điều đặc biệt / khoảnh khắc ấn tượng.
            4. Câu 4: Đánh giá + rating + lời kêu gọi (watch now, check trailer, etc).
            
            Phong cách: thân thiện, hứng thú, có cảm xúc (như kể chuyện với bạn).
            Ngôn ngữ: Tiếng Việt, dễ hiểu, ngắn gọn.
            
            Trả về JSON array 4 câu. Chỉ trả JSON, không giải thích thêm.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            return result if isinstance(result, list) else self._generate_heuristic(title, description)
            
        except Exception as e:
            logger.error(f"MovieScriptGenerator LLM error: {e}")
            return self._generate_heuristic(title, description)

# =========================
# 2️⃣ TTS PROVIDER
# =========================

def _prosody_rate_for_scene(scene_index: int, total_scenes: int) -> str:
    """Tính rate % cho từng đoạn: câu đầu/cuối chậm hơn (nhấn nhá), giữa bình thường."""
    if total_scenes <= 0:
        return "+0%"
    if scene_index == 0:
        return "-8%"
    if scene_index >= total_scenes - 1:
        return "-5%"
    return "+2%"


def _rate_for_sentence(sentence: str, base_rate: str) -> str:
    """Dựa vào nội dung câu (dấu câu, từ khóa) để chọn tốc độ đọc."""
    s = sentence.strip()
    if not s:
        return base_rate
    lower = s.lower()
    # Câu hỏi → chậm hơn để tự nhiên
    if s.endswith("?") or "?" in s[-2:]:
        return "-6%"
    # Câu cảm thán → nhấn mạnh
    if s.endswith("!") or "!" in s[-2:]:
        return "-5%"
    # Dấu ba chấm / gạch ngang → kéo dài, dramatic
    if s.endswith("...") or s.endswith("…") or s.endswith("—"):
        return "-8%"
    # Có từ cần nhấn mạnh (giá, chỉ, đặc biệt, ...)
    for kw in PROSODY_EMPHASIS_KEYWORDS:
        if kw in lower:
            return "-5%"
    # Câu ngắn (dưới ~6 từ) thường là nhấn mạnh
    if len(s.split()) <= 5:
        return "-3%"
    return base_rate


def _split_sentences_for_prosody(text: str) -> List[str]:
    """Tách văn bản thành các câu (giữ dấu câu) để gán rate từng câu."""
    if not text or not text.strip():
        return []
    # Tách theo . ! ? ... … và giữ phần sau dấu
    pattern = r"(?<=[.!?…])\s+|\s*—\s*|\s+\.\.\.\s+"
    parts = re.split(pattern, text.strip())
    sentences = [p.strip() for p in parts if p.strip()]
    # Nếu không tách được câu nào (không có dấu kết thúc), trả về cả đoạn
    if not sentences:
        return [text.strip()]
    return sentences


def _content_aware_prosody_fragments(
    text: str,
    scene_index: Optional[int] = None,
    total_scenes: Optional[int] = None,
    base_rate: str = "-3%",
) -> List[Tuple[str, str]]:
    """
    Phân tích nội dung, tách câu và gán rate cho từng câu.
    Returns: [(fragment_text, rate_str), ...]
    """
    sentences = _split_sentences_for_prosody(text)
    if not sentences:
        return [(text.strip(), base_rate)] if text.strip() else []

    # Điều chỉnh base theo vị trí scene (hook/cuối chậm hơn)
    if total_scenes and total_scenes > 0:
        if scene_index == 0:
            base_rate = "-8%"
        elif scene_index is not None and scene_index >= total_scenes - 1:
            base_rate = "-5%"
        else:
            base_rate = "+0%"

    return [(_s, _rate_for_sentence(_s, base_rate)) for _s in sentences]


class TTSProvider:
    def tts_to_file(self, text: str, **kwargs: Any) -> Optional[str]:
        raise NotImplementedError


class GTTSProvider(TTSProvider):
    """Google TTS - miễn phí nhưng giọng đều, ít nhấn nhá."""

    def tts_to_file(self, text: str, **kwargs: Any) -> Optional[str]:
        try:
            from gtts import gTTS
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            gTTS(text=text, lang="vi").save(f.name)
            return f.name
        except Exception as e:
            logger.warning("gTTS failed: %s", e)
            return None


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS - nhấn nhá theo nội dung (câu hỏi, cảm thán, từ khóa) + vị trí đoạn."""

    def __init__(
        self,
        voice: str = EDGE_TTS_VI_FEMALE,
        use_prosody: bool = True,
        content_aware_prosody: bool = True,
        base_rate: str = "-3%",
        base_pitch: str = "+0Hz",
    ):
        self.voice = voice
        self.use_prosody = use_prosody
        self.content_aware_prosody = content_aware_prosody
        self.base_rate = base_rate
        self.base_pitch = base_pitch

    def tts_to_file(
        self,
        text: str,
        scene_index: Optional[int] = None,
        total_scenes: Optional[int] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        try:
            import edge_tts
        except ImportError:
            logger.warning("edge-tts not installed. Run: pip install edge-tts")
            return None

        if not text or not text.strip():
            return None

        # Hiểu nội dung: tách câu và gán rate theo dấu câu + từ khóa
        if self.use_prosody and self.content_aware_prosody:
            fragments = _content_aware_prosody_fragments(
                text,
                scene_index=scene_index,
                total_scenes=total_scenes,
                base_rate=self.base_rate,
            )
            if len(fragments) <= 1:
                rate = fragments[0][1] if fragments else self.base_rate
                return self._generate_one(text.strip(), rate)
            return self._generate_and_concat(fragments)

        # Chỉ nhấn nhá theo vị trí scene (không phân tích câu)
        if self.use_prosody and scene_index is not None and total_scenes is not None:
            rate = _prosody_rate_for_scene(scene_index, total_scenes)
        else:
            rate = self.base_rate
        return self._generate_one(text.strip(), rate)

    def _generate_one(self, text: str, rate: str) -> Optional[str]:
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text,
                voice=self.voice,
                rate=rate,
                pitch=self.base_pitch,
            )
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            communicate.save_sync(f.name)
            return f.name
        except Exception as e:
            logger.warning("EdgeTTS failed: %s", e)
            return None

    def _generate_and_concat(self, fragments: List[Tuple[str, str]]) -> Optional[str]:
        """Tạo audio từng câu với rate riêng rồi ghép lại thành một file."""
        try:
            import edge_tts
            from moviepy.editor import AudioFileClip, concatenate_audioclips
        except ImportError as e:
            logger.warning("EdgeTTS or moviepy for concat: %s", e)
            # Fallback: gộp text và đọc một rate
            full = " ".join(f[0] for f in fragments)
            rate = fragments[0][1] if fragments else self.base_rate
            return self._generate_one(full, rate)

        temp_paths: List[str] = []
        try:
            for frag_text, rate in fragments:
                if not frag_text.strip():
                    continue
                com = edge_tts.Communicate(
                    frag_text.strip(),
                    voice=self.voice,
                    rate=rate,
                    pitch=self.base_pitch,
                )
                f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                com.save_sync(f.name)
                temp_paths.append(f.name)

            if not temp_paths:
                return None
            if len(temp_paths) == 1:
                return temp_paths[0]

            clips = [AudioFileClip(p) for p in temp_paths]
            final = concatenate_audioclips(clips)
            out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            final.write_audiofile(out.name, logger=None)
            for c in clips:
                c.close()
            for p in temp_paths:
                try:
                    os.unlink(p)
                except OSError:
                    pass
            return out.name
        except Exception as e:
            logger.warning("EdgeTTS concat failed: %s", e)
            for p in temp_paths:
                try:
                    os.unlink(p)
                except OSError:
                    pass
            full = " ".join(f[0] for f in fragments)
            return self._generate_one(full, self.base_rate)


class ElevenLabsTTSProvider(TTSProvider):
    def __init__(self, api_key: Optional[str], voice_id: str = "Rachel"):
        self.api_key = api_key
        self.voice_id = voice_id

    def tts_to_file(self, text: str, **kwargs: Any) -> Optional[str]:
        if not self.api_key:
            return None
        return None  # Implement later or use gTTS as fallback

# =========================
# 3️⃣ AVATAR PROVIDER
# =========================

class DIDAvatarProvider:
    def __init__(self, api_key: Optional[str], api_secret: Optional[str]):
        self.api_key = api_key
        self.api_secret = api_secret

    def create_avatar_clip(self, text: str) -> Optional[str]:
        return None
