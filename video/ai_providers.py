import os
import tempfile
import logging
import json
import subprocess
from typing import List, Optional

logger = logging.getLogger(__name__)

# =========================
# 1️⃣ SCRIPT GENERATOR
# =========================

class ScriptGenerator:
    def generate(self, title: str, description: str, price: str) -> List[str]:
        """Return 4-sentence script for video storytelling"""
        raise NotImplementedError

class HeuristicScriptGenerator(ScriptGenerator):
    """Fallback simple heuristic"""
    def generate(self, title: str, description: str, price: str):
        p = price if price and price != "0" else "giá cực hời"
        return [
            f"Khám phá ngay: {title[:50]}",
            "Sản phẩm cực chất, thiết kế tinh tế.",
            f"Chất liệu cao cấp, độ bền vượt trội.",
            f"Chỉ {p}, chốt đơn ngay kẻo lỡ!"
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
        Tạo kịch bản video ngắn (4 câu) quảng cáo sản phẩm sau:
        Tên: {title}
        Mô tả: {description}
        Giá: {price}
        
        Phong cách: {style} (nếu là veo3/sora thì làm cực kỳ lôi cuốn, có hook mạnh).
        
        Yêu cầu:
        1. Câu 1: Hook gây chú ý.
        2. Câu 2: Giới thiệu giải pháp/sản phẩm.
        3. Câu 3: Lợi ích chính.
        4. Câu 4: Kêu gọi hành động (CTA) kèm giá.
        
        Trả về kết quả là một mảng JSON 4 câu tiếng Việt. Chỉ trả về JSON, không giải thích gì thêm.
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
        Generate a 4-sentence TikTok/Shorts script in Vietnamese for this product.
        Title: {title}
        Desc: {description[:500]}
        Price: {price}
        Style: {style}
        
        Requirements: 
        1. Hook
        2. Solution
        3. Benefit
        4. CTA (include price)
        
        Return ONLY a JSON list of 4 strings.
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

class ElevenLabsTTSProvider(TTSProvider):
    def __init__(self, api_key: Optional[str], voice_id: str = "Rachel"):
        self.api_key = api_key
        self.voice_id = voice_id

    def tts_to_file(self, text: str) -> Optional[str]:
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
