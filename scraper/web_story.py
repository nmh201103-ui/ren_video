"""Web Story/Article Scraper - Extract content from any webpage"""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class WebStoryCScraper:
    """Extract article/story content from any webpage"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape(self, url: str) -> dict:
        """
        Extract article/story content from URL
        Returns: {
            'title': str,
            'description': str,
            'content': str (full article text),
            'author': str (optional),
            'source': str,
            'url': str
        }
        """
        try:
            from utils.logger import get_logger
            logger = get_logger()
            logger.info(f"📖 Scraping web story from: {url}")
            
            # Fetch page
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'utf-8'
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Extract description/excerpt
            description = self._extract_description(soup, content)
            
            # Extract author
            author = self._extract_author(soup)
            
            # Extract domain name
            domain = urlparse(url).netloc.replace('www.', '')
            
            if not content or len(content.strip()) < 100:
                raise ValueError("No meaningful content found in page")
            
            logger.info(f"✅ Extracted: {title[:50]}... ({len(content)} chars)")
            
            # Auto-download relevant images
            logger.info("🖼️ Searching for relevant images...")
            try:
                from video.image_searcher import ImageSearcher, extract_keywords
                searcher = ImageSearcher()
                keywords = extract_keywords(title, description, content)
                keyword_str = " ".join(keywords[:3])
                
                # Estimate number of images needed based on content length
                # Assume ~20-30 seconds per scene, ~150 words
                word_count = len(content.split())
                estimated_scenes = max(10, min(20, word_count // 150))  # 10-20 scenes
                
                logger.info(f"📊 Estimated {estimated_scenes} scenes, downloading {estimated_scenes} images")
                image_paths = searcher.search_and_download(keyword_str, num_images=estimated_scenes)
            except Exception as e:
                logger.warning(f"Image search failed: {e}, continuing without images")
                image_paths = []
            
            return {
                'title': title or 'Untitled Story',
                'description': description,
                'content': content,
                'author': author,
                'source': domain,
                'url': url,
                'type': 'story',
                'image_urls': image_paths  # Add downloaded images
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to scrape {url}: {e}")
            raise ValueError(f"Failed to fetch content: {str(e)}")
    
    def _extract_title(self, soup) -> str:
        """Extract page title"""
        # Try common title locations
        title = None
        
        # og:title meta tag
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '')
        
        # <title> tag
        if not title or len(title) < 5:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # h1 tag
        if not title or len(title) < 5:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        # Clean up
        if title:
            title = title.replace(' | ', ' ').replace(' - ', ' ').strip()
            title = title[:100]  # Limit length
        
        return title or 'Story'
    
    def _extract_content(self, soup) -> str:
        """Extract main article text"""
        # Remove script and style
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        # Try common article containers
        content = None
        
        for selector in ['article', '[role="main"]', '.post-content', '.entry-content', 
                         '.article-content', '.content', 'main']:
            container = soup.select_one(selector)
            if container:
                content = self._extract_text_from_container(container)
                if len(content) > 500:
                    break
        
        # Fallback: get all paragraphs
        if not content or len(content) < 500:
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
        
        # Clean up
        content = self._clean_text(content)
        
        return content[:5000]  # Limit to 5000 chars
    
    def _extract_text_from_container(self, container) -> str:
        """Extract clean text from HTML container"""
        # Get all text nodes
        text_parts = []
        for elem in container.find_all(['p', 'h2', 'h3', 'li']):
            text = elem.get_text(strip=True)
            if text and len(text) > 20:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def _extract_description(self, soup, content: str) -> str:
        """Extract meta description or generate from content"""
        # og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '')
        
        # meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        # First 200 chars of content
        if content:
            desc = content.replace('\n\n', ' ')
            desc = re.sub(r'\s+', ' ', desc)
            return desc[:200]
        
        return ''
    
    def _extract_author(self, soup) -> str:
        """Extract author name if available"""
        # og:author
        og_author = soup.find('meta', property='og:author')
        if og_author:
            return og_author.get('content', '')
        
        # article:author
        art_author = soup.find('meta', property='article:author')
        if art_author:
            return art_author.get('content', '')
        
        # Look for common author patterns
        for selector in ['.author-name', '.by-author', '[rel="author"]']:
            author = soup.select_one(selector)
            if author:
                return author.get_text(strip=True)[:50]
        
        return ''
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove common web clutter
        text = re.sub(r'\[.*?\]', '', text)  # Remove [brackets]
        text = re.sub(r'\(Photo:.*?\)', '', text)
        return text.strip()
