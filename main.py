import sys
import os
import io

# Fix UTF-8 encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ép Python tìm kiếm module từ thư mục gốc
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import chính xác từ gui/app.py
    from gui.app import VideoCreatorApp
    print("✅ Đã kết nối module GUI thành công")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

if __name__ == "__main__":
    app = VideoCreatorApp()
    app.run()
