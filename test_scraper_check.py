"""Test scraper to check if images are being captured"""
from scraper.shopee import ShopeeScraper

# Test with a simple Shopee URL
url = "https://shopee.vn/Áo-Thun-Nam-Nữ-Form-Rộng-Tay-Lỡ-Unisex-i.26132906.23693709863"

scraper = ShopeeScraper()
print(f"🔍 Scraping: {url}")

data = scraper.scrape(url)

if data:
    print(f"✅ Title: {data.get('title', 'N/A')[:60]}")
    print(f"✅ Description: {data.get('description', 'N/A')[:100]}")
    print(f"✅ Price: {data.get('price', 'N/A')}")
    print(f"✅ Platform: {data.get('platform', 'N/A')}")
    
    images = data.get('image_urls') or data.get('images') or []
    print(f"\n📸 Images found: {len(images)}")
    for i, img in enumerate(images[:3]):
        print(f"   {i+1}. {img[:80]}...")
else:
    print("❌ Scraper returned None or empty data")
