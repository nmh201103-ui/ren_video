import re
import time
from typing import Dict, List
from playwright.sync_api import sync_playwright
from scraper.base import BaseScraper
from utils.logger import get_logger

logger = get_logger()

class ShopeeScraper(BaseScraper):
    MAX_DESC_RETRIES = 8  # Tăng số lần thử cuộn
    SCROLL_STEP = 1000    # Cuộn mạnh hơn để kích hoạt lazy load

    def scrape(self, url: str) -> Dict:
        logger.info(f"🔗 Kết nối tới Chrome (9222) - URL: {url}")
        with sync_playwright() as p:
            try:
                # Kết nối browser đang mở
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                
                page = next((pg for pg in context.pages if "shopee.vn" in pg.url), None)
                if not page:
                    page = context.new_page()

                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                page.set_extra_http_headers({"User-Agent": ua})

                if url not in page.url:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Đợi trang ổn định một chút
                page.wait_for_timeout(3000) 

                # 1. Lấy Title, Ảnh và Giá
                title = self._get_title(page)
                images = self._get_images_advanced(page)
                price = self._get_price(page)

                # 2. CHIẾN THUẬT QUÉT MÔ TẢ TRIỆT ĐỂ
                description = ""
                
                # Cố gắng tìm và bấm nút "Xem thêm" nếu có để Shopee bung full text
                try:
                    expand_button = page.locator('button:has-text("Xem thêm"), div:has-text("Xem thêm")').last
                    if expand_button.is_visible():
                        expand_button.click(timeout=3000)
                        page.wait_for_timeout(1000)
                except:
                    pass

                for attempt in range(self.MAX_DESC_RETRIES):
                    # Cuộn chuột sâu xuống dưới
                    page.mouse.wheel(0, self.SCROLL_STEP)
                    page.wait_for_timeout(1000)
                    
                    description = self._get_description_logic(page)
                    # Nếu lấy được trên 500 ký tự (mô tả thật thường dài) thì dừng
                    if len(description) > 500:
                        break
                
                # Fallback nếu vẫn rỗng hoặc quá ngắn
                if len(description) < 100:
                    logger.warning("⚠️ Selector chuyên sâu thất bại, lấy dữ liệu thô từ Meta hoặc Body...")
                    description = self._get_fallback_description(page)

                # 3. Làm sạch nhẹ nhàng (giữ nguyên cấu trúc xuống dòng để Renderer tách câu)
                clean_desc = description.replace("MÔ TẢ SẢN PHẨM", "").strip()

                # --- LOG KIỂM TRA ---
                logger.info('[SCRAPER COMPLETED]')
                logger.info('Title: %s', title[:60])
                logger.info('Images: %d', len(images))
                logger.info('Price: %s', price)
                logger.info('Description length: %d chars', len(clean_desc))

                return {
                    "title": title,
                    "image_urls": images,
                    "description": clean_desc,
                    "short_description": clean_desc,
                    "price": price,
                    "platform": "shopee",
                    "original_url": url
                }

            except Exception as e:
                logger.error(f"❌ Scraper Error: {e}")
                return self._empty_data(url)

    def _get_description_logic(self, page) -> str:
        try:
            # Cuộn đến giữa trang để kích hoạt Lazy Load của phần mô tả
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
            page.wait_for_timeout(2000)

            return page.evaluate("""() => {
                // 1. Tìm chính xác Container chứa chi tiết sản phẩm (Cập nhật 2024-2025)
                // Shopee thường đặt mô tả trong các class có cấu trúc renderer hoặc p_7rWz
                const specificSelectors = [
                    'div.product-detail__renderer', 
                    'div.p_7rWz',
                    '.product-details__section',
                    'div._3yZ_0n'
                ];

                for (let sel of specificSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const txt = el.innerText || '';
                        const up = txt.toUpperCase();
                        // Tìm các biến thể: "MÔ TẢ", "MÔ TẢ SẢN PHẨM" hoặc "PRODUCT DESCRIPTION"
                        if (up.includes("MÔ TẢ") || up.includes("PRODUCT DESCRIPTION")) {
                            // Loại bỏ phần đánh giá nếu có
                            let content = txt.split(/ĐÁNH GIÁ SẢN PHẨM/i)[0];
                            return content.trim();
                        }
                    }
                }

                // 2. Nếu không tìm thấy bằng class, tìm dựa trên tiêu đề văn bản (case-insensitive)
                const allElements = document.querySelectorAll('h2, div, section, span');
                for (let el of allElements) {
                    const txt = (el.innerText || '').trim();
                    const up = txt.toUpperCase();
                    if (up === "MÔ TẢ SẢN PHẨM" || up === "PRODUCT DESCRIPTION" || up.includes('MÔ TẢ')) {
                        const nextEl = el.nextElementSibling || el.parentElement;
                        if (nextEl) {
                            let content = nextEl.innerText || '';
                            content = content.split(/ĐÁNH GIÁ SẢN PHẨM/i)[0].trim();
                            if (content) return content;
                        }
                    }
                }
                return "";
            }""")
        except:
            return ""

    def _get_fallback_description(self, page) -> str:
        """Hàm dự phòng nhưng có giới hạn phạm vi để tránh lấy 6000+ ký tự rác
        Tách phần logic phức tạp để dễ unit-test bằng Python.
        """
        try:
            # Lấy toàn bộ text của body từ trang
            body_text = page.evaluate("() => document.body.innerText") or ""
            desc = self._extract_description_from_body_text(body_text)
            if desc:
                return desc
            # Nếu không có, thử meta description
            meta = page.evaluate("() => document.querySelector('meta[name=\"description\"]')?.content")
            return meta or ""
        except Exception:
            return ""

    def _extract_description_from_body_text(self, body_text: str) -> str:
        """Tách và trả về đoạn mô tả từ body text (case-insensitive)."""
        if not body_text:
            return ""
        body_up = body_text.upper()
        start_idx = body_up.find('MÔ TẢ')
        if start_idx == -1:
            start_idx = body_up.find('PRODUCT DESCRIPTION')
        if start_idx != -1:
            end_idx = body_up.find('ĐÁNH GIÁ SẢN PHẨM', start_idx)
            if end_idx == -1 or (end_idx - start_idx) > 2500:
                end_idx = start_idx + 2000
            result = body_text[start_idx:end_idx]
            # Loại bỏ các tiêu đề như 'MÔ TẢ SẢN PHẨM', 'MÔ TẢ' hoặc 'PRODUCT DESCRIPTION'
            result = re.sub(r"MÔ TẢ SẢN PHẨM", "", result, flags=re.IGNORECASE)
            result = re.sub(r"MÔ TẢ", "", result, flags=re.IGNORECASE)
            result = re.sub(r"PRODUCT DESCRIPTION", "", result, flags=re.IGNORECASE)
            return result.strip()
        return ""

    def _get_title(self, page) -> str:
        try:
            t = page.title().split('|')[0].strip()
            if not t or t == "Shopee" or len(t) < 5:
                t = page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.content") or "Sản phẩm Shopee"
            return t
        except:
            return "Sản phẩm Shopee"

    def _get_images_advanced(self, page) -> List[str]:
        try:
            return page.evaluate("""() => {
                const urls = new Set();
                document.querySelectorAll('img').forEach(img => {
                    let src = img.getAttribute('data-src') || img.src;
                    if (src && (src.includes('usercontent') || src.includes('shopee.com/file/'))) {
                        // Loại bỏ các thumbnail nhỏ để lấy ảnh gốc (@ hoặc _tn)
                        let clean = src.split('@')[0].split('_tn')[0].split('_v')[0];
                        if (!clean.startsWith('http')) clean = 'https:' + clean;
                        // Chỉ lấy các ảnh có vẻ là ảnh sản phẩm (kích thước lớn)
                        urls.add(clean);
                    }
                });
                return Array.from(urls).slice(0, 10);
            }""")
        except:
            return []

    def _empty_data(self, url: str) -> Dict:
        return {
            "title": "Sản phẩm Shopee",
            "image_urls": [],
            "description": "",
            "short_description": "",
            "price": "0",
            "platform": "shopee",
            "original_url": url
        }

    def _get_price(self, page) -> str:
        """Lấy giá sản phẩm từ Shopee"""
        try:
            price = page.evaluate("""() => {
                // Các selector phổ biến cho giá trên Shopee
                const priceSelectors = [
                    '.product-price__current-price',           // Giá hiện tại
                    'span.shopee-price__current',              // Class cũ
                    '[data-testid="product-price"]',           
                    'div._3I7_6e',                             // Class Shopee 2024-2025
                    'div.shopee-product-rating',              
                    '.product-price'
                ];
                
                for (let sel of priceSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        let text = el.innerText?.trim() || '';
                        // Lấy con số từ text (loại bỏ ₫, dấu phẩy, khoảng trắng)
                        const nums = text.match(/\d+[\d.,]*\d*/);
                        if (nums) {
                            return nums[0].replace(/[.,]/g, '');  // '123.456' -> '123456'
                        }
                    }
                }
                
                // Fallback: tìm số lớn nhất trên trang (thường là giá)
                const bodyText = document.body.innerText;
                const pricePattern = /₫\s*[\d.,]+/g;
                const matches = bodyText.match(pricePattern);
                if (matches && matches.length > 0) {
                    let price = matches[0].replace(/[₫\s.,]/g, '');
                    // Lọc để chỉ lấy giá hợp lý (1000-999999999)
                    if (price.length >= 4 && price.length <= 9) {
                        return price;
                    }
                }
                
                return '0';
            }""")
            return price or '0'
        except Exception as e:
            logger.debug(f"⚠️ Failed to get price: {e}")
            return '0'