import re
from typing import Dict, List
from playwright.sync_api import sync_playwright
from scraper.base import BaseScraper
from utils.logger import get_logger
import time

logger = get_logger()


class ShopeeScraper(BaseScraper):
    MAX_DESC_RETRIES = 5  # số lần scroll thử lấy mô tả
    SCROLL_STEP = 500     # px mỗi lần scroll
    SCROLL_WAIT = 1.0     # giây chờ sau mỗi lần scroll

    def scrape(self, url: str) -> Dict:
        """
        Lấy dữ liệu Shopee theo thứ tự:
        1. Lấy title, price, images trước.
        2. Scroll xuống lấy description.
        3. Trả data đầy đủ cho renderer.
        """
        logger.info(f"🔗 Kết nối tới Chrome (9222)...")
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                page = next((pg for pg in context.pages if "shopee.vn" in pg.url), None)
                if not page:
                    page = context.new_page()

                ua = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
                page.set_extra_http_headers({"User-Agent": ua})

                if url not in page.url:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(2000)

                # -------------------------
                # BƯỚC 1: Lấy title, price, images ở đầu trang
                title = self._get_title(page) or "Sản phẩm Shopee"
                price = self._get_price(page) or "0"

                images = self._get_images(page)
                if not images:
                    images = self._get_images_regex(page)

                logger.info(f"✅ Lấy xong ảnh/title/price: {len(images)} ảnh, {title}, {price}")

                # -------------------------
                # BƯỚC 2: Scroll xuống lấy mô tả
                description = ""
                for attempt in range(self.MAX_DESC_RETRIES):
                    description = self._get_description(page)
                    if description.strip():
                        logger.info(f"✅ Lấy được mô tả sản phẩm sau {attempt+1} lần scroll, {len(description)} ký tự")
                        break
                    logger.info(f"⚠️ Mô tả chưa có, scroll lần {attempt + 1}/{self.MAX_DESC_RETRIES}")
                    page.evaluate(f"window.scrollBy(0, {self.SCROLL_STEP})")
                    page.wait_for_timeout(int(self.SCROLL_WAIT * 1000))

                if not description.strip():
                    logger.warning("⚠️ Không lấy được mô tả sản phẩm, dùng fallback text")

                # -------------------------
                # Trả dữ liệu đầy đủ cho renderer
                data = {
                    "title": title,
                    "price": price,
                    "image_urls": images or [],
                    "description": description or "",
                    "platform": "shopee",
                    "original_url": url,
                }

                logger.info(
                    f"✅ DONE | {len(data['image_urls'])} ảnh | "
                    f"Mô tả: {len(data['description'])} ký tự"
                )
                return data

            except Exception as e:
                logger.error(f"❌ Scraper Error: {e}")
                return self._empty(url)

    # -------------------------
    def _get_title(self, page) -> str:
        try:
            title = page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.content")
            if title:
                return title.strip()
            el = page.locator("h1").first
            if el.is_visible():
                return el.inner_text().strip()
            return ""
        except:
            return ""

    # -------------------------
    def _get_price(self, page) -> str:
        try:
            price = page.evaluate("document.querySelector('meta[property=\"product:price:amount\"]')?.content")
            if price:
                return price.strip()
            el = page.locator(".ZA5sW5").first
            if el.is_visible():
                return el.inner_text().strip()
            el = page.locator(".IZPeQz").first
            if el.is_visible():
                return el.inner_text().split(" - ")[0].strip()
            return "0"
        except:
            return "0"

    # -------------------------
    def _get_images(self, page) -> List[str]:
        try:
            return page.evaluate("""() => {
                const urls = new Set();
                const og = document.querySelector('meta[property="og:image"]')?.content;
                if (og) urls.add(og.split('@')[0]);
                document.querySelectorAll('img').forEach(img => {
                    const src = img.getAttribute('data-src') || img.src || '';
                    if (!src) return;
                    if (!src.includes('susercontent.com')) return;
                    if (src.includes('.svg') || src.includes('icon')) return;
                    urls.add(src.split('@')[0].split('_tn')[0]);
                });
                return Array.from(urls).slice(0, 10);
            }""")
        except:
            return []

    def _get_images_regex(self, page) -> List[str]:
        try:
            content = page.content()
            ids = set(re.findall(r'vn-\d{8}-[a-z0-9-]+', content))
            return [f"https://down-vn.img.susercontent.com/file/{i}" for i in list(ids)[:10]]
        except:
            return []

    # -------------------------
    def _get_description(self, page) -> str:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            desc_section = page.locator('section.I_DV_3:has(h2:has-text("MÔ TẢ SẢN PHẨM"))').first
            desc_section.wait_for(state="attached", timeout=10000)

            ps = desc_section.locator('div.e8lZp3 > div > p.QN2lPu')
            count = ps.count()
            texts = []
            for i in range(count):
                txt = ps.nth(i).inner_text().strip()
                if txt and len(txt) > 5:
                    texts.append(txt)
            texts = list(dict.fromkeys(texts))
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"❌ Lỗi lấy mô tả sản phẩm: {e}")
            return ""

    # -------------------------
    def _empty(self, url: str) -> Dict:
        return {
            "title": "Không lấy được dữ liệu",
            "price": "0",
            "image_urls": [],
            "description": "",
            "platform": "shopee",
            "original_url": url,
        }
