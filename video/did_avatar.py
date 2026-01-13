"""
D-ID API Integration for AI Talking Avatar
Tạo video người nói từ ảnh tĩnh + audio
"""
import os
import time
import requests
from utils.logger import get_logger

logger = get_logger()

class DIDTalkingAvatar:
    """Generate talking avatar videos using D-ID API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("DID_API_KEY")
        self.base_url = "https://api.d-id.com"
        
        if not self.api_key:
            logger.warning("⚠️ D-ID API key not found. Set DID_API_KEY environment variable.")
    
    def create_talking_video(self, image_path, audio_path, output_path, max_wait=120):
        """
        Tạo video người nói từ ảnh + audio
        
        Args:
            image_path: Đường dẫn ảnh người (JPG/PNG)
            audio_path: Đường dẫn file audio (MP3/WAV)
            output_path: Nơi lưu video kết quả
            max_wait: Thời gian chờ tối đa (giây)
        
        Returns:
            bool: True nếu thành công
        """
        if not self.api_key:
            logger.error("❌ Cannot create talking video: D-ID API key missing")
            return False
        
        try:
            # Step 1: Upload image
            logger.info("📤 Uploading image to D-ID...")
            image_url = self._upload_image(image_path)
            if not image_url:
                return False
            
            # Step 2: Upload audio
            logger.info("📤 Uploading audio to D-ID...")
            audio_url = self._upload_audio(audio_path)
            if not audio_url:
                return False
            
            # Step 3: Create talk (start generation)
            logger.info("🎬 Creating talking avatar video...")
            talk_id = self._create_talk(image_url, audio_url)
            if not talk_id:
                return False
            
            # Step 4: Wait for completion
            logger.info("⏳ Waiting for video generation...")
            video_url = self._wait_for_video(talk_id, max_wait)
            if not video_url:
                return False
            
            # Step 5: Download result
            logger.info("💾 Downloading result...")
            success = self._download_video(video_url, output_path)
            
            if success:
                logger.info("✅ Talking avatar video created: %s", output_path)
            return success
            
        except Exception as e:
            logger.error("❌ Failed to create talking video: %s", e)
            return False
    
    def _upload_image(self, image_path):
        """Upload image and get URL"""
        try:
            url = f"{self.base_url}/images"
            headers = {"Authorization": f"Basic {self.api_key}"}
            
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return data.get('url')
            else:
                logger.error("Image upload failed: %s", response.text)
                return None
        except Exception as e:
            logger.error("Image upload error: %s", e)
            return None
    
    def _upload_audio(self, audio_path):
        """Upload audio and get URL"""
        try:
            url = f"{self.base_url}/audios"
            headers = {"Authorization": f"Basic {self.api_key}"}
            
            with open(audio_path, 'rb') as f:
                files = {'audio': f}
                response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return data.get('url')
            else:
                logger.error("Audio upload failed: %s", response.text)
                return None
        except Exception as e:
            logger.error("Audio upload error: %s", e)
            return None
    
    def _create_talk(self, image_url, audio_url):
        """Create talk and get ID"""
        try:
            url = f"{self.base_url}/talks"
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "source_url": image_url,
                "script": {
                    "type": "audio",
                    "audio_url": audio_url
                },
                "config": {
                    "stitch": True,  # Smooth transitions
                    "result_format": "mp4"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return data.get('id')
            else:
                logger.error("Talk creation failed: %s", response.text)
                return None
        except Exception as e:
            logger.error("Talk creation error: %s", e)
            return None
    
    def _wait_for_video(self, talk_id, max_wait):
        """Poll for video completion"""
        url = f"{self.base_url}/talks/{talk_id}"
        headers = {"Authorization": f"Basic {self.api_key}"}
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'done':
                        return data.get('result_url')
                    elif status == 'error':
                        logger.error("Video generation failed: %s", data.get('error'))
                        return None
                    else:
                        logger.info("Status: %s (%.0fs elapsed)", status, time.time() - start_time)
                        time.sleep(5)  # Check every 5 seconds
                else:
                    logger.warning("Status check failed: %s", response.status_code)
                    time.sleep(5)
            except Exception as e:
                logger.warning("Status check error: %s", e)
                time.sleep(5)
        
        logger.error("Timeout waiting for video (max %ds)", max_wait)
        return None
    
    def _download_video(self, video_url, output_path):
        """Download final video"""
        try:
            response = requests.get(video_url, timeout=60, stream=True)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                logger.error("Download failed: %s", response.status_code)
                return False
        except Exception as e:
            logger.error("Download error: %s", e)
            return False
