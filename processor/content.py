import re
from typing import Dict, List

class ContentProcessor:
    """Xử lý content cho video"""
    
    def __init__(self, max_title_length: int = 50, max_description_length: int = 100):
        self.max_title_length = max_title_length
        self.max_description_length = max_description_length
    
    def process(self, product_data: Dict) -> Dict:
        # Tự động nhận diện danh sách ảnh dù key là images hay image_urls
        image_urls = product_data.get('image_urls') or product_data.get('images') or []
        
        # Xử lý title
        title = self._clean_title(product_data.get('title', ''))
        title = self._truncate_text(title, self.max_title_length)
        
        # Xử lý price
        price = self._format_price(product_data.get('price', '0'))
        
        # Xử lý description
        description = product_data.get('description', '')
        cleaned_desc = self._sanitize_description(description)

        # Chia description thành các đoạn nhỏ để gắn vào từng ảnh
        image_descriptions = self._split_description_for_images(cleaned_desc, len(image_urls))

        # Tạo danh sách image_data chuẩn cho Renderer
        image_data = []
        for i, img_url in enumerate(image_urls):
            img_desc = image_descriptions[i] if i < len(image_descriptions) else ""
            image_data.append({
                'url': img_url,
                'description': img_desc
            })
        
        short_description = self._truncate_text(cleaned_desc, self.max_description_length)
        cta_text = self._generate_cta(product_data.get('platform', 'shopee'))
        
        return {
            'title': title,
            'price': price,
            'image_urls': image_urls,
            'image_data': image_data,
            'description': cleaned_desc,
            'short_description': short_description,
            'cta_text': cta_text,
            'original_url': product_data.get('original_url', ''),
            'platform': product_data.get('platform', 'shopee')
        }

    def _sanitize_description(self, text: str) -> str:
        """Loại bỏ các block kỹ thuật, hướng dẫn, hashtags và các phần không phù hợp cho script marketing."""
        if not text:
            return ''
        # Normalize whitespace
        text = text.replace('\r', '\n')
        # Split into paragraphs by double newlines or single newlines
        paras = [p.strip() for p in text.split('\n\n') if p.strip()]
        keep = []
        for p in paras:
            up = p.upper()
            # Drop paragraphs that look like specs, headings, guides, policies or hashtags
            if any(k in up for k in ("THÔNG TIN SẢN PHẨM", "HƯỚNG DẪN", "CAM KẾT", "QUY ĐỊNH", "TRƯỜNG HỢP", "LƯU Ý")):
                continue
            if p.strip().startswith('*'):
                continue
            if '#' in p and len(p) < 120:
                # likely a set of hashtags
                continue
            # drop very long spec-like paragraphs containing many colons or 'Tên sản phẩm'
            if ('TÊN SẢN PHẨM' in up or 'KÍCH THƯỚC' in up or 'MÀU SẮC' in up) and len(p) > 60:
                continue
            # keep marketing-like short paragraphs
            keep.append(' '.join(p.split()))
        return '\n'.join(keep)  # No length limit - let full content flow for scene generation
    
    def _clean_title(self, title: str) -> str:
        title = re.sub(r'<[^>]+>', '', title)
        title = re.sub(r'[^\w\s\-.,!?()]', '', title)
        return ' '.join(title.split()).strip()
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        return ' '.join(text.split()).strip()
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        if len(text) <= max_length: return text
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:
            truncated = truncated[:last_space]
        return truncated + '...'
    
    def _format_price(self, price: str) -> str:
        try:
            price_num = re.sub(r'[^\d]', '', str(price))
            if price_num:
                return f"{int(price_num):,}".replace(',', '.')
            return '0'
        except:
            return str(price)
    
    def _split_description_for_images(self, description: str, num_images: int) -> List[str]:
        if not description or num_images == 0: return []
        sentences = re.split(r'[.!?]\s+', description)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if len(sentences) <= num_images:
            res = sentences + [''] * (num_images - len(sentences))
            return res[:num_images]
        
        # Chia đều câu cho ảnh
        result = []
        avg = len(sentences) // num_images
        for i in range(num_images):
            chunk = ' '.join(sentences[i*avg : (i+1)*avg])
            result.append(self._truncate_text(chunk, 100))
        return result

    def _generate_cta(self, platform: str) -> str:
        return f"Mua ngay trên {platform.capitalize()}!"