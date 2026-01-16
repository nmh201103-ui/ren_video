#!/usr/bin/env python
"""Quick test of image searcher"""
from video.image_searcher import ImageSearcher
import os

s = ImageSearcher()
output_dir = "assets/temp/web_story_images_test"
os.makedirs(output_dir, exist_ok=True)

# Test generating URLs
print("Testing URL generation...")
urls = s._search_duckduckgo("business", 2)
print(f"✅ Generated {len(urls)} URLs")
for url in urls:
    print(f"  - {url}")

# Test downloading
print("\nTesting downloads...")
paths = s.search_and_download("learning", 2, output_dir)
print(f"✅ Downloaded {len(paths)} images")
for p in paths:
    size = os.path.getsize(p) if os.path.exists(p) else 0
    print(f"  - {p} ({size} bytes)")

print("\nTest complete!")
