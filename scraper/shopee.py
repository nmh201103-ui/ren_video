import re
import time
from typing import Dict, List
from playwright.sync_api import sync_playwright
from scraper.base import BaseScraper
from utils.logger import get_logger

logger = get_logger()

class ShopeeScraper(BaseScraper):
    MAX_DESC_RETRIES = 6
    SCROLL_STEP = 900 

    def scrape(self, url: str) -> Dict:
        logger.info(f"🔗 Kết nối tới Chrome (9222) - URL: {url}")
        with sync_playwright() as p:
            try:
                # Kết nối browser hiện tại
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                
                # Tìm tab shopee hoặc tạo mới
                page = next((pg for pg in context.pages if "shopee.vn" in pg.url), None)
                if not page:
                    page = context.new_page()

                # Giả lập User-Agent xịn
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                page.set_extra_http_headers({"User-Agent": ua})

                # Chuyển trang nếu cần
                if url not in page.url:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                page.wait_for_timeout(2000) 

                # Lấy Title và Ảnh trước
                title = self._get_title(page)
                images = self._get_images_advanced(page)

                # --- CHIẾN THUẬT LẤY MÔ TẢ ĐA TẦNG ---
                description = ""
                for attempt in range(self.MAX_DESC_RETRIES):
                    # Cuộn chuột để Shopee render phần Description (Lazy load)
                    page.mouse.wheel(0, self.SCROLL_STEP)
                    page.wait_for_timeout(1200)
                    
                    description = self._get_description_logic(page)
                    if len(description) > 150: # Đã lấy đủ nội dung dài
                        break
                
                # Fallback: Nếu cuộn không ra, lấy từ Meta Description (Dù ngắn nhưng vẫn có chữ)
                if len(description) < 50:
                    logger.warning("⚠️ Không tìm thấy selector mô tả, thử lấy từ Meta tags...")
                    description = page.evaluate("document.querySelector('meta[name=\"description\"]')?.content") or ""

                # Làm sạch dữ liệu
                clean_desc = description.replace("MÔ TẢ SẢN PHẨM", "").strip()

                # --- LOG XUẤT XƯỞNG (XÁC NHẬN CHÍNH XÁC KÝ TỰ) ---
                print("\n" + "🚀" * 15)
                print(f"[SCRAPER SUCCESS]")
                print(f"Title: {title[:50]}...")
                print(f"Ảnh: {len(images)} tấm")
                print(f"Mô tả gốc: {len(clean_desc)} ký tự")
                print("🚀" * 15 + "\n")

                # --- ĐÓNG GÓI DỮ LIỆU ĐA KEY (BẢO VỆ DỮ LIỆU) ---
                # Chúng ta trả về cả 2 key để Renderer không bao giờ bị rỗng
                return {
                    "title": title,
                    "image_urls": images,
                    "description": clean_desc,        # Key chính
                    "short_description": clean_desc,  # Key dự phòng cho renderer/main.py
                    "platform": "shopee",
                    "original_url": url,
                    "price": self._get_price_simple(page)
                }

            except Exception as e:
                logger.error(f"❌ Scraper Error: {e}")
                return self._empty_data(url)

    def _get_description_logic(self, page) -> str:
        try:
            # Ép Shopee hiển thị nội dung bằng cách click hoặc chờ selector cụ thể
            return page.evaluate("""() => {
                // Thử tìm tất cả các thẻ có khả năng chứa mô tả
                const selectors = [
                    'div.p_7rWz', 
                    '.product-detail__renderer',
                    'div.product-details__section > font',
                    'div._3yZ_0n',
                    'section:has(h2:has-text("MÔ TẢ SẢN PHẨM")) div'
                ];
                
                for (let sel of selectors) {
                    const el = document.querySelector(sel);
                    // Nếu tìm thấy và nội dung đủ dài thì lấy
                    if (el && el.innerText.length > 100) return el.innerText;
                }
                return "";
            }""")
        except:
            return ""

    def _get_title(self, page) -> str:
        try:
            t = page.title().split('|')[0].strip()
            if not t or t == "Shopee":
                t = page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.content") or "Sản phẩm Shopee"
            return t
        except:
            return "Sản phẩm Shopee"

    def _get_images_advanced(self, page) -> List[str]:
        try:
            return page.evaluate("""() => {
                const urls = new Set();
                // Tìm tất cả ảnh sản phẩm, bỏ qua các icon nhỏ
                document.querySelectorAll('img').forEach(img => {
                    let src = img.getAttribute('data-src') || img.src;
                    if (src && (src.includes('usercontent') || src.includes('shopee.com/file/'))) {
                        // Làm sạch URL để lấy ảnh gốc chất lượng cao
                        let clean = src.split('@')[0].split('_tn')[0].split('_v')[0];
                        if (!clean.startsWith('http')) clean = 'https:' + clean;
                        urls.add(clean);
                    }
                });
                return Array.from(urls).slice(0, 10);
            }""")
        except:
            return []

    def _get_price_simple(self, page) -> str:
        try:
            return page.evaluate("document.querySelector('meta[property=\"product:price:amount\"]')?.content") or "0"
        except:
            return "0"

    def _empty_data(self, url: str) -> Dict:
        return {
            "title": "Sản phẩm",
            "image_urls": [],
            "description": "Nội dung đang cập nhật",
            "short_description": "Nội dung đang cập nhật",
            "platform": "shopee",
            "original_url": url
        }