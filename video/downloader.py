"""
Video Downloader & Processor
Download videos from YouTube, TikTok, Instagram
"""
import os
import subprocess
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger()


class VideoDownloader:
    """Download videos using yt-dlp"""
    
    def __init__(self, output_dir="assets/temp/downloads"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Download video from URL with retry logic
        Returns: path to downloaded video file
        """
        try:
            import yt_dlp
        except ImportError:
            logger.error("yt-dlp not installed. Install: pip install yt-dlp")
            return None
        
        logger.info(f"📥 Downloading video from: {url}")
        
        # Try multiple format options
        format_options = [
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Best quality MP4
            'best[height<=1080][ext=mp4]/best[height<=1080]',  # 1080p or lower
            'best[height<=720][ext=mp4]/best[height<=720]',   # 720p fallback
            'best',  # Any format as last resort
        ]
        
        for attempt in range(max_retries):
            for fmt in format_options:
                try:
                    output_template = os.path.join(self.output_dir, "%(id)s.%(ext)s")
                    
                    ydl_opts = {
                        'format': fmt,
                        'outtmpl': output_template,
                        'noplaylist': True,
                        'quiet': False if attempt > 0 else True,  # Show output on retry
                        'no_warnings': False,
                        'ignoreerrors': False,
                        # Fix for empty downloads
                        'nocheckcertificate': True,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        },
                        # Retry on network errors
                        'retries': 3,
                        'fragment_retries': 3,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        if not info:
                            logger.warning(f"No video info returned (attempt {attempt+1}/{max_retries})")
                            continue
                        
                        video_id = info.get('id', 'video')
                        ext = info.get('ext', 'mp4')
                        video_path = os.path.join(self.output_dir, f"{video_id}.{ext}")
                        
                        # Verify file exists and is not empty
                        if os.path.exists(video_path):
                            file_size = os.path.getsize(video_path)
                            if file_size > 1024:  # At least 1KB
                                logger.info(f"✅ Downloaded: {video_path} ({file_size/1024/1024:.1f}MB)")
                                return video_path
                            else:
                                logger.warning(f"File too small ({file_size} bytes), retrying...")
                                os.remove(video_path)
                                continue
                        else:
                            logger.warning(f"File not found: {video_path}, trying next format...")
                            continue
                    
                except yt_dlp.utils.DownloadError as e:
                    if 'format' in str(e).lower():
                        logger.warning(f"Format '{fmt}' failed, trying next...")
                        continue
                    else:
                        logger.error(f"Download error: {e}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying ({attempt+2}/{max_retries})...")
                            continue
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1} with format '{fmt}' failed: {e}")
                    continue
        
        logger.error(f"All download attempts failed after {max_retries} retries")
        return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video metadata without downloading"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        'title': info.get('title', ''),
                        'duration': info.get('duration', 0),
                        'description': info.get('description', ''),
                        'uploader': info.get('uploader', ''),
                        'view_count': info.get('view_count', 0),
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
