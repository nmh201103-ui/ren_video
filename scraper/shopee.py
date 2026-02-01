import re
import time
from typing import Dict, List
from io import BytesIO
import requests
from PIL import Image
import numpy as np
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

                # Kiểm tra Shopee redirect sang captcha/xác minh — không scrape được
                current_url = page.url or ""
                if "/verify/captcha" in current_url or "/verify" in current_url:
                    logger.error("❌ Shopee đang hiển thị trang captcha/xác minh. Hoàn thành captcha trong Chrome rồi thử lại.")
                    out = self._empty_data(url)
                    out["_scrape_failed"] = True
                    out["_scrape_error"] = (
                        "Shopee chuyển sang trang captcha/xác minh. "
                        "Bạn cần: 1) Mở link sản phẩm trong Chrome, 2) Bấm 'Thử Lại' / hoàn thành captcha (nếu có), "
                        "3) Đợi trang sản phẩm load xong, 4) Bấm Generate lại."
                    )
                    return out

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

                # Fallback giá từ mô tả nếu DOM không lấy được
                if (not price or price == "0") and clean_desc:
                    price_match = re.search(r"(?:giá|Giá|GIÁ|₫|VNĐ|vnd)\s*[:\s]*([\d.,]+)\s*(?:₫|VNĐ|k)?", clean_desc, re.IGNORECASE)
                    if not price_match:
                        price_match = re.search(r"\b(\d{2,3}(?:\.\d{3})+(?:\.\d{3})?)\s*₫", clean_desc)
                    if price_match:
                        pstr = re.sub(r"[^\d]", "", price_match.group(1))
                        if len(pstr) >= 4:
                            price = pstr
                            logger.info("📌 Lấy giá từ mô tả (fallback): %s", price)

                # Nếu 0 ảnh + title generic → có thể đang trang captcha/lỗi tải
                generic_titles = ("Sản phẩm Shopee", "Shopee", "Shopee Việt Nam")
                if len(images) == 0 and (not title or title.strip() in generic_titles):
                    logger.warning("⚠️ Không lấy được ảnh và title — có thể trang captcha hoặc 'Lỗi tải'. Hoàn thành xác minh trong Chrome rồi thử lại.")
                    out = self._empty_data(url)
                    out["_scrape_failed"] = True
                    out["_scrape_error"] = (
                        "Không lấy được ảnh sản phẩm (trang có thể đang captcha hoặc 'Lỗi tải'). "
                        "Trong Chrome: bấm 'Thử Lại' / hoàn thành captcha, đợi trang sản phẩm load xong rồi Generate lại."
                    )
                    return out

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
                out = self._empty_data(url)
                out["_scrape_failed"] = True
                out["_scrape_error"] = str(e)
                return out

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
            # Ưu tiên og:title (trang sản phẩm luôn có), tránh title tab generic "Shopee Việt Nam"
            og = page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.content") or ""
            if og and len(og.strip()) > 10 and "shopee" not in og.strip().lower()[:20]:
                return og.strip().split("|")[0].strip()
            t = page.title().split("|")[0].strip()
            if not t or t == "Shopee" or "Shopee Việt Nam" in t or len(t) < 8:
                return og.strip().split("|")[0].strip() if og else "Sản phẩm Shopee"
            return t
        except Exception:
            return "Sản phẩm Shopee"

    def _get_images_advanced(self, page) -> List[str]:
        try:
            # Cuộn tới vùng gallery để kích lazy-load ảnh sản phẩm
            try:
                page.evaluate("window.scrollTo(0, 400)")
                page.wait_for_timeout(1500)
            except Exception:
                pass
            raw_urls = page.evaluate("""() => {
                const urls = new Set();
                const add = (src) => {
                    if (!src || typeof src !== 'string') return;
                    const s = src.trim();
                    // Shopee CDN: usercontent, shopee.com/file, cdn.shopee, down-*.img
                    if (s.includes('usercontent') || s.includes('shopee.com/file') || s.includes('cdn.shopee') || /down-[a-z0-9-]+\\.img\\./.test(s) || (s.includes('shopee') && s.includes('img'))) {
                        let clean = s.split('@')[0].split('_tn')[0].split('_v')[0];
                        if (!clean.startsWith('http')) clean = 'https:' + clean;
                        urls.add(clean);
                    }
                };
                document.querySelectorAll('img').forEach(img => {
                    add(img.getAttribute('data-src') || img.getAttribute('src'));
                });
                document.querySelectorAll('picture source').forEach(el => { add(el.getAttribute('srcset')?.split(' ')[0]); add(el.getAttribute('src')); });
                return Array.from(urls).slice(0, 15);
            }""")
            # Fallback: ảnh chính từ og:image
            if not raw_urls or len(raw_urls) == 0:
                try:
                    og_img = page.evaluate("document.querySelector('meta[property=\"og:image\"]')?.content") or ""
                    if og_img and "shopee" in og_img.lower():
                        raw_urls = [og_img]
                        logger.info("📷 Dùng og:image làm ảnh sản phẩm (fallback)")
                except Exception:
                    pass
            
            # Lọc ảnh sản phẩm thực (loại bỏ banner, voucher, model)
            filtered = self._filter_product_images(raw_urls)
            logger.info(f"📸 Lọc ảnh: {len(raw_urls)} -> {len(filtered)} ảnh sản phẩm")
            # Bỏ ảnh thứ 3 (index 2): trong DOM thường là video/banner "GIẢM" → render ra trắng khi làm video
            if len(filtered) > 2:
                filtered = filtered[:2] + filtered[3:]
                logger.info("📷 Đã bỏ ảnh thứ 3 (video/banner) để tránh render trắng")
            return filtered[:10]  # Trả về max 10 ảnh
        except Exception as e:
            logger.error(f"❌ Failed to get images: {e}")
            return []
    
    def _filter_product_images(self, image_urls: List[str]) -> List[str]:
        """Filter to keep only real product images, remove banners/vouchers/models"""
        filtered = []
        
        for url in image_urls:
            try:
                if self._is_product_image(url):
                    filtered.append(url)
            except Exception as e:
                logger.debug(f"⚠️ Failed to check image {url}: {e}")
                # If check fails, keep it (safe default)
                filtered.append(url)
        
        return filtered
    
    def _is_product_image(self, url: str) -> bool:
        """
        Detect if image is real product photo (not banner/voucher/model).
        Returns True if likely a product image.
        """
        try:
            # CRITICAL: Only accept Shopee CDN URLs (block local files)
            if not url.startswith('http'):
                logger.debug(f"❌ Rejected: Not HTTP URL")
                return False
            
            # Block local file paths that might leak into scraper
            if 'file:///' in url or 'C:/' in url or 'C:' in url or 'Users/' in url:
                logger.debug(f"❌ Rejected: Local file path")
                return False
            
            # Must be from Shopee CDN (bao gồm og:image, cdn, down-*.img)
            if not ('usercontent' in url or 'shopee.com/file/' in url or 'shopee' in url.lower() or 'cdn.shopee' in url or re.search(r'down-[a-z0-9-]+\.img\.', url)):
                logger.debug(f"❌ Rejected: Not Shopee CDN")
                return False
            
            # Download image
            response = requests.get(url, timeout=5, stream=True)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert('RGB')
            
            # 1. Check aspect ratio (banners usually wide, products square-ish)
            width, height = img.size
            aspect_ratio = width / height
            
            # CHỈ loại bỏ banner CỰC KỲ rõ ràng (quá ngang)
            if aspect_ratio > 8.0 or aspect_ratio < 0.12:
                logger.debug(f"❌ Rejected: Extreme aspect ratio {aspect_ratio:.2f}")
                return False
            
            # 2. Check size - chỉ loại ảnh icon cực nhỏ
            if width < 100 or height < 100:
                logger.debug(f"❌ Rejected: Too small {width}x{height}")
                return False
            
            # TẮT text overlay check - quá nhiều false positive
            # TẮT color distribution check - quá nhiều false positive
            
            return True  # Pass most images
            
        except Exception as e:
            logger.debug(f"⚠️ Image check failed: {e}, keeping image")
            return True  # Safe default: keep if unable to check
    
    def _has_heavy_text_overlay(self, img: Image.Image) -> bool:
        """Detect if image has heavy text overlay (banner characteristic)"""
        try:
            # Convert to grayscale
            gray = img.convert('L')
            arr = np.array(gray)
            
            # Detect edges (text has many edges)
            from scipy import ndimage
            edges = ndimage.sobel(arr)
            edge_ratio = np.sum(edges > 40) / arr.size
            
            # If more than 30% of pixels are edges, likely has text
            return edge_ratio > 0.30
            
        except:
            return False  # If detection fails, assume no text
    
    def _is_single_color_dominant(self, img: Image.Image) -> bool:
        """Detect if single color dominates (voucher/icon characteristic)"""
        try:
            # Resize to speed up
            img_small = img.resize((100, 100))
            arr = np.array(img_small)
            
            # Check if one color channel dominates
            r_mean, g_mean, b_mean = arr[:,:,0].mean(), arr[:,:,1].mean(), arr[:,:,2].mean()
            total = r_mean + g_mean + b_mean
            
            # If one channel is > 70% of total, single color dominates
            if max(r_mean, g_mean, b_mean) / total > 0.7:
                return True
            
            # Check color variance
            variance = np.var(arr)
            if variance < 300:  # Low variance = single color
                return True
            
            return False
            
        except:
            return False

    def _empty_data(self, url: str) -> Dict:
        return {
            "title": "Sản phẩm Shopee",
            "image_urls": [],
            "description": "",
            "short_description": "",
            "price": "0",
            "platform": "shopee",
            "original_url": url,
            "_scrape_failed": False,
        }

    def _get_price(self, page) -> str:
        """Lấy giá sản phẩm từ Shopee (nhiều selector + JSON fallback)"""
        try:
            price = page.evaluate("""() => {
                function parsePriceNum(text) {
                    if (!text) return null;
                    const m = text.replace(/[.,\\s₫]/g, '').match(/\\d+/);
                    return m ? m[0] : null;
                }
                // 1. Selector giá hiện tại (Shopee 2024-2025)
                const priceSelectors = [
                    '.product-price__current-price',
                    'span.shopee-price__current',
                    '[data-testid="product-price"]',
                    'div._3I7_6e',
                    '.pqTWkA', '.ZEgDHl', '.GcqTgR',
                    '[class*="price"] span',
                    '.shopee-product-info__main-price',
                    '.product-price'
                ];
                for (const sel of priceSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const text = (el.innerText || el.textContent || '').trim();
                        const num = parsePriceNum(text);
                        if (num && num.length >= 4 && num.length <= 9) return num;
                    }
                }
                // 2. Tất cả node chứa ₫
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                let node;
                while (node = walker.nextNode()) {
                    const t = node.textContent || '';
                    if (t.includes('₫')) {
                        const num = parsePriceNum(t);
                        if (num && num.length >= 4 && num.length <= 9) return num;
                    }
                }
                // 3. Regex toàn trang (giá VND: 4-9 chữ số)
                const bodyText = document.body.innerText || '';
                const matches = bodyText.match(/[\\d.,]{4,}/g);
                if (matches) {
                    for (const m of matches) {
                        const num = m.replace(/[.,]/g, '');
                        if (num.length >= 4 && num.length <= 9 && parseInt(num, 10) >= 1000)
                            return num;
                    }
                }
                return '0';
            }""")
            return str(price).strip() if price else '0'
        except Exception as e:
            logger.debug(f"⚠️ Failed to get price: {e}")
            return '0'