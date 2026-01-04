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

                # 1. Lấy Title và Ảnh
                title = self._get_title(page)
                images = self._get_images_advanced(page)

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
                print("\n" + "🚀" * 15)
                print(f"[SCRAPER COMPLETED]")
                print(f"Title: {title[:60]}...")
                print(f"Ảnh: {len(images)} tấm")
                print(f"Mô tả thu được: {len(clean_desc)} ký tự")
                print("🚀" * 15 + "\n")

                return {
                    "title": title,
                    "image_urls": images,
                    "description": clean_desc,
                    "short_description": clean_desc,
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
                    // Nếu tìm thấy và nó chứa tiêu đề "Mô tả sản phẩm"
                    if (el && el.innerText.includes("MÔ TẢ SẢN PHẨM")) {
                        // Loại bỏ các phần thừa nếu lỡ quét dính (như Đánh giá) bằng cách cắt chuỗi
                        let content = el.innerText.split("ĐÁNH GIÁ SẢN PHẨM")[0];
                        return content.trim();
                    }
                }

                // 2. Nếu không tìm thấy bằng class, tìm dựa trên tiêu đề văn bản "MÔ TẢ SẢN PHẨM"
                const allElements = document.querySelectorAll('h2, div, section');
                for (let el of allElements) {
                    if (el.innerText === "MÔ TẢ SẢN PHẨM" || el.innerText === "Product Description") {
                        // Lấy phần tử tiếp theo ngay sau tiêu đề này (thường là nội dung mô tả)
                        const nextEl = el.nextElementSibling || el.parentElement;
                        if (nextEl) return nextEl.innerText.split("ĐÁNH GIÁ SẢN PHẨM")[0].trim();
                    }
                }
                return "";
            }""")
        except:
            return ""

    def _get_fallback_description(self, page) -> str:
        """Hàm dự phòng nhưng có giới hạn phạm vi để tránh lấy 6000+ ký tự rác"""
        try:
            return page.evaluate("""() => {
                const bodyText = document.body.innerText;
                const startKeyword = "MÔ TẢ SẢN PHẨM";
                const endKeyword = "ĐÁNH GIÁ SẢN PHẨM";
                
                const startIndex = bodyText.indexOf(startKeyword);
                if (startIndex !== -1) {
                    let endIndex = bodyText.indexOf(endKeyword, startIndex);
                    
                    // Nếu không tìm thấy từ khóa kết thúc, chỉ lấy tối đa 1500 ký tự từ điểm bắt đầu
                    if (endIndex === -1 || (endIndex - startIndex) > 2500) {
                        endIndex = startIndex + 2000;
                    }
                    
                    let result = bodyText.substring(startIndex, endIndex);
                    // Loại bỏ dòng tiêu đề "MÔ TẢ SẢN PHẨM" ở đầu
                    return result.replace(startKeyword, "").trim();
                }
                
                // Cuối cùng mới dùng Meta Description (thường chỉ ~150-200 ký tự sạch)
                return document.querySelector('meta[name="description"]')?.content || "";
            }""")
        except:
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
            "platform": "shopee",
            "original_url": url
        }