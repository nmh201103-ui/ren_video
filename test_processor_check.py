"""Test if scraper returns images - direct check"""
import sys
sys.path.insert(0, '.')

# Direct test without full imports
print("Testing product data flow...")

# Simulate what processor does
product_data = {
    'title': 'Test Product',
    'description': 'A nice product',
    'price': '100000',
    'image_urls': ['img1.jpg', 'img2.jpg', 'img3.jpg'],
    'platform': 'shopee'
}

# Test processor
from processor.content import ContentProcessor

processor = ContentProcessor()
result = processor.process(product_data)

print(f"✅ Original images: {len(product_data.get('image_urls', []))}")
print(f"✅ Processed images: {len(result.get('image_urls', []))}")
print(f"✅ Result keys: {list(result.keys())}")

if result.get('image_urls'):
    print(f"\n📸 Images in result:")
    for img in result['image_urls'][:3]:
        print(f"   - {img}")
else:
    print("❌ NO IMAGES in processed result!")
