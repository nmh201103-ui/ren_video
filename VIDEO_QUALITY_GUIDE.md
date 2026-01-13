# 🎬 Hướng Dẫn Nâng Cấp Chất Lượng Video

## ✅ Đã Fix - Changes Applied

### 1. **Resolution: 720p → 1080p**
- Trước: 720x1280 (HD)
- Sau: **1080x1920 (Full HD)** ✨
- Chuẩn TikTok/YouTube Shorts

### 2. **FPS: 24fps → 30fps**
- Trước: 24fps (cinema style)
- Sau: **30fps** ✨
- Mượt mà hơn, phù hợp social media

### 3. **Bitrate: Auto → 8000k (8 Mbps)**
- Video bitrate: **8000k** cho 1080p
- Audio bitrate: **320k** (AAC high quality)
- Giảm compression artifacts

### 4. **CRF: None → 18**
- CRF (Constant Rate Factor): **18**
- Scale: 0 (lossless) đến 51 (worst)
- 18 = near-lossless, chất lượng rất cao

### 5. **Preset: medium → slow**
- Preset "slow" = better compression
- Trade-off: Render lâu hơn ~30-50%
- Chất lượng tốt hơn đáng kể

### 6. **Image Format: JPEG → PNG**
- JPEG quality 90 → **PNG lossless**
- Không mất chi tiết khi xử lý
- Giữ nguyên chất lượng gốc

### 7. **FFmpeg Optimizations**
```python
ffmpeg_params=[
    "-crf", "18",           # Near-lossless quality
    "-pix_fmt", "yuv420p",  # Universal color space
    "-profile:v", "high",   # H.264 High Profile
    "-level", "4.2",
    "-movflags", "+faststart"  # Web streaming
]
```

---

## 🚀 Nâng Cao Thêm (Optional)

### Option 1: Maximum Quality (Render rất lâu)
```python
# render.py - write_videofile()
bitrate="12000k",      # 12 Mbps
preset="veryslow",     # Chất lượng tối đa
ffmpeg_params=[
    "-crf", "15",      # Ultra high quality
    ...
]
```

### Option 2: H.265/HEVC (File nhỏ hơn, chất lượng tương đương)
```python
codec="libx265",       # H.265/HEVC
bitrate="5000k",       # Nhỏ hơn H.264 50% với quality tương đương
ffmpeg_params=[
    "-crf", "20",      # CRF cho H.265 (20-28)
    "-preset", "slow",
    "-pix_fmt", "yuv420p"
]
```
⚠️ **Note**: TikTok/YouTube hỗ trợ H.265 nhưng viewer device phải support

### Option 3: 4K (nếu có source images quality cao)
```python
self.template = {
    "width": 2160,
    "height": 3840,    # 4K vertical
    "fps": 30
}
bitrate="20000k"       # 20 Mbps cho 4K
```

### Option 4: 60fps (Ultra smooth)
```python
self.template = {
    "width": 1080,
    "height": 1920,
    "fps": 60          # Ultra smooth
}
bitrate="12000k"       # Cần bitrate cao hơn cho 60fps
```

---

## 📊 So Sánh Quality Settings

| Setting | Low | Medium | **High (Current)** | Ultra |
|---------|-----|--------|-------------------|-------|
| Resolution | 720p | 1080p | **1080p** | 4K |
| FPS | 24 | 24 | **30** | 60 |
| Bitrate | Auto | 4000k | **8000k** | 12000k |
| CRF | 23 | 21 | **18** | 15 |
| Preset | fast | medium | **slow** | veryslow |
| Render Time | 1x | 2x | **3-4x** | 6-8x |
| File Size | 5 MB | 10 MB | **20 MB** | 40 MB |

---

## 🎯 Lý Do Video Vẫn Không "Sora-like"

### ⚠️ Hiện Thực
**Sora/Veo là AI tạo VIDEO ĐỘNG từ text**, không phải slideshow:
- Sora: Generate actual video với camera movement, realistic motion
- Veo: Google's video generation với physics simulation
- Bạn: Static images + fade = slideshow

### 💡 Để Đạt "Sora-like" Quality:

#### 1. **Dùng Real Video Stock Footage**
```python
# Thay vì static images, dùng video clips
from moviepy.editor import VideoFileClip

video_clip = VideoFileClip("product_demo.mp4")
```

#### 2. **Add Motion to Static Images**
```python
# Ken Burns effect (zoom + pan)
def ken_burns_effect(img_clip, duration):
    return img_clip.resize(lambda t: 1 + 0.1*t/duration)  # Zoom in 10%
```

#### 3. **Thêm Transitions Cinematic**
```python
from moviepy.video.fx.all import fadein, fadeout, crossfadein, crossfadeout

clip = clip.fx(crossfadein, 1).fx(crossfadeout, 1)
```

#### 4. **Color Grading**
```python
def color_grade(clip):
    return clip.fx(vfx.colorx, 1.2)  # Tăng saturation
```

#### 5. **Dùng AI Avatar với SadTalker/D-ID**
```python
# Đã có trong code, enable nó:
use_ai_avatar=True
avatar_backend="colab"  # Free SadTalker
```

#### 6. **Add Background Music + Sound Effects**
```python
from moviepy.editor import AudioFileClip

bg_music = AudioFileClip("assets/music/upbeat.mp3").volumex(0.3)
video.audio = CompositeAudioClip([voice_audio, bg_music])
```

---

## 🔧 Quick Test Commands

### Test Current Settings:
```bash
python main.py
```

### Test với Ultra Quality:
Edit `render.py` line 179:
```python
bitrate="12000k",
preset="veryslow",
```

### Test 60fps:
Edit `render.py` line 47:
```python
self.template = template or {"width": 1080, "height": 1920, "fps": 60}
```

---

## 📈 Kết Quả Mong Đợi

### Trước (Old Settings):
- ❌ 720p @ 24fps
- ❌ Auto bitrate (~2-3 Mbps)
- ❌ JPEG compression
- ❌ "Củ chuối" quality

### Sau (New Settings):
- ✅ 1080p @ 30fps
- ✅ 8 Mbps bitrate + CRF 18
- ✅ PNG lossless
- ✅ Professional social media quality
- ⚠️ Vẫn là slideshow, không phải AI-generated video như Sora

### Để Đạt "Sora Level":
- 🎥 Cần dùng real video footage hoặc AI video generation APIs
- 💰 Hoặc integrate Runway ML, Pika Labs, etc.
- 🚀 Hoặc chờ OpenAI Sora API ra mắt

---

## 📝 Notes

1. **File size sẽ lớn hơn** (~20-30 MB thay vì 5-10 MB)
2. **Render time sẽ lâu hơn** (~3-5 phút thay vì 1-2 phút)
3. **Upload TikTok/YouTube vẫn compress lại** - nhưng input quality cao → output sau compression vẫn tốt hơn

**Bottom line**: Settings mới cho quality tốt nhất có thể với static images. Để đạt "Sora-like", cần chuyển sang real video generation hoặc video stock footage.
