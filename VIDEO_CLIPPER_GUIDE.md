# 🎬 Video Clipper Guide - Tự động cắt Highlights từ Video

## 📌 Tính năng mới: Auto-Cut Video Highlights

App đã có **Tab "Video Clipper"** - tự động phát hiện và cắt những đoạn hay nhất từ video YouTube/TikTok thành short clips!

---

## 🚀 Cách sử dụng

### Bước 1: Mở Tab "✂️ Video Clipper"
- Mở app → Click tab **"Video Clipper"** (tab thứ 3)

### Bước 2: Dán URL Video
Hỗ trợ:
- ✅ YouTube: `https://youtube.com/watch?v=...`
- ✅ TikTok: `https://tiktok.com/@user/video/...`
- ✅ Instagram: `https://instagram.com/reel/...`
- ✅ Facebook: `https://facebook.com/watch/...`

### Bước 3: Chọn cài đặt

**📐 Clip Format:**
- **Short (15-30s)**: Cho TikTok/Reels viral
- **Medium (30-60s)**: YouTube Shorts/Instagram

**🎬 Number of Clips:**
- Chọn 1-10 clips (mặc định: 5)
- App sẽ tự chọn những đoạn hay nhất

**🔍 Detection Method:**
- **Audio Peaks** (Khuyên dùng): Tìm đoạn có âm thanh lớn/hấp dẫn
  - Tự động phát hiện: action scenes, nhạc cao trào, tràn cười
  - Nhanh và chính xác
  
- **Uniform**: Cắt đều đặn (backup)
  - Dùng khi video ít action

### Bước 4: Nhấn "✂️ Auto-Cut Video"

**Quy trình tự động:**
```
1. 📥 Download video (yt-dlp)
2. 🔊 Phân tích audio - tìm peak moments
3. ✂️ Cắt clips theo format
4. 💾 Lưu vào output/clips/
5. 📊 Hiển thị kết quả
```

---

## 📊 Kết quả

Sau khi xử lý, bạn sẽ thấy:

```
✅ Generated 5 clips:

1. 45.2s - 60.3s (15.1s)
   Score: 0.85
   📁 output/clips/clip_001_45.2-60.3.mp4

2. 120.5s - 148.7s (28.2s)
   Score: 0.92
   📁 output/clips/clip_002_120.5-148.7.mp4
```

**Score càng cao = đoạn càng hay!**

---

## 🎯 Use Cases

### 1️⃣ Review Phim → Highlight Reel
```
Input: https://youtube.com/watch?v=trailer_avatar2
→ 5 clips: action scenes, best moments
→ Upload lên TikTok/Reels
```

### 2️⃣ Gaming Video → Best Plays
```
Input: https://youtube.com/watch?v=gameplay_elden_ring
→ 10 clips: epic kills, boss fights
→ Viral shorts
```

### 3️⃣ Vlog → Funny Moments
```
Input: https://tiktok.com/@user/video/123
→ 3 clips: cười nhiều nhất
→ Re-upload với caption mới
```

---

## 🔧 Advanced Settings

### Audio Peak Detection (Mặc định)
```python
# Tự động phát hiện:
- Tiếng hét/la hét (action scenes)
- Nhạc cao trào (music videos)
- Tiếng cười (comedy)
- Tiếng nổ/va chạm (fights)
```

**Tham số:**
- `min_duration`: 10s (đoạn tối thiểu)
- `overlap_threshold`: 0.5 (tránh trùng lặp)
- `score_threshold`: 0.6 (chất lượng tối thiểu)

### Uniform Distribution
```python
# Cắt đều:
- Video 5 phút → 5 clips = mỗi phút 1 clip
- Đơn giản nhưng ít thông minh
```

---

## 📦 Yêu cầu cài đặt

### Cài yt-dlp (nếu chưa có):
```bash
pip install yt-dlp
```

Hoặc update requirements:
```bash
pip install -r requirements.txt
```

