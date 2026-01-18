"""Web Story/Article Scraper - Extract content from any webpage"""
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class WebStoryCScraper:
    """Extract article/story content from any webpage"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        # Create session for connection pooling and retry
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
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
            import time
            logger = get_logger()
            logger.info(f"📖 Scraping web story from: {url}")
            
            # Fetch page with retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"🌐 Attempt {attempt + 1}/{max_retries}...")
                    resp = self.session.get(
                        url, 
                        timeout=20,
                        verify=True,  # Verify SSL
                        allow_redirects=True
                    )
                    resp.encoding = 'utf-8'
                    resp.raise_for_status()
                    break  # Success
                except (requests.exceptions.ConnectionError, 
                        requests.exceptions.SSLError,
                        requests.exceptions.Timeout) as conn_err:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"⚠️ Connection failed: {conn_err}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise on final attempt
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Debug: Save HTML if DEBUG env is set
            if os.getenv("DEBUG_SCRAPER"):
                debug_file = "debug_scraped.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                logger.info(f"🐛 Debug: Saved HTML to {debug_file}")
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # If content is too short, try robust JS-free extractors first
            if not content or len(content.strip()) < 100:
                # Fallback A: newspaper3k
                try:
                    from newspaper import Article
                    art = Article(url)
                    art.set_html(resp.text)
                    art.download_state = 2  # mark as downloaded
                    art.parse()
                    if hasattr(art, 'text') and len(art.text.strip()) > 300:
                        content = art.text
                        logger.info(f"✅ newspaper3k extracted {len(content)} chars")
                except Exception as e:
                    logger.debug(f"newspaper3k not available or failed: {e}")
                
                # Fallback B: trafilatura
                if not content or len(content.strip()) < 100:
                    try:
                        import trafilatura
                        downloaded = trafilatura.fetch_url(url)
                        if downloaded:
                            extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                            if extracted and len(extracted.strip()) > 300:
                                content = extracted
                                logger.info(f"✅ trafilatura extracted {len(content)} chars")
                    except Exception as e:
                        logger.debug(f"trafilatura not available or failed: {e}")
            
            # If still short, try Selenium (JavaScript rendering)
            if not content or len(content.strip()) < 100:
                logger.warning(f"⚠️ Static scraping got {len(content) if content else 0} chars, trying Selenium...")
                try:
                    from scraper.web_story_selenium import scrape_with_selenium
                    selenium_soup = scrape_with_selenium(url, timeout=30)
                    if selenium_soup:
                        # Re-extract with Selenium-rendered content
                        content = self._extract_content(selenium_soup)
                        soup = selenium_soup
                        logger.info(f"✅ Selenium scraped {len(content)} chars")
                except ImportError:
                    logger.warning("⚠️ Selenium not installed. Install with: pip install selenium")
                except Exception as e:
                    logger.warning(f"⚠️ Selenium failed: {e}")
            
            # If still short, try Playwright (if installed)
            if not content or len(content.strip()) < 100:
                try:
                    logger.info("🌐 Trying Playwright headless Chromium...")
                    from playwright.sync_api import sync_playwright
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(url, timeout=30000, wait_until="networkidle")
                        html = page.content()
                        browser.close()
                        pw_soup = BeautifulSoup(html, 'html.parser')
                        extracted = self._extract_content(pw_soup)
                        if extracted and len(extracted.strip()) > 300:
                            content = extracted
                            soup = pw_soup
                            logger.info(f"✅ Playwright extracted {len(content)} chars")
                        else:
                            logger.warning("⚠️ Playwright rendered but content still insufficient")
                except ImportError:
                    logger.warning("⚠️ Playwright not installed. Install with: pip install playwright && playwright install")
                except Exception as e:
                    logger.warning(f"⚠️ Playwright failed: {e}")
            
            # Extract description/excerpt
            description = self._extract_description(soup, content)
            
            # Extract author
            author = self._extract_author(soup)
            
            # Extract domain name
            domain = urlparse(url).netloc.replace('www.', '')
            
            if not content or len(content.strip()) < 100:
                logger.warning(f"⚠️ Content still too short: {len(content)} chars")
                logger.debug(f"HTML title tags: {[t.name for t in soup.find_all(['h1', 'h2', 'h3'])[:5]]}")
                raise ValueError("No meaningful content found in page. Website may require JavaScript rendering. Try installing: pip install selenium")
            
            logger.info(f"✅ Extracted: {title[:50]}... ({len(content)} chars)")
            
            # Extract images from article first
            article_images = self._extract_article_images(soup, url)
            logger.info(f"📸 Found {len(article_images)} images in article")
            
            # Auto-download relevant images
            logger.info("🖼️ Searching for relevant images...")
            image_paths = []
            try:
                from video.image_searcher import ImageSearcher, extract_keywords
                searcher = ImageSearcher()
                
                # Estimate number of images needed based on content length
                word_count = len(content.split())
                estimated_scenes = max(3, min(8, word_count // 200))  # 3-8 scenes for stories
                
                # Try to download article images first
                if article_images:
                    logger.info(f"⬇️ Downloading {len(article_images[:estimated_scenes])} images from article...")
                    for idx, img_url in enumerate(article_images[:estimated_scenes], 1):
                        try:
                            path = searcher._download_image(img_url, "assets/temp/web_story_images", idx, referer=url)
                            if path:
                                image_paths.append(path)
                                logger.info(f"✅ Article image {idx} downloaded")
                        except Exception as e:
                            logger.warning(f"Failed to download article image {idx} from {img_url}: {e}")
                else:
                    logger.info("ℹ️ No images found in article HTML")
                
                # If not enough images from article, search Google Images by content
                if len(image_paths) < estimated_scenes:
                    needed = estimated_scenes - len(image_paths)
                    logger.info(f"🔍 Need {needed} more images, searching Google Images by scene text...")
                    
                    # Split content into chunks and search for each
                    chunks = content.split('\n\n')[:needed]
                    for scene_idx, chunk in enumerate(chunks, len(image_paths) + 1):
                        # Extract key phrase from chunk
                        words = chunk.split()[:15]  # First 15 words as search query
                        search_query = ' '.join(words)
                        
                        logger.info(f"🔎 Scene {scene_idx}: Searching images for: {search_query[:50]}...")
                        try:
                            # Try Google Images search
                            google_paths = searcher.search_google_images(search_query, num_images=1, output_dir="assets/temp/web_story_images", index=scene_idx)
                            if google_paths:
                                image_paths.extend(google_paths)
                                logger.info(f"✅ Scene {scene_idx} image found via Google Images")
                            else:
                                # Fallback: use generic keyword search with correct index
                                logger.info(f"⚠️ Google Images failed for scene {scene_idx}, trying keyword fallback...")
                                keywords = extract_keywords(search_query, '', '')
                                keyword_str = ' '.join(keywords[:2])
                                fallback_paths = searcher.search_and_download(keyword_str, num_images=1, output_dir="assets/temp/web_story_images", start_index=scene_idx)
                                if fallback_paths:
                                    image_paths.extend(fallback_paths)
                        except Exception as e:
                            logger.warning(f"Failed to find image for scene {scene_idx}: {e}")
                
                # Filter out None/invalid values
                image_paths = [p for p in image_paths if p and isinstance(p, str) and os.path.exists(p)]
                
                logger.info(f"✅ Total {len(image_paths)} images ready for video")
            except Exception as e:
                logger.warning(f"Image search failed: {e}, continuing without images")
                logger.exception("Full traceback:")
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
        from utils.logger import get_logger
        logger = get_logger()
        
        # Remove script and style
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
            tag.decompose()
        
        # Try common article containers (expanded list)
        content = None
        
        selectors = [
            'article', 
            '[role="main"]', 
            '.post-content', 
            '.entry-content', 
            '.article-content', 
            '.article-body',
            '.content', 
            '.story-content',
            '.post-body',
            '#content',
            '#article',
            'main',
            '.detail-content',  # ybox.vn specific
            '.article-detail',
            '[itemprop="articleBody"]',
            '.text-content'
        ]
        
        for selector in selectors:
            container = soup.select_one(selector)
            if container:
                content = self._extract_text_from_container(container)
                if len(content) > 300:
                    logger.info(f"✅ Found content in selector: {selector}")
                    break
        
        # Fallback 1: get all paragraphs
        if not content or len(content) < 300:
            logger.warning("⚠️ No container found, trying paragraphs...")
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
        
        # Fallback 2: get all divs with text
        if not content or len(content) < 300:
            logger.warning("⚠️ Paragraphs insufficient, trying all divs...")
            all_divs = soup.find_all('div')
            texts = []
            for div in all_divs:
                # Skip if div has too many children (likely container)
                if len(div.find_all()) < 3:
                    text = div.get_text(strip=True)
                    if len(text) > 50 and len(text) < 500:  # Reasonable paragraph length
                        texts.append(text)
            content = '\n\n'.join(texts)
        
        # Fallback 3: Get entire body text (last resort)
        if not content or len(content) < 200:
            logger.warning("⚠️ All methods failed, extracting body text...")
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
        
        # Clean up
        content = self._clean_text(content)
        
        logger.info(f"📊 Extracted {len(content)} chars, {len(content.split())} words")
        
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
    
    def _extract_article_images(self, soup, base_url: str) -> list:
        """Extract images from article content"""
        from urllib.parse import urljoin
        images = []
        
        # Find images in article content
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # Skip small images (icons, avatars)
            width = img.get('width')
            if width and int(width) < 300:
                continue
            
            # Make absolute URL
            if not src.startswith('http'):
                src = urljoin(base_url, src)
            
            # Skip common non-content images
            if any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'ad', 'banner']):
                continue
            
            images.append(src)
        
        return images
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove common web clutter
        text = re.sub(r'\[.*?\]', '', text)  # Remove [brackets]
        text = re.sub(r'\(Photo:.*?\)', '', text)
        return text.strip()
