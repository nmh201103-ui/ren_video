import re
import time
from typing import Dict, List
from playwright.sync_api import sync_playwright
from scraper.base import BaseScraper
from utils.logger import get_logger

logger = get_logger()

class ShopeeScraper(BaseScraper):
    MAX_DESC_RETRIES = 6
    SCROLL_STEP = 750 

    def scrape(self, url: str) -> Dict:
        logger.info(f"🔗 Kết nối tới Chrome (9222)...")
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                page = next((pg for pg in context.pages if "shopee.vn" in pg.url), None)
                if not page:
                    page = context.new_page()

                # Cấu hình User-Agent hiện đại
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                page.set_extra_http_headers({"User-Agent": ua})

                if url not in page.url:
                    page.goto(url, wait_until="commit", timeout=60000)
                
                # CHỜ ẢNH LOAD: Đợi container ảnh chính xuất hiện
                try:
                    page.wait_for_selector('img[src*="shopee.com"], div[style*="background-image"]', timeout=8000)
                except:
                    pass
                
                page.wait_for_timeout(2500) # Chờ thêm cho các ảnh lazy-load hiện ra

                # --- BƯỚC 1: LẤY ẢNH + TITLE + PRICE NGAY LẬP TỨC ---
                title = self._get_title(page) or "Sản phẩm Shopee"
                price = self._get_price(page)
                
                # Sử dụng logic nâng cao kết hợp cả code cũ và code mới
                images = self._get_images_advanced(page)
                
                if not images:
                    logger.warning("⚠️ Không tìm thấy ảnh qua DOM, thử quét Regex...")
                    images = self._get_images_regex(page)

                logger.info(f"✅ Đã lấy xong dữ liệu đầu trang: {len(images)} ảnh, {title}")

                # --- BƯỚC 2: SCROLL XUỐNG ĐỂ LẤY MÔ TẢ ---
                description = ""
                for attempt in range(self.MAX_DESC_RETRIES):
                    description = self._get_description_logic(page)
                    if len(description) > 50:
                        logger.info(f"✅ Lấy thành công mô tả sau {attempt+1} lần scroll.")
                        break
                    
                    logger.info(f"⚠️ Đang tìm mô tả... (Lần {attempt+1})")
                    # Dùng mouse.wheel để giả lập người dùng thật cuộn trang
                    page.mouse.wheel(0, self.SCROLL_STEP)
                    page.wait_for_timeout(1200)

                # --- BƯỚC 3: ĐÓNG GÓI DỮ LIỆU ---
                data = {
                    "title": title,
                    "price": price,
                    "image_urls": images,
                    "description": description if description.strip() else "Sản phẩm tuyệt vời với giá ưu đãi cực tốt.",
                    "platform": "shopee",
                    "original_url": url,
                }

                logger.info(f"✅ DONE | Ảnh: {len(data['image_urls'])} | Mô tả: {len(data['description'])} ký tự")
                return data

            except Exception as e:
                logger.error(f"❌ Scraper Error: {e}")
                return self._empty(url)

    def _get_title(self, page) -> str:
        try:
            # Lấy title sạch nhất từ OpenGraph hoặc page.title()
            og_title = page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.content")
            if og_title: return og_title.split('|')[0].strip()
            return page.title().split('|')[0].strip()
        except: return ""

    def _get_price(self, page) -> str:
        try:
            # Thử lấy giá từ metadata trước (luôn chính xác và không bị format lạ)
            meta_price = page.evaluate("document.querySelector('meta[property=\"product:price:amount\"]')?.content")
            if meta_price: 
                return f"{int(float(meta_price)):,}₫".replace(",", ".")
            
            # Nếu meta không có, tìm trên giao diện
            for selector in [".G27FPX", ".pmmxKx", ".IZPeQz"]:
                price_el = page.locator(selector).first
                if price_el.is_visible():
                    return price_el.inner_text().split('\n')[0].strip()
            return "Giá tốt"
        except: return "0"

    def _get_images_advanced(self, page) -> List[str]:
        """Lấy toàn bộ ảnh sản phẩm: Kết hợp logic 'usercontent' cũ và 'shopee.com' mới"""
        return page.evaluate("""() => {
            const results = new Set();
            
            // 1. Ưu tiên lấy ảnh đại diện chính từ Meta Tag
            const ogImg = document.querySelector('meta[property="og:image"]')?.content;
            if (ogImg) results.add(ogImg.split('@')[0]);

            // 2. Quét các selectors ảnh sản phẩm
            const selectors = [
                'div[style*="background-image"]', 
                'img[src*="shopee.com/file/"]', 
                'img[src*="usercontent.com"]',
                '.V63p_R img'
            ];
            
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    let url = '';
                    if (el.tagName === 'IMG') {
                        url = el.getAttribute('data-src') || el.src || '';
                    } else {
                        const bg = el.style.backgroundImage;
                        url = bg.replace(/url\(["']?|["']?\)/g, '');
                    }
                    
                    // Lọc bỏ rác
                    if (!url || url.includes('.svg') || url.includes('icon')) return;

                    // Logic làm sạch link ảnh (Xử lý cả @ của usercontent và _tn của shopee)
                    // Tách @ để lấy link gốc từ usercontent, tách _ để bỏ thumbnail từ shopee
                    let cleanUrl = url.split('@')[0].split('_tn')[0].split('_v')[0];
                    
                    if (!cleanUrl.startsWith('http')) cleanUrl = 'https:' + cleanUrl;
                    
                    if (cleanUrl.includes('shopee.com/file/') || cleanUrl.includes('usercontent.com')) {
                        results.add(cleanUrl);
                    }
                });
            });
            
            return Array.from(results).slice(0, 10);
        }""")

    def _get_images_regex(self, page) -> List[str]:
        try:
            content = page.content()
            # Regex bắt cả 2 loại domain ảnh
            pattern = r'(?:down-vn\.img\.shopee\.com/file/|cf\.shopee\.vn/file/|down-vn\.img\.shopee\.vn/file/)([a-z0-9A-Z_-]+)'
            matches = re.findall(pattern, content)
            urls = []
            for m in matches:
                if len(m) >= 30: # ID ảnh Shopee thường rất dài
                    url = f"https://down-vn.img.shopee.com/file/{m}"
                    if url not in urls: urls.append(url)
            return urls[:10]
        except: return []

    def _get_description_logic(self, page) -> str:
        try:
            # Lấy text từ khối section có chứa tiêu đề mô tả
            section = page.locator('section:has(h2:has-text("MÔ TẢ SẢN PHẨM"))').first
            if not section.is_visible():
                # Thử tìm theo cấu trúc khác nếu cấu trúc trên thất bại
                section = page.locator('div:has(> h2:has-text("MÔ TẢ SẢN PHẨM"))').first
            
            if not section.is_visible(): return ""
            
            raw_text = section.inner_text()
            lines = [l.strip() for l in raw_text.split('\n') if len(l.strip()) > 3]
            
            # Loại bỏ tiêu đề "MÔ TẢ SẢN PHẨM" ở dòng đầu tiên
            if lines and "MÔ TẢ SẢN PHẨM" in lines[0].upper():
                lines = lines[1:]
            
            return "\n".join(lines)
        except:
            return ""

    def _empty(self, url: str) -> Dict:
        return {
            "title": "Sản phẩm Shopee",
            "price": "Giá tốt",
            "image_urls": [],
            "description": "Sản phẩm chất lượng cao, cam kết chính hãng.",
            "platform": "shopee",
            "original_url": url,
        }