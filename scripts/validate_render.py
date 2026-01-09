"""Quick validation script to run SmartVideoRenderer locally (dry run).
Requires at least one image in assets/images or internet access.
"""
import os
from video.render import SmartVideoRenderer

sample = {
    "title": "Test Product",
    "description": "Sản phẩm thử nghiệm, rất đẹp, phù hợp mặc hàng ngày.",
    "price": "199000",
    "image_urls": ["https://via.placeholder.com/720x1280.png?text=Test1"]
}

if __name__ == "__main__":
    out = "output/test_render.mp4"
    r = SmartVideoRenderer()
    success = r.render(sample, out, max_images=1)
    print("Success:", success)
