# NMH03 Video Pro v3 - Complete Edition

🎬 Tạo video Shorts/TikTok/Reels/YouTube tự động từ:
- 📦 **Sản phẩm** (Shopee, TikTok Shop) → Review video + AI avatar
- 📽️ **Phim** (IMDb, Wikipedia) → Review/tóm tắt với auto-segment detection
- ⚡ **3 formats**: Short (15-30s), Medium (60s), Long (2-5 phút)
- ✂️ **Auto segments**: Tự động tách chapters + export riêng

## ✨ Features v3

### 📐 Multiple Video Formats
- **⚡ Short (15-30s)** - 3 scenes, perfect for TikTok/Reels viral
- **📹 Medium (45-60s)** - 5 scenes, Instagram/YouTube Shorts
- **🎬 Long (2-5 min)** - 10+ scenes, full YouTube review

### ✂️ Smart Segment Detection (Movie Only)
- **Auto-detect chapters**: Intro, Plot, Highlights, Review, CTA
- **Export segments separately**: Mỗi chapter thành video riêng
- **Copy timestamps**: Paste vào YouTube description
- **Suggest 60s clips**: Tự động gợi ý cắt thành TikTok/Reels

### 🎨 Presentation Modes
- **📹 Simple**: Product/movie + text overlay + voiceover
- **🎙️ Reviewer**: Talking head với AI avatar (Wav2Lip/D-ID)

### 🤖 AI-Powered
- **Script Generation**: OpenAI/Ollama/Heuristic
- **Text-to-Speech**: gTTS (free) hoặc ElevenLabs (premium)
- **Talking Avatar**: Wav2Lip (free local) hoặc D-ID (paid API)

---

## Quick Start

### 1. Setup Chrome với Remote Debugging (cho Shopee scraping)

```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="E:\chrome_profile_affiliate"
```

### 2. Setup Python Environment (Python 3.11 recommended)

```powershell
# Tạo virtual environment với Python 3.11
python -m venv .venv

# Activate venv (QUAN TRỌNG!)
.\.venv\Scripts\Activate.ps1

# Cài dependencies
pip install -r requirements.txt

# Cài Playwright browsers
playwright install chromium
```

### 3. Run Application

```powershell
# Sau khi activate venv
python main.py

# Hoặc dùng trực tiếp (không cần activate)
.\.venv\Scripts\python.exe main.py
```

**Lưu ý:** Luôn đảm bảo venv được activate (thấy `(.venv)` ở đầu prompt) trước khi chạy để tránh thiếu thư viện!

---

## 🎯 How to Use

### 🎬 Movie Review Workflow

1. **Switch to "📽️ Movie Review" tab**
2. **Enter movie:**
   - IMDb URL: `https://www.imdb.com/title/tt1234567/`
   - Wikipedia: `https://en.wikipedia.org/wiki/Oppenheimer_(film)`
   - Or just: `Avatar`, `Interstellar`, etc.

3. **Choose format:**
   - ⚡ Short (30s) - Quick teaser
   - 📹 Medium (60s) - Standard review
   - 🎬 Long (3-5min) - Full analysis

4. **Enable Auto Segment Detection** ✓
   - App tự động tách: [Intro] [Plot] [Highlights] [Review]
   - Hiển thị timestamps + duration từng phần

5. **Click "Generate Movie Review"**
   - AI tạo script theo format
   - Render full video
   - Segments xuất hiện trong panel

6. **Export Options:**
   - 💾 Export All Segments → Tách thành các video riêng
   - 📋 Copy Timestamps → Paste vào YouTube description

### 📦 Product Review Workflow

1. **Switch to "📦 Product Review" tab**
2. **Paste Shopee/TikTok URL**
3. **Choose format** (Short/Medium/Long)
4. **Choose style:**
   - 📹 Simple (text + images)
   - 🎙️ Reviewer (upload face → AI talking avatar)
5. **Generate!**

---

## 📐 Video Format Comparison

| Format | Duration | Scenes | Best For | Use Case |
|--------|----------|--------|----------|----------|
| ⚡ **Short** | 15-30s | 3 | TikTok, Reels | Hook + key point + CTA |
| 📹 **Medium** | 45-60s | 5 | YouTube Shorts | Quick review with details |
| 🎬 **Long** | 2-5 min | 10+ | YouTube video | Full analysis + chapters |

---

## ✂️ Segment Detection Example

**Input:** `Oppenheimer` movie review

**Auto-detected segments:**
```
1. [00:00 - 00:05] INTRO (1 sentence, 5s)
   "🎬 Oppenheimer - phim tiểu sử khoa học đầy kịch tính"

2. [00:05 - 00:18] PLOT (2 sentences, 13s)
   "Phim kể về J. Robert Oppenheimer, cha đẻ bom nguyên tử..."

3. [00:18 - 00:32] HIGHLIGHT (2 sentences, 14s)
   "Những khoảnh khắc căng thẳng trong phòng thí nghiệm..."

4. [00:32 - 00:45] REVIEW (1 sentence, 13s)
   "Đánh giá: 8.5/10 ⭐ - Masterpiece của Christopher Nolan"
```

**Export:**
- Full video: `movie_long_20260114_143022.mp4`
- Segment 1: `segments/intro_oppenheimer.mp4`
- Segment 2: `segments/plot_oppenheimer.mp4`
- etc.

---

## 📽️ Movie Review Feature (NEW!)

### ✂️ **Auto Segment Detection** - Tách video thành chapters tự động

