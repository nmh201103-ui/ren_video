"""
Downloader utilities để download images
"""
import requests
import os
from typing import Optional
from pathlib import Path


def download_image(url: str, save_path: str, timeout: int = 10) -> bool:
    """
    Download image từ URL
    
    Args:
        url: URL của image
        save_path: Đường dẫn lưu file
        timeout: Timeout cho request
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Lưu file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return False


def get_image_extension(url: str) -> str:
    """Lấy extension từ URL"""
    # Loại bỏ query parameters
    url = url.split('?')[0]
    # Lấy extension
    ext = os.path.splitext(url)[1]
    if ext:
        return ext
    return '.jpg'  # Default




