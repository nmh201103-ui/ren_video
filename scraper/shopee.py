import re
import json
from typing import Dict, List
from playwright.sync_api import sync_playwright
from scraper.base import BaseScraper
from utils.logger import get_logger

logger = get_logger()

class ShopeeScraper(BaseScraper):
    def scrape(self, url: str) -> Dict:
        logger.info(f"🔗 Kết nối tới Chrome (9222)...")
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                page = next((pge for pge in context.pages if "shopee.vn" in pge.url), None)
                if not page:
                    page = context.new_page()

                # Cấu hình Header chống bị chặn
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                page.set_extra_http_headers({"User-Agent": ua})

                if url not in page.url:
                    page.goto(url, wait_until="networkidle", timeout=60000)

                # Chờ cho các thành phần chính hiện ra
                page.wait_for_timeout(2000)
                self._force_load(page)

                # Lấy danh sách ảnh bằng nhiều cách khác nhau
                raw_images = self._get_images(page)
                
                # Nếu vẫn không có ảnh, dùng phương pháp Regex quét toàn bộ Source Code
                if not raw_images:
                    logger.warning("⚠️ Không tìm thấy ảnh bằng DOM, đang thử quét Regex...")
                    raw_images = self._get_images_regex(page)

                description = self._get_description(page)
                title = self._get_title(page)
                price = self._get_price(page)
                
                data = {
                    "title": title,
                    "price": price,
                    "image_urls": raw_images,
                    "description": description,
                    "platform": "shopee",
                    "original_url": url,
                }
                
                logger.info(f"✅ Kết quả: {len(raw_images)} ảnh | Tiêu đề: {title[:30]}...")
                return data
            except Exception as e:
                logger.error(f"❌ Scraper Error: {e}")
                return self._empty(url)

    def _force_load(self, page):
        """Ép trang load ảnh bằng cách cuộn chuột và click xem thêm"""
        try:
            page.evaluate("window.scrollTo(0, 800)")
            page.wait_for_timeout(1000)
            # Tìm và bấm nút 'Xem thêm' mô tả nếu có
            btn = page.locator('text="Xem thêm"').first
            if btn.is_visible():
                btn.click()
        except:
            pass

    def _get_title(self, page) -> str:
        try:
            # Ưu tiên lấy từ Meta tag vì nó luôn có và chuẩn
            title = page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.content")
            if title: return title.strip()
            
            selectors = ["h1", "._44qnta", "div.hpX4qW span", ".VpY09Z"]
            for s in selectors:
                el = page.locator(s).first
                if el.is_visible(): return el.inner_text().strip()
            return "Sản phẩm Shopee"
        except: return "Sản phẩm Shopee"

    def _get_price(self, page) -> str:
        try:
            # Lấy giá từ meta tag để tránh sai sót giao diện
            price = page.evaluate("document.querySelector('meta[property=\"product:price:amount\"]')?.content")
            if price: return price
            
            price_el = page.locator(".pq6u9U, .G-uSTW, .p86s3C, ._2Sh_1t").first
            return re.sub(r"\D", "", price_el.inner_text())
        except:
            return "0"

    def _get_images(self, page) -> List[str]:
        """Phương pháp 1: Quét DOM tìm thẻ img và picture"""
        return page.evaluate("""() => {
            const urls = new Set();
            
            // Lấy ảnh từ các thẻ meta (thường là ảnh đại diện đẹp nhất)
            const ogImg = document.querySelector('meta[property="og:image"]')?.content;
            if (ogImg) urls.add(ogImg.split('@')[0].split('_tn')[0]);

            // Quét tất cả thẻ img có liên quan đến sản phẩm
            document.querySelectorAll('img').forEach(img => {
                const src = img.getAttribute('srcset')?.split(' ')[0] || img.getAttribute('data-src') || img.src;
                if (src && (src.includes('susercontent.com') || src.includes('shopee.vn/file'))) {
                    if (!src.includes('.svg') && !src.includes('icon')) {
                        urls.add(src.split('@')[0].split('_tn')[0].split('_cover')[0]);
                    }
                }
            });
            return Array.from(urls).slice(0, 10);
        }""")

    def _get_images_regex(self, page) -> List[str]:
        """Phương pháp 2: Quét trực tiếp trong Source Code (Dùng khi DOM bị ảo)"""
        try:
            content = page.content()
            # Tìm tất cả các mã ID ảnh Shopee (thường là chuỗi hex 32 ký tự)
            img_ids = re.findall(r'vn-11134207-[a-z0-9-]+', content)
            if not img_ids:
                img_ids = re.findall(r'[a-f0-9]{32}', content)
            
            urls = []
            for img_id in set(img_ids):
                if len(img_id) >= 32: # ID ảnh Shopee chuẩn dài 32 ký tự
                    urls.append(f"https://down-vn.img.susercontent.com/file/{img_id}")
            
            return urls[:10]
        except:
            return []

    def _get_description(self, page) -> str:
        try:
            # Thử lấy từ Meta tag description
            meta_desc = page.evaluate("document.querySelector('meta[property=\"og:description\"]')?.content")
            if meta_desc and len(meta_desc) > 50: return meta_desc

            return page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('div, span, p'))
                    .filter(el => window.getComputedStyle(el).whiteSpace === 'pre-wrap' && el.innerText.length > 50);
                return els.length > 0 ? els[0].innerText : "";
            }""")
        except:
            return ""

    def _empty(self, url: str) -> Dict:
        return {"title": "Không lấy được dữ liệu", "price": "0", "image_urls": [], "description": "", "platform": "shopee", "original_url": url}