import os
from scraper.shopee import ShopeeScraper
from scraper.tiktok import TikTokScraper
from scraper.base import BaseScraper
from typing import Optional


def get_scraper(url: str) -> Optional[BaseScraper]:
    url = url.lower()

    if "shopee.vn" in url:
        return ShopeeScraper()

    if "tiktok.com" in url:
        return TikTokScraper()

    return None


def ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)



