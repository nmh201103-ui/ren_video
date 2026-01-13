"""
Video templates
"""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class VideoTemplate:
    """Template cho video - HIGH QUALITY SETTINGS"""
    name: str
    width: int = 1080  # Full HD 1080p
    height: int = 1920  # Vertical format cho TikTok/Shorts
    duration: float = 15.0  # Giây
    fps: int = 30  # 30fps cho smooth playback (chuẩn TikTok/YouTube)
    
    # Timing cho các elements
    title_duration: float = 3.0
    image_duration: float = 2.0
    price_duration: float = 2.0
    cta_duration: float = 3.0
    
    # Colors
    bg_color: str = '#000000'
    title_color: str = '#FFFFFF'
    price_color: str = '#FF6B6B'
    cta_color: str = '#4ECDC4'
    
    # Font sizes
    title_font_size: int = 60
    price_font_size: int = 80
    cta_font_size: int = 50


# Predefined templates
TEMPLATE_TIKTOK = VideoTemplate(
    name='tiktok',
    width=1080,
    height=1920,
    duration=15.0
)

TEMPLATE_SHOPEE = VideoTemplate(
    name='shopee',
    width=1080,
    height=1920,
    duration=15.0
)

TEMPLATE_DEFAULT = VideoTemplate(
    name='default',
    width=1080,
    height=1920,
    duration=15.0
)





