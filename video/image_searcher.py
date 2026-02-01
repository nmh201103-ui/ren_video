"""Image Searcher - Download relevant images for video content"""
import os
import re
import requests
from typing import List
from urllib.parse import quote_plus
from utils.logger import get_logger

logger = get_logger()


class ImageSearcher:
    """Search and download images from multiple sources: Bing, Pexels, Picsum"""
    
    def __init__(self, pexels_api_key: str = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Pexels API (optional, 200 requests/hour free)
        self.pexels_api_key = pexels_api_key or os.getenv("PEXELS_API_KEY")
    
    def search_and_download(self, 
                          keyword: str, 
                          num_images: int = 5,
                          output_dir: str = "assets/temp/web_story_images",
                          referer: str = None,
                          start_index: int = 1) -> List[str]:
        """Search and download images - tries Bing first, then Pexels, finally placeholders"""
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"🔍 Searching images for: {keyword}")
        
        # Try Bing Images (primary, no API key needed)
        downloaded = self._try_bing(keyword, num_images, output_dir, start_index)
        if downloaded:
            return downloaded
        
        # Try Pexels API if available
        if self.pexels_api_key:
            image_urls = self._search_pexels(keyword, num_images)
            if image_urls:
                downloaded = self._download_batch(image_urls, output_dir, start_index, referer)
                if downloaded:
                    return downloaded
        
        # Fallback: Picsum placeholders
        logger.warning("⚠️ All sources failed, using placeholders")
        image_urls = [f"https://picsum.photos/1080/1920?random={i}" for i in range(start_index, start_index + num_images)]
        return self._download_batch(image_urls, output_dir, start_index, referer)
    
    def search_google_images(self, query: str, num_images: int = 1, output_dir: str = "assets/temp/web_story_images", index: int = 1) -> List[str]:
        """Alias for Bing image download"""
        return self._try_bing(query, num_images, output_dir, index) or []
    
    def _try_bing(self, query: str, num_images: int, output_dir: str, start_index: int) -> List[str]:
        """Download images using Bing Image Downloader"""
        try:
            from bing_image_downloader import downloader
            import shutil
            
            # Sanitize query to avoid invalid Windows path characters and overly long names
            safe_query = self._sanitize_query(query)
            logger.info(f"📸 Bing Images: {query}")
            if safe_query != query:
                logger.info(f"   ↳ Sanitized for filesystem: {safe_query}")

            downloader.download(
                safe_query,
                limit=num_images,
                output_dir="dataset",
                adult_filter_off=True,
                force_replace=True,
                timeout=15,
                verbose=False,
                filter=''
            )
            
            # Find downloaded images
            dataset_path = os.path.join("dataset", safe_query.replace(" ", "_"))
            if not os.path.exists(dataset_path):
                # Try finding folder by first word of sanitized query only (no random "latest" folder)
                first_word = safe_query.split()[0].lower() if safe_query.split() else ""
                for folder in os.listdir("dataset") if os.path.exists("dataset") else []:
                    if folder.lower().startswith(first_word):
                        dataset_path = os.path.join("dataset", folder)
                        break
                # Do NOT use "latest dataset folder" - that reuses unrelated old images and breaks story sync
            
            if os.path.exists(dataset_path):
                images = [f for f in os.listdir(dataset_path) if f.endswith(('.jpg', '.png', '.jpeg'))][:num_images]
                if images:
                    os.makedirs(output_dir, exist_ok=True)
                    downloaded = []
                    for idx, img_name in enumerate(images, start_index):
                        src = os.path.join(dataset_path, img_name)
                        dest = os.path.normpath(os.path.join(output_dir, f"image_{idx}.jpg"))
                        shutil.copy2(src, dest)
                        downloaded.append(dest)
                        logger.info(f"✅ Bing: {os.path.basename(dest)}")
                    return downloaded
            
            # Retry with shorter query
            if len(safe_query.split()) > 3:
                short_query = ' '.join(safe_query.split()[:3])
                logger.info(f"🔄 Retry with: {short_query}")
                return self._try_bing(short_query, num_images, output_dir, start_index)
                
        except ImportError as e:
            logger.warning(f"⚠️ Bing import failed: {e}")
        except Exception as e:
            logger.error(f"❌ Bing failed: {type(e).__name__}: {e}")
        
        return []

    def _sanitize_query(self, query: str) -> str:
        """Make query safe for Windows filesystem and Bing downloader.
        - Remove invalid path chars: <>:"/\|?*
        - Trim punctuation at ends
        - Collapse whitespace
        - Limit to first 6 words to avoid very long folder names
        """
        # Remove invalid filesystem characters
        safe = re.sub(r'[<>:"/\\|?*]+', ' ', query)
        # Remove excessive punctuation
        safe = re.sub(r'\s+[.,;:!?]+', ' ', safe)
        safe = re.sub(r'^[.,;:!?]+|[.,;:!?]+$', '', safe).strip()
        # Collapse whitespace
        safe = re.sub(r'\s+', ' ', safe)
        # Limit length by words
        parts = safe.split()
        if len(parts) > 6:
            safe = ' '.join(parts[:6])
        return safe
    
    def _search_pexels(self, keyword: str, num_images: int) -> List[str]:
        """Search Pexels API for free stock photos (200 requests/hour)"""
        try:
            headers = {
                'Authorization': self.pexels_api_key,
                'User-Agent': self.headers['User-Agent']
            }
            
            url = f"https://api.pexels.com/v1/search?query={quote_plus(keyword)}&per_page={num_images}&orientation=portrait"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            urls = [photo['src']['large2x'] for photo in data.get('photos', [])]
            
            if urls:
                logger.info(f"✅ Pexels: Found {len(urls)} images")
            return urls
            
        except Exception as e:
            logger.warning(f"⚠️ Pexels failed: {e}")
            return []
    
    def _download_batch(self, urls: List[str], output_dir: str, start_index: int, referer: str = None) -> List[str]:
        """Download multiple images from URLs"""
        downloaded = []
        for idx, url in enumerate(urls, start_index):
            try:
                path = self._download_image(url, output_dir, idx, referer)
                if path:
                    downloaded.append(path)
            except Exception as e:
                logger.warning(f"⚠️ Download failed ({idx}): {e}")
        
        logger.info(f"✅ Downloaded {len(downloaded)}/{len(urls)} images")
        return downloaded
    
    def _download_image(self, url: str, output_dir: str, index: int, referer: str = None) -> str:
        """Download and convert single image to JPEG"""
        try:
            # Skip invalid URLs
            if not url or url.startswith(('data:', 'javascript:', 'about:')):
                return None
            
            # Quick domain typo fix for known source
            if 'quantrimang.comm' in url:
                url = url.replace('quantrimang.comm', 'quantrimang.com')
            
            # Fetch image
            headers = dict(self.headers)
            if referer:
                headers['Referer'] = referer
            
            resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            resp.raise_for_status()
            
            # Validate Content-Type
            content_type = resp.headers.get('content-type', '').lower()
            if 'image' not in content_type:
                logger.warning(f"⚠️ Not an image: {content_type}")
                return None
            # Skip SVG (Pillow cannot open SVG)
            if 'svg' in content_type:
                logger.warning("⚠️ Skipping SVG image (unsupported by Pillow)")
                return None
            
            # Convert to JPEG
            from PIL import Image
            from io import BytesIO
            
            img = Image.open(BytesIO(resp.content))
            
            # Handle transparency (WebP, PNG, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            filename = f"image_{index}.jpg"
            filepath = os.path.normpath(os.path.join(output_dir, filename))
            os.makedirs(output_dir, exist_ok=True)
            
            img.save(filepath, 'JPEG', quality=90, optimize=True)
            logger.info(f"✅ {filename} ({os.path.getsize(filepath)} bytes)")
            return filepath
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to download {url}: {type(e).__name__}")
            return None


def extract_keywords(title: str, description: str, content: str) -> List[str]:
    """Extract keywords for image search (Vietnamese → English concept mapping)"""
    text = f"{title} {title} {description}".lower()
    
    # Map Vietnamese concepts to English for better image search
    concept_map = {
        'thành công': 'success', 'kinh doanh': 'business', 'học': 'learning',
        'tiền': 'money', 'sống': 'lifestyle', 'người': 'people',
        'công việc': 'work', 'gia đình': 'family', 'sức khỏe': 'health',
        'hạnh phúc': 'happiness', 'khôn ngoan': 'wisdom', 'bài học': 'lesson',
        'kinh nghiệm': 'experience', 'đầu tư': 'investment', 'phát triển': 'growth'
    }
    
    keywords = []
    for vn_word, en_word in concept_map.items():
        if vn_word in text and en_word not in keywords:
            keywords.append(en_word)
            if len(keywords) >= 5:
                break
    
    return keywords[:5] or ['lifestyle', 'inspiration']


if __name__ == "__main__":
    searcher = ImageSearcher()
    paths = searcher.search_and_download("business success", num_images=3)
    print(f"Downloaded: {paths}")
