"""
Scraper module để lấy thông tin sản phẩm từ các platform
"""
from .base import BaseScraper
from .shopee import ShopeeScraper
from .tiktok import TikTokScraper

__all__ = ['BaseScraper', 'ShopeeScraper', 'TikTokScraper']




