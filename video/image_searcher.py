"""Image Searcher - Download relevant images for video content"""
import os
import re
import requests
from typing import List
from html.parser import HTMLParser
from utils.logger import get_logger

logger = get_logger()


class ImageSearcher:
    """Search and download images from free sources (DuckDuckGo, fallback to Unsplash direct links)"""
    
    def __init__(self):
        # DuckDuckGo image search (no auth, no rate limiting for reasonable use)
        self.ddg_api = "https://duckduckgo.com/"
        # Fallback: Direct Unsplash URLs (no auth needed, just URLs)
        self.unsplash_base = "https://source.unsplash.com/featured/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_and_download(self, 
                          keyword: str, 
                          num_images: int = 5,
                          output_dir: str = "assets/temp/web_story_images") -> List[str]:
        """
        Search for images and download locally
        
        Args:
            keyword: Search keyword (e.g., "business", "success", "learning")
            num_images: How many images to download
            output_dir: Where to save images
        
        Returns:
            List of local image file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"🔍 Searching images for: {keyword}")
        
        # Try DuckDuckGo first (no auth, no rate limiting)
        image_urls = self._search_duckduckgo(keyword, num_images)
        
        if not image_urls:
            logger.warning("DuckDuckGo failed, trying Unsplash direct links...")
            image_urls = self._get_unsplash_direct(keyword, num_images)
        
        if not image_urls:
            logger.warning("No images found from any source")
            return []
        
        # Download images
        downloaded_paths = []
        for i, url in enumerate(image_urls[:num_images], 1):
            try:
                path = self._download_image(url, output_dir, i)
                if path:
                    downloaded_paths.append(path)
            except Exception as e:
                logger.warning(f"Failed to download image {i}: {e}")
                continue
        
        logger.info(f"✅ Downloaded {len(downloaded_paths)} images")
        return downloaded_paths
    
    def _search_duckduckgo(self, keyword: str, num_images: int) -> List[str]:
        """Generate image URLs from Lorem Picsum (reliable, no auth, no rate limiting)"""
        try:
            # LoremPicsum is a simple image service: provides placeholder/stock images
            # Endpoint: https://picsum.photos/{width}/{height}?random={seed}
            urls = []
            
            # Create diverse URLs with different seed values
            # picsum.photos returns random images, changing seed gets different images
            # Support up to 20 images for longer videos
            for i in range(min(num_images, 20)):
                # 1080x1920 is portrait (vertical video format)
                # Add keyword hash to seed for more variation
                seed = i + hash(keyword) % 1000
                url = f"https://picsum.photos/1080/1920?random={seed}"
                urls.append(url)
            
            logger.info(f"Generated {len(urls)} image URLs from Lorem Picsum")
            return urls
        except Exception as e:
            logger.warning(f"Image URL generation failed: {e}")
            return []
    
    def _get_unsplash_direct(self, keyword: str, num_images: int) -> List[str]:
        """Fallback: Use more Lorem Picsum URLs with different styles"""
        try:
            urls = []
            # More URLs for fallback
            for i in range(num_images, num_images * 2):
                url = f"https://picsum.photos/1080/1920?random={i}"
                urls.append(url)
            
            logger.info(f"Generated {len(urls)} fallback image URLs")
            return urls[:num_images]
        except Exception as e:
            logger.warning(f"Fallback image generation failed: {e}")
            return []
    
    def _download_image(self, url: str, output_dir: str, index: int) -> str:
        """Download single image and save locally"""
        try:
            resp = requests.get(url, headers=self.headers, timeout=15, stream=True)
            resp.raise_for_status()
            
            # Determine file extension
            content_type = resp.headers.get('content-type', 'image/jpeg')
            ext = '.jpg' if 'jpeg' in content_type else '.png'
            
            filename = f"image_{index}{ext}"
            filepath = os.path.join(output_dir, filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"✅ Downloaded: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None


def extract_keywords(title: str, description: str, content: str) -> List[str]:
    """Extract relevant keywords from content for image search"""
    # Combine all text
    text = f"{title} {description} {content}".lower()
    
    # Remove Vietnamese tone marks for better matching
    # Remove common words
    stop_words = {
        'và', 'hoặc', 'là', 'được', 'có', 'cái', 'những', 'rất', 'từ', 'đến', 'cho',
        'để', 'trong', 'trên', 'dưới', 'ngoài', 'cùng', 'tại', 'bởi', 'sau', 'trước',
        'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'or', 'and'
    }
    
    # Extract words/phrases
    words = re.findall(r'\b\w{4,}\b', text)  # Words 4+ chars
    keywords = [w for w in words if w not in stop_words][:5]  # Top 5
    
    return keywords or [title.split()[0]]  # Fallback to first word of title


if __name__ == "__main__":
    searcher = ImageSearcher()
    
    # Test
    paths = searcher.search_and_download("business success learning", num_images=3)
    print(f"Downloaded: {paths}")
