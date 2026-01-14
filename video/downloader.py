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
    
    def download(self, url: str) -> Optional[str]:
        """
        Download video from URL
        Returns: path to downloaded video file
        """
        try:
            # Check if yt-dlp is installed as module
            try:
                import yt_dlp
            except ImportError:
                logger.error("yt-dlp not installed. Install: pip install yt-dlp")
                return None
            
            logger.info(f"📥 Downloading video from: {url}")
            
            # Output template
            output_template = os.path.join(self.output_dir, "%(id)s.%(ext)s")
            
            # Use yt-dlp as Python module
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': output_template,
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    video_id = info.get('id', 'video')
                    ext = info.get('ext', 'mp4')
                    video_path = os.path.join(self.output_dir, f"{video_id}.{ext}")
                    
                    if os.path.exists(video_path):
                        logger.info(f"✅ Downloaded: {video_path}")
                        return video_path
                    else:
                        logger.error(f"Video file not found: {video_path}")
                        return None
            
            return None
                
        except Exception as e:
            logger.error(f"Download error: {e}")
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
