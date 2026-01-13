# Wav2Lip Setup Guide

## Yêu Cầu

- **GPU** (NVIDIA CUDA hoặc AMD): Để tăng tốc độ (~2-3 sec/video)
- **CPU**: Hoạt động nhưng chậm (~30-60 sec/video)
- **FFmpeg**: Đã cài sẵn với moviepy

## Quick Setup

### 1. **CPU Mode** (Dễ nhất, hoạt động ngay)
```powershell
# Đã cài sẵn, không cần gì thêm
$env:AVATAR_BACKEND = 'wav2lip'
.\.venv\Scripts\python.exe main.py
```

### 2. **GPU Mode** (Nếu có NVIDIA CUDA)
```powershell
# Cài PyTorch với CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Download models (lần đầu)
python -c "from video.wav2lip_avatar import Wav2LipAvatar; a = Wav2LipAvatar()"

# Chạy với GPU
$env:AVATAR_BACKEND = 'wav2lip'
.\.venv\Scripts\python.exe main.py
```

## Sử Dụng

### Từ Code
```python
from video.render import SmartVideoRenderer

# Tạo video với Wav2Lip talking avatar
renderer = SmartVideoRenderer(
    use_ai_avatar=True, 
    avatar_backend='wav2lip'  # Free local option
)

renderer.render(data, output_path='output.mp4')
```

### Từ GUI
1. Mở `main.py`
2. Chọn "Use AI Avatar" checkbox
3. Chọn "wav2lip" từ Avatar Backend dropdown
4. Upload ảnh reviewer + sản phẩm
5. Click "Generate Video"

## Backend Comparison

| Backend | Chi Phí | Tốc Độ | Chất Lượng | Cài Đặt |
|---------|--------|--------|-----------|--------|
| **Wav2Lip** (Local) | FREE | 2-3 sec (GPU) / 30-60 sec (CPU) | Lip-sync focused | Dễ |
| Colab SadTalker | FREE | 20-60 sec | Expressive | API setup phức tạp |
| D-ID API | $0.05/video | 10-20 sec | Cao nhất | Trả phí |

## Lỗi & Giải Pháp

### "ModuleNotFoundError: No module named 'torch'"
```powershell
# Cài PyTorch (chọn phiên bản theo GPU/CPU)
pip install torch
```

### "CUDA out of memory"
```powershell
# Sử dụng CPU mode (chậm hơn nhưng hoạt động)
# Hoặc giảm video resolution
```

### Setup chậm lần đầu
- Đúng, lần đầu phải download models (~300MB)
- Lần thứ 2+ sẽ nhanh

## Tips

1. **Test trước**: 
   ```powershell
   python -c "from video.wav2lip_avatar import Wav2LipAvatar; print('✅ Wav2Lip ready')"
   ```

2. **GPU vs CPU**: 
   - GPU (CUDA): Khuyên dùng, nhanh 10x
   - CPU: Hoạt động, nhưng chờ lâu

3. **Chất lượng tốt nhất**:
   - Ảnh reviewer: Mặt rõ, nhìn vào camera
   - Audio: Clear, pronunciation đúng
   - Video resolution: 1080p

## Tài Liệu

- Wav2Lip GitHub: https://github.com/Rudrabha/Wav2Lip
- PyTorch Setup: https://pytorch.org/get-started/locally/