App v2 tự động phát hiện các phần trong movie review:
- **Intro**: Giới thiệu phim (tên, thể loại, đạo diễn)
- **Plot**: Cốt truyện chính
- **Highlight**: Điểm nổi bật, khoảnh khắc ấn tượng
- **Review**: Đánh giá, rating
- **CTA**: Lời kêu gọi (xem trailer, check IMDb, etc.)

### Cách sử dụng:

1. **Chọn tab "📽️ Movie Review"** trong app
2. **Nhập URL hoặc tên phim:**
   - `https://www.imdb.com/title/tt1234567/`
   - `https://en.wikipedia.org/wiki/Avatar_(2009_film)`
   - Hoặc chỉ cần gõ tên phim: `Avatar`, `Oppenheimer`, etc.

3. **Bật "Auto-detect chapters"** → App tự động tách script thành segments
4. **Tùy chọn: "Suggest short clips"** → Gợi ý cắt thành clips 60s cho TikTok/Reels
5. **Click "Generate Movie Review"** → AI tạo script review + render video

### Segment Detection Output:

Sau khi generate, app sẽ hiển thị:
```
1. [INTRO] 1 câu (~4.5s)
2. [PLOT] 2 câu (~9.0s)
3. [HIGHLIGHT] 2 câu (~9.0s)
4. [REVIEW] 1 câu (~4.5s)
```

Bạn có thể:
- Xem danh sách segments trong GUI
- Export segments riêng (future feature)
- Tự động tạo timestamps/chapters cho YouTube

### Script tự động tạo:
- Hook gây chú ý (tên + thể loại)
- Tóm tắt sơ bộ (không spoil)
- Điểm nổi bật / khoảnh khắc ấn tượng
- Đánh giá + lời kêu gọi xem

### Yêu cầu API (optional):
Để lấy dữ liệu chi tiết từ IMDb:
```
OMDB_API_KEY=your_key_here  # Lấy free tại https://www.omdbapi.com/
```

Nếu không có key, app sẽ fallback sang Wikipedia API (free, không cần key).

---

## AI Providers & Configuration

### Environment Variables:

**Script Generation (LLM):**
- `OPENAI_API_KEY` — Required để dùng ChatGPT cho script generation
- `OPENAI_MODEL` (optional, default: `gpt-3.5-turbo`)
- `LLM_PROVIDER` (optional: `openai` hoặc `ollama`)
- `LLM_STYLE` (optional: `veo3`, `sora`, `default`)

**Movie Data:**
- `OMDB_API_KEY` (optional) — Free tier cho IMDb lookups. Nếu không có, dùng Wikipedia

**AI Avatar (Talking Head):**
- `DID_API_KEY` + `DID_API_SECRET` (optional, D-ID premium backend)
- Hoặc dùng **Wav2Lip** (free local) — no API key needed

**Text-to-Speech (Optional):**
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` (premium TTS)
- Mặc định: gTTS (free Google Translate TTS)

**Local LLM (Optional):**
```bash
# Install Ollama: https://ollama.com
ollama pull gemma3:4b

# Set env vars
export OLLAMA_MODEL=gemma3:4b
export OLLAMA_TIMEOUT=120
```

### Example setup (Movie Review with OpenAI):

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:OMDB_API_KEY="your_omdb_key"
python main.py
```

---

## Video Modes & Presets

| Preset | Mode | Avatar | Use Case |
|--------|------|--------|----------|
| 📦 Unboxing | Reviewer | ✅ Wav2Lip | Unboxing sản phẩm |
| ⭐ Review | Reviewer | ✅ Wav2Lip | Review sản phẩm (talking head) |
| 📹 Simple | Simple | ❌ No | Text + images (nhanh) |
| 📽️ Movie | Simple | ❌ No | Review phim (không cần avatar) |

---

## Supported Platforms

### Input (Scraping):
- ✅ **Shopee** (requires Chrome remote debugging)
- ✅ **TikTok Shop** (basic support)
- ✅ **IMDb** (movie links)
- ✅ **Wikipedia** (movie links)
- ✅ **Direct movie names** (via OMDb/Wikipedia)

### Output:
- 🎬 **TikTok / Shorts / Reels** (1080x1920, 30fps)
- 📁 **Local MP4** (high quality H.264)

---

## Performance tips

- Preload remote assets to reduce render stalls (the renderer now downloads assets concurrently when possible).
- For large jobs, pin `Pillow<10` only if you depend on legacy behavior, or keep latest and ensure third-party libs are compatible.
- Increase `threads` argument in `write_videofile` for faster encoding if you have CPU resources.

---

## Troubleshooting

**Q: "Scraper failed" khi chạy Shopee**
- A: Chắc chắn Chrome có remote debugging port 9222 mở (xem Quick Start #1)

**Q: Script generation quá lâu**
- A: Chuyển sang Ollama (local LLM) hoặc tắt AI avatar để nhanh hơn

**Q: Phim không tìm thấy**
- A: Thử IMDb URL hoặc Wikipedia link. Nếu dùng tên, cần OMDB_API_KEY.

---

## Advanced: Custom Script Generators

```python
from video.ai_providers import MovieScriptGenerator

# Dùng OpenAI
gen = MovieScriptGenerator(
    use_llm=True,
    api_key="sk-..."
)

script = gen.generate(
    title="Avatar (2009)",
    description="Sci-fi epic about Na'vi people...",
)
print(script)  # ['Hook...', 'Plot...', 'Highlight...', 'Rating...']
```


