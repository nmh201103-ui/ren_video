from scraper.shopee import ShopeeScraper


def test_extract_description_from_body_text_vietnamese():
    s = ShopeeScraper()
    body = (
        "Trang header\n"
        "Mô tả sản phẩm\n"
        "Đây là mô tả sản phẩm rất hay. Chi tiết sản phẩm gồm nhiều phần.\n"
        "ĐÁNH GIÁ SẢN PHẨM\n"
        "Phần khác..."
    )
    res = s._extract_description_from_body_text(body)
    assert "Đây là mô tả sản phẩm rất hay" in res


def test_extract_description_from_body_text_english():
    s = ShopeeScraper()
    body = (
        "Header\n"
        "Product Description\n"
        "This is a great product description. It has details.\n"
        "REVIEWS\n"
    )
    res = s._extract_description_from_body_text(body)
    assert "This is a great product description" in res


def test_extract_description_from_body_text_none():
    s = ShopeeScraper()
    body = "No description here, just random text."
    res = s._extract_description_from_body_text(body)
    assert res == ""