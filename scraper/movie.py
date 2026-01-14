import re
import requests
from typing import Dict, Optional
from scraper.base import BaseScraper
from utils.logger import get_logger

logger = get_logger()


class MovieScraper(BaseScraper):
    """Scrape movie data từ IMDb/OMDb hoặc Wikipedia"""
    
    def __init__(self):
        self.omdb_api_key = None  # TODO: Set from env variable OMDB_API_KEY
        self.omdb_endpoint = "https://www.omdbapi.com/"
    
    def scrape(self, url: str) -> Dict:
        """
        Scrape movie data từ:
        - IMDb URL (imdb.com/title/tt...)
        - Wikipedia (wikipedia.org/wiki/...)
        - OMDb (nếu không có url, lấy từ query parameter "?q=movie_name")
        - Hoặc nhập trực tiếp tên phim
        """
        logger.info(f"🎬 Scraping movie data from: {url}")
        
        # Case 1: IMDb URL
        if "imdb.com" in url:
            return self._scrape_imdb(url)
        
        # Case 2: Wikipedia URL
        if "wikipedia.org" in url:
            return self._scrape_wikipedia(url)
        
        # Case 3: Direct movie name (search via OMDb)
        return self._search_omdb(url)
    
    def _scrape_imdb(self, url: str) -> Dict:
        """Extract IMDb ID từ URL và lấy data via OMDb API"""
        try:
            # Extract IMDb ID (tt123456)
            match = re.search(r'(tt\d+)', url)
            if not match:
                return self._empty_data(url)
            
            imdb_id = match.group(1)
            logger.info(f"📽️ Found IMDb ID: {imdb_id}")
            
            return self._fetch_omdb(imdb_id)
        except Exception as e:
            logger.error(f"❌ IMDb scraping failed: {e}")
            return self._empty_data(url)
    
    def _scrape_wikipedia(self, url: str) -> Dict:
        """Scrape từ Wikipedia (fallback if OMDb key not available)"""
        try:
            # Extract movie name từ Wikipedia URL
            movie_name = url.split('/wiki/')[-1].replace('_', ' ')
            logger.info(f"🎬 Movie from Wikipedia: {movie_name}")
            
            # Lấy basic metadata từ Wikipedia
            response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + movie_name.replace(' ', '_'),
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            
            if response.status_code != 200:
                # Fallback: search OMDb
                return self._search_omdb(movie_name)
            
            data = response.json()
            description = data.get('extract', '')
            
            return {
                "title": data.get('title', movie_name),
                "description": description,
                "short_description": description[:200] if description else movie_name,
                "price": "FREE (Watch now!)",  # Movies don't have "price"
                "platform": "movie",
                "original_url": url,
                "image_urls": [data.get('thumbnail', {}).get('source', '')] if data.get('thumbnail') else [],
            }
        except Exception as e:
            logger.error(f"❌ Wikipedia scraping failed: {e}")
            return self._empty_data(url)
    
    def _search_omdb(self, query: str) -> Dict:
        """Search movie by name via OMDb API"""
        try:
            # Nếu OMDb API key không có, dùng fallback
            if not self.omdb_api_key:
                logger.warning("⚠️ OMDb API key not set. Set OMDB_API_KEY env variable.")
                return self._search_wikipedia_fallback(query)
            
            response = requests.get(
                self.omdb_endpoint,
                params={
                    "apikey": self.omdb_api_key,
                    "t": query,
                    "type": "movie",
                    "plot": "full"
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('Response') == 'True':
                return {
                    "title": data.get('Title', query),
                    "description": data.get('Plot', ''),
                    "short_description": data.get('Plot', '')[:200],
                    "price": data.get('Runtime', 'N/A'),  # Runtime thay vì giá
                    "platform": "movie",
                    "original_url": "",
                    "image_urls": [data.get('Poster', '')] if data.get('Poster') else [],
                    "year": data.get('Year', ''),
                    "imdb_rating": data.get('imdbRating', ''),
                    "director": data.get('Director', ''),
                    "actors": data.get('Actors', ''),
                }
            
            # Nếu search không thấy
            logger.warning(f"⚠️ Movie not found in OMDb: {query}")
            return self._search_wikipedia_fallback(query)
            
        except Exception as e:
            logger.error(f"❌ OMDb search failed: {e}")
            return self._search_wikipedia_fallback(query)
    
    def _fetch_omdb(self, imdb_id: str) -> Dict:
        """Fetch data từ OMDb bằng IMDb ID"""
        try:
            if not self.omdb_api_key:
                logger.warning("⚠️ OMDb API key not set.")
                return self._empty_data("")
            
            response = requests.get(
                self.omdb_endpoint,
                params={
                    "apikey": self.omdb_api_key,
                    "i": imdb_id,
                    "plot": "full"
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('Response') == 'True':
                return {
                    "title": data.get('Title', ''),
                    "description": data.get('Plot', ''),
                    "short_description": data.get('Plot', '')[:200],
                    "price": data.get('Runtime', 'N/A'),
                    "platform": "movie",
                    "original_url": f"https://imdb.com/title/{imdb_id}",
                    "image_urls": [data.get('Poster', '')] if data.get('Poster') else [],
                    "year": data.get('Year', ''),
                    "imdb_rating": data.get('imdbRating', ''),
                    "director": data.get('Director', ''),
                    "actors": data.get('Actors', ''),
                    "genre": data.get('Genre', ''),
                }
            
            return self._empty_data("")
            
        except Exception as e:
            logger.error(f"❌ OMDb fetch failed: {e}")
            return self._empty_data("")
    
    def _search_wikipedia_fallback(self, query: str) -> Dict:
        """Fallback: search Wikipedia via Wikipedia API"""
        try:
            # Search Wikipedia
            search_response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query + " film",
                    "format": "json"
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            
            results = search_response.json().get('query', {}).get('search', [])
            if not results:
                return self._empty_data(query)
            
            # Lấy kết quả đầu tiên
            page_title = results[0]['title']
            
            # Fetch page content
            content_response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + page_title.replace(' ', '_'),
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            
            if content_response.status_code == 200:
                data = content_response.json()
                return {
                    "title": data.get('title', query),
                    "description": data.get('extract', ''),
                    "short_description": data.get('extract', '')[:200],
                    "price": "FREE (Watch now!)",
                    "platform": "movie",
                    "original_url": data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    "image_urls": [data.get('thumbnail', {}).get('source', '')] if data.get('thumbnail') else [],
                }
            
            return self._empty_data(query)
            
        except Exception as e:
            logger.error(f"❌ Wikipedia fallback failed: {e}")
            return self._empty_data(query)
    
    def _empty_data(self, query: str) -> Dict:
        """Return empty but valid data structure"""
        return {
            "title": f"Movie: {query[:50]}",
            "description": "Unable to fetch movie data. Please provide a valid URL or movie name.",
            "short_description": "Movie data not found",
            "price": "N/A",
            "platform": "movie",
            "original_url": "",
            "image_urls": [],
        }
