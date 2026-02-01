"""
Mô hình video (image-to-video): SVD local hoặc Runway API.
Bật qua env: VIDEO_GENERATOR=svd hoặc runway.
"""
import os
import tempfile
import time
from abc import ABC, abstractmethod
from typing import Optional

from utils.logger import get_logger

logger = get_logger()


class BaseVideoGenerator(ABC):
    """Interface: từ ảnh + prompt → video ngắn."""

    @abstractmethod
    def generate(self, image_path: str, prompt: str, output_path: str, duration_sec: float = 4.0) -> Optional[str]:
        """
        Sinh video từ ảnh + mô tả.
        Returns: đường dẫn file video, hoặc None nếu lỗi.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class StableVideoDiffusionGenerator(BaseVideoGenerator):
    """Stable Video Diffusion (local): ảnh → video 2–4s. Cần GPU, diffusers + torch."""

    name = "Stable Video Diffusion (local)"

    def __init__(self, model_id: str = "stabilityai/stable-video-diffusion-img2vid-xt"):
        self.model_id = model_id
        self._pipe = None

    def _load_pipe(self):
        if self._pipe is not None:
            return True
        try:
            import torch
            from diffusers import StableVideoDiffusionPipeline
            self._pipe = StableVideoDiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                variant="fp16",
            )
            self._pipe.enable_model_cpu_offload()
            logger.info("SVD pipeline loaded (local)")
            return True
        except ImportError as e:
            logger.warning("SVD requires: pip install diffusers transformers accelerate torch — %s", e)
            return False
        except Exception as e:
            logger.warning("SVD load failed: %s", e)
            return False

    def generate(self, image_path: str, prompt: str, output_path: str, duration_sec: float = 4.0) -> Optional[str]:
        if not os.path.exists(image_path):
            return None
        if not self._load_pipe():
            return None
        try:
            from diffusers.utils import load_image, export_to_video
            image = load_image(image_path)
            image = image.resize((1024, 576))
            generator = __import__("torch").manual_seed(int(time.time()) % 2**31)
            frames = self._pipe(
                image,
                decode_chunk_size=8,
                generator=generator,
                num_frames=25,
            ).frames[0]
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            export_to_video(frames, output_path, fps=7)
            return output_path if os.path.exists(output_path) else None
        except Exception as e:
            logger.warning("SVD generate failed: %s", e)
            return None


class RunwayVideoGenerator(BaseVideoGenerator):
    """Runway API: image-to-video. Cần RUNWAY_API_KEY, pip install runwayml."""

    name = "Runway API"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RUNWAY_API_KEY")
        self._client = None
        if self.api_key:
            try:
                from runwayml import RunwayML
                self._client = RunwayML(api_key=self.api_key)
            except ImportError:
                logger.warning("Runway requires: pip install runwayml")
            except Exception as e:
                logger.warning("Runway client init failed: %s", e)

    def generate(self, image_path: str, prompt: str, output_path: str, duration_sec: float = 4.0) -> Optional[str]:
        if not self._client or not self.api_key:
            return None
        if not os.path.exists(image_path):
            return None
        try:
            task = self._client.image_to_video.create(
                model="gen3a_turbo",
                prompt_image=image_path,
                prompt_text=prompt[:500] if prompt else "smooth motion, product shot",
                duration=min(5, max(2, int(duration_sec))),
            )
            task_id = task.id
            for _ in range(120):
                status = self._client.tasks.retrieve(task_id)
                if getattr(status, "status", None) == "SUCCEEDED":
                    break
                if getattr(status, "status", None) in ("FAILED", "CANCELED"):
                    return None
                time.sleep(2)
            else:
                return None
            out_url = getattr(status, "output", None) or (status.result if hasattr(status, "result") else None)
            if not out_url:
                return None
            import requests
            r = requests.get(out_url, timeout=60)
            r.raise_for_status()
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(r.content)
            return output_path if os.path.exists(output_path) else None
        except Exception as e:
            logger.warning("Runway generate failed: %s", e)
            return None


def get_video_generator() -> Optional[BaseVideoGenerator]:
    """Từ env VIDEO_GENERATOR (svd | runway) trả về generator hoặc None."""
    provider = (os.getenv("VIDEO_GENERATOR") or "").strip().lower()
    if not provider:
        return None
    if provider == "svd":
        return StableVideoDiffusionGenerator()
    if provider == "runway":
        if os.getenv("RUNWAY_API_KEY"):
            return RunwayVideoGenerator()
        logger.warning("VIDEO_GENERATOR=runway but RUNWAY_API_KEY not set")
        return None
    logger.warning("Unknown VIDEO_GENERATOR=%s (use svd or runway)", provider)
    return None
