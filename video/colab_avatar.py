"""
SadTalker Colab Integration - Free AI Avatar
Gọi SadTalker API trên Google Colab (miễn phí)
"""
import os
import requests
from utils.logger import get_logger

logger = get_logger()

class ColabSadTalkerAvatar:
    """Generate talking avatar using SadTalker on Google Colab (FREE)"""
    
    def __init__(self, colab_api_url=None):
        """
        Args:
            colab_api_url: URL của Colab API (từ ngrok)
                          Ví dụ: https://xxxx-xx-xx-xxx-xx.ngrok.io
        """
        self.api_url = colab_api_url or os.getenv("COLAB_API_URL")
        
        if not self.api_url:
            logger.warning("⚠️ Colab API URL not set. Run notebook first!")
            logger.info("📋 Hướng dẫn:")
            logger.info("1. Mở file: SadTalker_Colab_Free.ipynb")
            logger.info("2. Upload lên Google Colab")
            logger.info("3. Chạy cell 5 (API Server)")
            logger.info("4. Copy URL ngrok → Set COLAB_API_URL")
    
    def create_talking_video(self, image_path, audio_path, output_path, max_wait=180, retry_count=2):
        """
        Tạo video người nói từ ảnh + audio qua Colab API
        
        Args:
            image_path: Đường dẫn ảnh người
            audio_path: Đường dẫn audio
            output_path: Nơi lưu video kết quả
            max_wait: Thời gian chờ tối đa (giây)
            retry_count: Số lần thử lại khi gặp lỗi
        
        Returns:
            bool: True nếu thành công
        """
        if not self.api_url:
            logger.error("❌ Colab API URL chưa được cấu hình")
            logger.info("💡 Fix: Chạy SadTalker_Colab_Free.ipynb cell 5, sau đó:")
            logger.info("   $env:COLAB_API_URL='https://denny-pseudospiritual-stomachically.ngrok-free.dev'")
            return False
        
        # Retry logic
        for attempt in range(retry_count):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt + 1}/{retry_count}...")
                
                logger.info("📤 Uploading to Colab...")
                
                # Validate files exist
                if not os.path.exists(image_path):
                    logger.error(f"❌ Image not found: {image_path}")
                    return False
                if not os.path.exists(audio_path):
                    logger.error(f"❌ Audio not found: {audio_path}")
                    return False
                
                # Prepare files
                with open(image_path, 'rb') as img_file, open(audio_path, 'rb') as audio_file:
                    files = {
                        'image': ('image.jpg', img_file, 'image/jpeg'),
                        'audio': ('audio.wav', audio_file, 'audio/wav')
                    }
                    
                    # Add optional parameters to reduce processing errors
                    data = {
                        'preprocess': 'crop',  # 'crop' faster and more stable than 'full'
                        'still_mode': 'true',  # Recommended for photos
                        'enhancer': 'none'  # Disable GFPGAN to avoid errors
                    }
                    
                    # POST to Colab API
                    response = requests.post(
                        f"{self.api_url}/generate",
                        files=files,
                        data=data,
                        timeout=max_wait
                    )
                
                if response.status_code == 200:
                    # Check if response is actually video content
                    if len(response.content) < 1000:
                        logger.error("❌ Response too small, likely an error")
                        if attempt < retry_count - 1:
                            continue
                        return False
                    
                    # Save video
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info("✅ Video created successfully: %s", output_path)
                    return True
                else:
                    error_msg = response.text
                    logger.error(f"❌ Colab API failed (attempt {attempt + 1}): {error_msg}")
                    
                    # Parse common errors
                    if "gfpgan" in error_msg.lower():
                        logger.info("💡 GFPGAN error detected - this is common")
                        logger.info("💡 Fix: Update Colab notebook to use enhancer='none' or 'RestoreFormer'")
                    elif "exit status 1" in error_msg:
                        logger.info("💡 Inference failed - possible causes:")
                        logger.info("   1. Image quality too low or corrupted")
                        logger.info("   2. Audio file format not supported")
                        logger.info("   3. Colab dependencies not fully installed")
                        logger.info("   4. Try running Colab setup cells again")
                    
                    if attempt < retry_count - 1:
                        import time
                        time.sleep(2)  # Wait before retry
                        continue
                    return False
                    
            except requests.Timeout:
                logger.error(f"❌ Timeout waiting for Colab (max {max_wait}s)")
                if attempt < retry_count - 1:
                    continue
                return False
            except Exception as e:
                logger.error(f"❌ Failed to create video (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    continue
                return False
        
        return False
    
    def is_available(self):
        """Check if Colab API is running"""
        if not self.api_url:
            return False
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
