"""Test video downloader with improved retry logic"""
from video.downloader import VideoDownloader
from utils.logger import get_logger
import sys

logger = get_logger()

def test_download():
    """Test downloading a video"""
    downloader = VideoDownloader()
    
    # Test URL (Rick Roll - known working video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"Testing download from: {test_url}")
    print("="*60)
    
    result = downloader.download(test_url)
    
    if result:
        import os
        file_size = os.path.getsize(result)
        print(f"\n✅ SUCCESS!")
        print(f"📁 Path: {result}")
        print(f"📊 Size: {file_size/1024/1024:.1f}MB")
        return True
    else:
        print(f"\n❌ FAILED!")
        print("Check logs above for details")
        return False

if __name__ == "__main__":
    success = test_download()
    sys.exit(0 if success else 1)
