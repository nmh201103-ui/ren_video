from scraper.shopee import ShopeeScraper

s = ShopeeScraper()
body_vn = "Header\nMô tả sản phẩm\nĐây là mô tả sản phẩm rất hay. Chi tiết...\nĐÁNH GIÁ SẢN PHẨM\nFooter"
body_en = "Header\nProduct Description\nThis is a great product description. Details here.\nREVIEWS\nFooter"
body_none = "No description at all here."

print('VN ->', s._extract_description_from_body_text(body_vn)[:120])
print('EN ->', s._extract_description_from_body_text(body_en)[:120])
print('NONE ->', repr(s._extract_description_from_body_text(body_none)))

assert 'Đây là mô tả sản phẩm' in s._extract_description_from_body_text(body_vn)
assert 'This is a great product description' in s._extract_description_from_body_text(body_en)
assert s._extract_description_from_body_text(body_none) == ''
print('All checks passed')
