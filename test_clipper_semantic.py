"""
Test Video Clipper với chế độ Semantic (ASR + chọn câu hay)
Sử dụng Whisper để phân tích nội dung và tìm highlights thông minh
"""
import sys
import os

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from video.clipper import VideoHighlightDetector
from utils.logger import get_logger
import glob

logger = get_logger()

def test_semantic_clipper():
    """Test video clipper với semantic mode (ASR)"""
    
    print("=" * 80)
    print("🧠 TEST VIDEO CLIPPER - SEMANTIC MODE (ASR + Smart Selection)")
    print("=" * 80)
    print()
    
    # Tìm video test trong thư mục
    test_dirs = [
        "assets/temp/downloads/*.mp4",
        "output/videos/*.mp4",
        "*.mp4"
    ]
    
    video_files = []
    for pattern in test_dirs:
        video_files.extend(glob.glob(pattern))
    
    if not video_files:
        print("⚠️ Không tìm thấy video để test!")
        print("   Hãy tải một video về hoặc đặt video .mp4 vào thư mục gốc")
        print("\nThử tạo video demo...")
        create_demo_video()
        return
    
    # Test với video đầu tiên tìm thấy
    video_path = video_files[0]
    print(f"📹 Testing with video: {video_path}")
    print(f"   File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    print()
    
    detector = VideoHighlightDetector(
        min_clip_duration=10,
        max_clip_duration=30
    )
    
    # Test các methods
    methods = [
        ("semantic", "🧠 Semantic (Whisper ASR + Smart Selection)"),
        ("audio", "🔊 Audio Peaks (Fallback)"),
    ]
    
    for method, description in methods:
        print(f"\n{'='*80}")
        print(f"{description}")
        print(f"{'='*80}")
        
        try:
            highlights = detector.detect_highlights(
                video_path, 
                num_clips=5,
                method=method
            )
            
            if highlights:
                print(f"\n✅ Tìm thấy {len(highlights)} highlights:\n")
                
                for i, clip in enumerate(highlights, 1):
                    duration = clip['end'] - clip['start']
                    print(f"  Clip #{i}:")
                    print(f"    ⏱️  Time: {clip['start']:.1f}s → {clip['end']:.1f}s (duration: {duration:.1f}s)")
                    print(f"    📊 Score: {clip['score']:.3f}")
                    
                    # Hiển thị transcript nếu có (semantic mode)
                    if 'text' in clip and clip['text']:
                        print(f"    💬 Text: {clip['text'][:80]}...")
                    print()
                    
            else:
                print(f"❌ Không tìm thấy highlights với method '{method}'")
                
        except Exception as e:
            print(f"\n❌ Error with method '{method}': {e}")
            logger.error(f"Test failed: {e}", exc_info=True)
    
    # Cleanup
    detector.cleanup()
    
    print(f"\n{'='*80}")
    print("✅ VIDEO CLIPPER TEST COMPLETED")
    print(f"{'='*80}\n")
    
    print("\n📝 Kết luận:")
    print("  - Nếu Semantic mode thành công → Whisper đang hoạt động!")
    print("  - Nếu fallback to Audio → Kiểm tra video có audio track không")
    print("  - Highlights với 'text' field → ASR đã phân tích nội dung")
    print()

def create_demo_video():
    """Tạo video demo ngắn để test nếu không có video"""
    try:
        from moviepy.editor import ColorClip, AudioClip
        import numpy as np
        
        print("\n🎬 Creating demo video with audio...")
        
        # Tạo video màu đỏ 30s
        duration = 30
        clip = ColorClip(size=(640, 480), color=(255, 0, 0), duration=duration)
        
        # Thêm audio đơn giản (sine wave)
        def make_frame(t):
            frequency = 440  # A4 note
            return np.sin(2 * np.pi * frequency * t)
        
        audio = AudioClip(make_frame, duration=duration, fps=44100)
        clip = clip.set_audio(audio)
        
        # Save
        output_path = "test_demo_video.mp4"
        clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        print(f"✅ Demo video created: {output_path}")
        print(f"   Bây giờ chạy lại script này để test!")
        
    except Exception as e:
        print(f"❌ Không thể tạo demo video: {e}")
        print("   Hãy tải một video về để test")

if __name__ == "__main__":
    # Kiểm tra xem whisper có sẵn không
    try:
        import whisper
        print("✅ Whisper is installed and ready!")
        print(f"   Version: {whisper.__version__ if hasattr(whisper, '__version__') else 'unknown'}")
        print()
    except ImportError:
        print("⚠️ WARNING: Whisper not installed!")
        print("   Run: pip install openai-whisper")
        print("   Semantic mode will not work without it.\n")
    
    test_semantic_clipper()
