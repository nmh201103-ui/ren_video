"""Custom Streaming Extractors - Extract direct video URLs from embed pages"""
import re
import requests
from urllib.parse import urlparse
from utils.logger import get_logger

logger = get_logger()


class StreamingExtractor:
    """Extract direct video URLs from streaming embed pages"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://google.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def extract(self, url: str) -> str:
        """
        Extract direct video URL from embed page
        Args:
            url: Embed page URL
        Returns:
            Direct video URL (.m3u8 or .mp4)
        Raises:
            ValueError: If extraction fails
        """
        domain = urlparse(url).netloc
        
        # Try different extractors based on domain
        if 'opstream' in domain:
            return self._extract_opstream(url)
        elif 'vimeo' in domain or 'youtube' in domain or 'youtu.be' in domain:
            # These should be handled by yt-dlp
            raise ValueError("Use yt-dlp for this domain")
        else:
            # Generic extraction
            return self._extract_generic(url)
    
    def _extract_opstream(self, url: str) -> str:
        """Extract video from opstream embed"""
        try:
            logger.info(f"🔍 Extracting from opstream embed: {url}")
            
            # Fetch embed page
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Try multiple patterns to find video URL
            patterns = [
                # M3U8 playlist
                r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                # MP4 source
                r'["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
                # Video URL in player config
                r'sources?:\s*\[?\s*["\']([^"\']+)["\']',
                # File parameter
                r'file:\s*["\']([^"\']+)["\']',
                # Source tag
                r'<source[^>]+src=["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    # Filter out ads, thumbnails, subtitles
                    if any(skip in match.lower() for skip in ['ads', 'thumb', 'subtitle', 'caption', '.vtt', '.srt']):
                        continue
                    
                    # Check if it's a valid video URL
                    if match.endswith(('.m3u8', '.mp4', '.webm')):
                        logger.info(f"✅ Found video URL: {match[:80]}...")
                        return match
            
            # Try to find iframe with video source
            iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\']'
            iframes = re.findall(iframe_pattern, html, re.IGNORECASE)
            for iframe_url in iframes:
                if 'opstream' in iframe_url or any(x in iframe_url.lower() for x in ['player', 'embed', 'video']):
                    # Recursive extraction from iframe
                    logger.info(f"🔄 Following iframe: {iframe_url[:60]}...")
                    if iframe_url.startswith('//'):
                        iframe_url = 'https:' + iframe_url
                    elif iframe_url.startswith('/'):
                        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        iframe_url = base + iframe_url
                    
                    try:
                        return self._extract_opstream(iframe_url)
                    except:
                        continue
            
            raise ValueError("Could not find video URL in page")
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch embed page: {e}")
    
    def _extract_generic(self, url: str) -> str:
        """Generic extraction for unknown streaming sites"""
        try:
            logger.info(f"🔍 Attempting generic extraction: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Look for common video patterns
            patterns = [
                r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                r'["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
                r'file:\s*["\']([^"\']+)["\']',
                r'<source[^>]+src=["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if match.endswith(('.m3u8', '.mp4', '.webm')):
                        logger.info(f"✅ Found video URL: {match[:80]}...")
                        return match
            
            raise ValueError("Could not extract video URL")
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch page: {e}")
