from processor.content import ContentProcessor


def test_sanitize_removes_specs_and_hashtags():
    proc = ContentProcessor()
    raw = """
Áo Thun Cổ Tròn Clean Fit - B Brand Form Gọn, Tôn Dáng.

*THÔNG TIN SẢN PHẨM

Tên sản phẩm: Áo Thun Cổ tròn Clean Fit B Brand

Màu sắc: Trắng / Đen / Be

#AoThunCleanFit #AoThun

Đặc điểm nổi bật: mềm, co giãn.
"""
    cleaned = proc._sanitize_description(raw)
    assert 'THÔNG TIN SẢN PHẨM' not in cleaned.upper()
    assert '#' not in cleaned
    assert 'Đặc điểm nổi bật' in cleaned


def test_sanitize_keeps_marketing_lines():
    proc = ContentProcessor()
    raw = """Siêu mềm, mặc mát. Thiết kế ôm nhẹ, tôn dáng."""
    cleaned = proc._sanitize_description(raw)
    assert 'Siêu mềm' in cleaned
