# 🎬 NMH03 Video Pro v3 - Quick Guide

## 🚀 3 Chế độ chính:

### 1️⃣ Product Review (📦)
**Use case:** Review sản phẩm Shopee/TikTok Shop

**Workflow:**
```
1. Tab "Product Review"
2. Paste URL: https://shopee.vn/product/...
3. Chọn format:
   ⚡ Short (30s) - Viral TikTok
   📹 Medium (60s) - Instagram
   🎬 Long (3min) - YouTube
4. Chọn style:
   📹 Simple - Text + ảnh
   🎙️ Reviewer - AI avatar (cần upload ảnh mặt)
5. Generate!
```

**Output:**
- `product_short_20260114.mp4` (nếu chọn Short)
- Script 3-10 câu tùy format
- Auto voiceover (Vietnamese)

---

### 2️⃣ Movie Review (📽️)
**Use case:** Review/tóm tắt phim cho TikTok/YouTube

**Workflow:**
```
1. Tab "Movie Review"
2. Nhập:
   - IMDb URL: https://imdb.com/title/tt1234567
   - Wikipedia: https://en.wikipedia.org/wiki/Avatar_(2009_film)
   - Hoặc tên phim: "Oppenheimer", "Avatar 2"
3. Chọn format (Short/Medium/Long)
4. ✓ Enable "Auto Segment Detection"
5. ✓ (Optional) "Suggest 60s clips"
6. Generate!
```

**Output:**
- Full video: `movie_medium_20260114.mp4`
- Detected segments hiển thị trong panel
- Timestamps: `[00:00-00:15] INTRO`, `[00:15-00:35] PLOT`, etc.

**Export Options:**
- 💾 Export All Segments → Tách thành video riêng (intro.mp4, plot.mp4, etc.)
- 📋 Copy Timestamps → Paste vào YouTube description

---

### 3️⃣ Settings (⚙️)
**Optional API keys:**

```env
# Script generation (tốt hơn heuristic)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Movie metadata (nếu không có dùng Wikipedia free)
OMDB_API_KEY=...

# Premium AI avatar (nếu không có dùng Wav2Lip free)
DID_API_KEY=...
DID_API_SECRET=...

# Local LLM (free, offline)
OLLAMA_MODEL=gemma3:4b
```

---

## 📐 Format Recommendations

| Platform | Format | Duration | Best For |
|----------|--------|----------|----------|
| TikTok | ⚡ Short | 15-30s | Viral, hook-based |
| Instagram Reels | 📹 Medium | 45-60s | Quick review |
| YouTube Shorts | 📹 Medium | 60s | Standard format |
| YouTube Video | 🎬 Long | 2-5min | Full review + chapters |

---

## ✂️ Segment Detection (Movie Only)

**Auto-detects 5 chapter types:**

1. **INTRO** - Giới thiệu phim (tên, thể loại, đạo diễn)
   - Keywords: "giới thiệu", "tên phim", "thể loại"
   - Typical: 1 câu, ~5s

2. **PLOT** - Cốt truyện
   - Keywords: "câu chuyện", "phim kể về", "nội dung"
   - Typical: 2-3 câu, ~10-15s

3. **HIGHLIGHT** - Điểm nhấn, khoảnh khắc ấn tượng
   - Keywords: "đặc biệt", "ấn tượng", "nổi bật"
   - Typical: 1-2 câu, ~8s

4. **REVIEW** - Đánh giá, rating
   - Keywords: "đánh giá", "rating", "điểm"
   - Typical: 1 câu, ~5s

5. **CTA** - Call to action
   - Keywords: "xem ngay", "đừng bỏ lỡ", "trailer"
   - Typical: 1 câu, ~5s

**Example Output:**
```
1. [00:00 - 00:05] INTRO (1 sentence, 5.0s)
2. [00:05 - 00:18] PLOT (2 sentences, 13.0s)
3. [00:18 - 00:32] HIGHLIGHT (2 sentences, 14.0s)
4. [00:32 - 00:45] REVIEW (1 sentence, 13.0s)

✅ Total: 4 segments, ~45s
```

---

## 🎯 Use Cases

### Case 1: Viral TikTok (Product)
```
Format: ⚡ Short (30s)
Style: Simple
Script: 3 câu (hook → feature → CTA)
Output: 15-30s clip, ready to upload
```

### Case 2: YouTube Movie Review
```
Format: 🎬 Long (3min)
Enable: Auto Segments ✓
Output: 
  - Full video (3min)
  - 5 separate segments
  - Timestamps for description
```

### Case 3: Instagram Product Story
```
Format: 📹 Medium (60s)
Style: Reviewer + AI Avatar
Upload: Face photo
Output: Talking head video 45-60s
```

---

## 🆘 Troubleshooting

**Q: "Scraper failed" (Shopee)**
- ✅ Mở Chrome remote debugging: port 9222
- Command: `chrome.exe --remote-debugging-port=9222`

**Q: "Movie not found"**
- ✅ Dùng IMDb URL hoặc Wikipedia link
- ✅ Hoặc set `OMDB_API_KEY` (free tier: https://omdbapi.com)

**Q: "Segments không hiển thị"**
- ✅ Chỉ có Movie Review mới có segment detection
- ✅ Phải bật "Auto Segment Detection" ✓

**Q: "Script quá ngắn/dài"**
- ✅ Chọn format phù hợp:
  - Short → 3 câu
  - Medium → 5 câu
  - Long → 10+ câu

---

## 💡 Pro Tips

1. **Short format = Viral potential**
   - Hook trong 2s đầu
   - 1 key point duy nhất
   - CTA rõ ràng

2. **Long format = SEO + Revenue**
   - Đầy đủ thông tin
   - Chapters tăng watch time
   - Copy timestamps vào description

3. **Segment export = Content repurposing**
   - Export intro → Teaser
   - Export highlights → Reel viral
   - Export review → Standalone opinion

4. **AI Avatar = Higher engagement**
   - Upload ảnh mặt rõ nét
   - Ánh sáng đều
   - Nhìn thẳng camera

---

## 📊 Performance Tips

**Render nhanh:**
- Format Short (3 scenes) ~ 30s render
- Format Long (10 scenes) ~ 2-3 phút render
- Disable AI avatar nếu cần nhanh

**Chất lượng cao:**
- 1080p @ 30fps (chuẩn TikTok/YouTube)
- H.264 encoding, CRF 18 (near-lossless)
- Bitrate 8Mbps video + 320kbps audio

**API cost:**
- gTTS (free) vs ElevenLabs ($paid)
- Wav2Lip (free local) vs D-ID ($0.3/video)
- OpenAI GPT-3.5 (~$0.001/request) vs Ollama (free)

---

## 🔗 Resources

- OMDb API (movie data): https://www.omdbapi.com/
- OpenAI API: https://platform.openai.com/
- Ollama (local LLM): https://ollama.com/
- D-ID (avatar): https://www.d-id.com/

---

Made with ❤️ by NMH03 Team
Version 3.0 - January 2026
