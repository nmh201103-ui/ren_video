import os
from scraper.shopee import ShopeeScraper
from scraper.tiktok import TikTokScraper
from scraper.movie import MovieScraper
from scraper.base import BaseScraper
from typing import Optional


def get_scraper(url: str) -> Optional[BaseScraper]:
    url = url.lower()

    if "shopee.vn" in url:
        return ShopeeScraper()

    if "tiktok.com" in url:
        return TikTokScraper()
    
    # Movie scrapers (IMDb, Wikipedia, movie names)
    if "imdb.com" in url or "wikipedia.org" in url or len(url) < 100:
        # If short string or IMDb/Wiki URL, treat as movie
        return MovieScraper()

    return None


def ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)