### Kiểm tra FFmpeg:
```bash
ffmpeg -version
```

Nếu chưa có: [Download FFmpeg](https://ffmpeg.org/download.html)

---

## 💡 Pro Tips

### ✅ Làm sao để có clips viral?
1. **Chọn video HOT**: Trending movies, popular games
2. **Audio Peaks**: Luôn chọn "Audio Peaks" cho action/comedy
3. **15-30s**: TikTok/Reels yêu thích độ dài này
4. **Caption tốt**: Thêm text overlay sau khi cắt

### ✅ Tối ưu quality:
- Chọn video gốc HD (720p+)
- Dùng 5-7 clips cho video 5-10 phút
- Kiểm tra preview trước khi upload

### ✅ Tránh copyright:
- ⚠️ **CẢNH BÁO**: Không upload trực tiếp clip từ phim/nhạc có bản quyền
- ✅ **AN TOÀN**: Thêm commentary, reaction, review
- ✅ **TƯƠNG TÁC**: Dùng làm B-roll, kết hợp với talking head

---

## 🐛 Troubleshooting

### ❌ "yt-dlp not installed"
```bash
pip install yt-dlp
```

### ❌ "Failed to download video"
- Kiểm tra URL hợp lệ
- Thử video khác (có thể bị region-lock)
- Update yt-dlp: `pip install -U yt-dlp`

### ❌ "No clips generated"
- Video quá ngắn (< 1 phút)
- Thử "Uniform" method
- Giảm số clips xuống 3

### ❌ "FFmpeg not found"
- Cài FFmpeg: https://ffmpeg.org
- Add vào PATH (Windows)

---

## 📈 Workflow hoàn chỉnh

### Tạo Video Review Phim Viral:

```mermaid
1. Tab "Movie Review" 
   → Nhập URL IMDb
   → Generate script + segments

2. Tab "Video Clipper"
   → Dán URL trailer YouTube
   → Auto-cut 5 highlights (15-30s)

3. Combine:
   → Dùng clips làm B-roll
   → Thêm voiceover/talking head
   → Upload TikTok/YouTube Shorts
```

**Kết quả:**
- ✅ Nội dung chất lượng (AI script)
- ✅ Visual đẹp (clips từ trailer gốc)
- ✅ Nhanh (tự động cắt + render)
- ✅ Viral potential (highlight moments)

---

## 🎓 Ví dụ thực tế

### Case 1: Review Avatar 2
```
1. Movie tab: "https://imdb.com/title/tt1630029"
   → Script: 10 segments, 2:30s

2. Clipper tab: "https://youtube.com/watch?v=trailer_avatar2"
   → 5 clips: underwater scenes, flight sequences, battles

3. Render:
   → Talking head + B-roll clips
   → TTS voice + avatar
   → Export → 2:30s vertical video

4. Upload TikTok:
   → Caption: "Avatar 2 Review - Kĩ xảo đỉnh của chóp! 🔥"
   → Hashtags: #avatar2 #moviereview #film2024
```

**Metrics:**
- Views: 50K-500K (nếu trending)
- Engagement: 5-10% (quality content)
- Watch time: High (viral clips)

---

## 🚀 Next Steps

### Tính năng sắp có:
- [ ] Scene detection (AI visual analysis)
- [ ] Face detection (closeup moments)
- [ ] Text overlay automation
- [ ] Multi-platform export (TikTok/Reels/Shorts)
- [ ] Thumbnail generator

### Tích hợp:
- Kết hợp Movie Review + Clipper
- Auto B-roll cho Product videos
- Batch processing (nhiều videos cùng lúc)

---

## 📞 Support

**Issues?** → Check [logs/app.log](logs/app.log)

**Feature requests?** → Update [VIDEO_CLIPPER_GUIDE.md](VIDEO_CLIPPER_GUIDE.md)

---

**Happy Clipping! 🎬✂️**
