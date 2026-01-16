"""
Test Movie Review Generation
Test tạo review phim từ URL IMDb hoặc Wikipedia
"""
import sys
import os

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scraper.movie import MovieScraper
from utils.logger import get_logger

logger = get_logger()

def test_movie_scraper():
    """Test movie scraper với nhiều loại URL"""
    
    test_urls = [
        # IMDb URLs
        "https://www.imdb.com/title/tt0111161/",  # The Shawshank Redemption
        "https://www.imdb.com/title/tt0068646/",  # The Godfather
        
        # Wikipedia URLs
        "https://en.wikipedia.org/wiki/The_Matrix",
        "https://en.wikipedia.org/wiki/Inception",
        
        # Direct movie names
        "Interstellar",
        "The Dark Knight"
    ]
    
    scraper = MovieScraper()
    
    print("=" * 80)
    print("🎬 TEST MOVIE REVIEW GENERATOR")
    print("=" * 80)
    print()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*80}")
        print(f"Test #{i}: {url}")
        print(f"{'='*80}")
        
        try:
            result = scraper.scrape(url)
            
            print(f"\n✅ Kết quả:")
            print(f"  📌 Title: {result.get('title', 'N/A')}")
            print(f"  📝 Description: {result.get('description', 'N/A')[:200]}...")
            print(f"  🔗 Platform: {result.get('platform', 'N/A')}")
            print(f"  🖼️  Images: {len(result.get('image_urls', []))} found")
            
            if result.get('rating'):
                print(f"  ⭐ Rating: {result.get('rating')}")
            if result.get('genre'):
                print(f"  🎭 Genre: {result.get('genre')}")
            if result.get('year'):
                print(f"  📅 Year: {result.get('year')}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Test failed for {url}: {e}", exc_info=True)
    
    print(f"\n{'='*80}")
    print("✅ MOVIE SCRAPER TEST COMPLETED")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    test_movie_scraper()
