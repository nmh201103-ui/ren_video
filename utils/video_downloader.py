"""Video URL Downloader - Download video from URL using yt-dlp"""
import os
import tempfile
from pathlib import Path
from utils.logger import get_logger

logger = get_logger()


class VideoURLDownloader:
    """Download video from URL (YouTube, Vimeo, direct links, etc.)"""
    
    def __init__(self, output_dir: str = "assets/temp/downloads"):
        """
        Initialize downloader
        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.yt_dlp = self._check_yt_dlp()
    
    def _check_yt_dlp(self):
        """Check if yt-dlp is installed and import it"""
        try:
            import yt_dlp
            logger.info(f"✅ yt-dlp available: {yt_dlp.version.__version__}")
            return yt_dlp
        except ImportError as e:
            logger.error(f"❌ yt-dlp not found: {e}")
            return None
    
    def download(self, url: str, max_duration: int = 3600) -> str:
        """
        Download video from URL
        Args:
            url: Video URL (YouTube, Vimeo, HTTP link, etc.)
            max_duration: Maximum duration in seconds (default 1 hour)
        Returns:
            Path to downloaded video file
        Raises:
            ValueError: If download fails
        """
        # Try yt-dlp first
        try:
            return self._download_with_ytdlp(url)
        except Exception as ytdlp_error:
            logger.warning(f"yt-dlp failed: {ytdlp_error}")
            
            # Fallback to custom streaming extractor
            logger.info("🔄 Trying custom streaming extractor...")
            try:
                from utils.streaming_extractor import StreamingExtractor
                extractor = StreamingExtractor()
                video_url = extractor.extract(url)
                
                # Download the extracted direct video URL
                return self._download_direct(video_url)
            
            except Exception as custom_error:
                logger.error(f"Custom extractor failed: {custom_error}")
                raise ValueError(
                    f"Failed to download video from both methods:\n"
                    f"1. yt-dlp: {str(ytdlp_error)}\n"
                    f"2. Custom extractor: {str(custom_error)}\n\n"
                    f"Supported: YouTube, Vimeo, direct .mp4, streaming embeds\n"
                    f"Alternative: Upload local .mp4 file"
                )
    
    def _download_with_ytdlp(self, url: str) -> str:
        """Download using yt-dlp"""
    def _download_with_ytdlp(self, url: str) -> str:
        """Download using yt-dlp"""
        if not self.yt_dlp:
            raise ValueError("yt-dlp not installed")
        
        logger.info(f"📥 Downloading with yt-dlp: {url}")
        
        # Generate output filename
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        output_template = os.path.join(self.output_dir, f"video_{timestamp}.%(ext)s")
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        # Download
        with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        if not os.path.exists(filename):
            raise ValueError("Downloaded file not found")
        
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        logger.info(f"✅ Downloaded: {os.path.basename(filename)} ({file_size_mb:.1f} MB)")
        return filename
    
    def _download_direct(self, url: str) -> str:
        """Download direct video URL (M3U8 or MP4)"""
        logger.info(f"📥 Downloading direct URL: {url[:80]}...")
        
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Check if M3U8 playlist
        if '.m3u8' in url:
            # Use yt-dlp to download M3U8 (handles segments)
            output_template = os.path.join(self.output_dir, f"video_{timestamp}.mp4")
            
            if self.yt_dlp:
                ydl_opts = {
                    'outtmpl': output_template,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                if os.path.exists(output_template):
                    file_size_mb = os.path.getsize(output_template) / (1024 * 1024)
                    logger.info(f"✅ Downloaded M3U8: {os.path.basename(output_template)} ({file_size_mb:.1f} MB)")
                    return output_template
            
            raise ValueError("Failed to download M3U8 - yt-dlp not available")
        
        else:
            # Direct MP4 download
            output_path = os.path.join(self.output_dir, f"video_{timestamp}.mp4")
            
            response = __import__('requests').get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            if int(progress) % 10 == 0:
                                logger.info(f"  Progress: {progress:.0f}%")
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ Downloaded MP4: {os.path.basename(output_path)} ({file_size_mb:.1f} MB)")
            return output_path
    
    def cleanup(self, video_path: str):
        """Delete downloaded video file"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"🗑️ Cleaned up: {os.path.basename(video_path)}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {video_path}: {e}")
