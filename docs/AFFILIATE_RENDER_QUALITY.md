# Chất lượng render video Affiliate & hướng nâng cấp kiểu Veo3/Sora

## 1. Hiện trạng – Chức năng đang có

### Pipeline
- **Product tab** (`gui/tabs/product_tab.py`): URL → scrape → `ContentProcessor` → script (3/5/10 câu theo format Short/Medium/Long) → **SmartVideoRenderer.render()**
- **Script**: OpenAI / Ollama / Heuristic (Hook → Giải pháp → Lợi ích → CTA), có env `LLM_STYLE` (veo3/sora/default).
- **Encode**: 1080x1920, 30fps, 8Mbps, CRF 18, AAC 320k, preset slow – **đạt chuẩn tốt**.

### Scene (video/render.py – `make_premium_scene`)
| Tính năng | Trạng thái |
|-----------|------------|
| 1 ảnh per scene | ✅ |
| Blur nền, product căn giữa | ✅ |
| Xóa nền sản phẩm (rembg) | ✅ (reviewer mode) |
| Avatar tròn góc (reviewer) | ✅ (ảnh tĩnh, không nói) |
| **Text overlay (title, giá, CTA trên hình)** | ❌ **Không có** – comment trong code: "Audio only, no text overlay" |
| **Motion (zoom/pan/Ken Burns)** | ❌ **Không có** – chỉ fade in/out 0.3s |
| **Caption/subtitle theo câu** | ❌ Không có |
| Transition giữa scene | Chỉ cắt thẳng (cut) |

### TTS (video/ai_providers.py)
- **GTTSProvider** (gTTS): đang dùng – giọng robot, miễn phí.
- **ElevenLabsTTSProvider**: có class nhưng `tts_to_file` trả về `None` – **chưa dùng**.

### Template (video/templates.py)
- Có `title_color`, `price_color`, `cta_color`, `title_font_size`, v.v. nhưng **render.py không dùng** – không vẽ title/price/CTA lên video.

### Kết luận tại sao “chất lượng chưa tốt”
1. **Toàn ảnh tĩnh** – không zoom/pan → cảm giác slideshow.
2. **Không có chữ trên hình** – thiếu lower-third, giá, CTA → kém “review chuẩn”.
3. **Giọng gTTS** – nghe robot, không tự nhiên như Veo/Sora voice.
4. **Không caption** – người xem tắt tiếng khó follow.
5. **Cắt thẳng giữa các scene** – không crossfade/transition mượt.

---

## 2. Cần thêm gì để gần “AI review kiểu Veo3/Sora”

### Mức 1 – Cải thiện trong code hiện tại (không cần API AI video)

| Hạng mục | Việc cần làm | File liên quan |
|----------|--------------|----------------|
| **Motion ảnh** | Ken Burns: zoom nhẹ hoặc pan chậm theo thời gian (MoviePy `resize`/`set_position` theo `t`) | `video/render.py` – `make_premium_scene` |
| **Text overlay** | Vẽ title (scene đầu), giá, CTA (scene cuối hoặc mỗi scene) lên từng clip; dùng `templates.py` (color, font_size) | `video/render.py`, `video/templates.py` |
| **Font ổn định** | Fallback font (e.g. Arial/Consolas) nếu không có `fonts/Roboto-Bold.ttf`; hoặc embed font | `video/render.py` – `load_font()` |
| **Caption/subtitle** | Tạo TextClip theo từng câu, sync với duration của scene; có thể làm đơn giản: 1 dòng chữ dưới màn hình | `video/render.py` – sau khi có audio duration |
| **Transition** | Crossfade 0.3–0.5s giữa hai clip (MoviePy `crossfadeout`/`crossfadein`) | `video/render.py` – khi `CompositeVideoClip` |
| **TTS tốt hơn** | Implement `ElevenLabsTTSProvider.tts_to_file()` (gọi API ElevenLabs) và chọn TTS theo env (e.g. `ELEVENLABS_API_KEY`) | `video/ai_providers.py`, `video/render.py` (chọn provider) |

### Mức 2 – Chất lượng “pro” hơn

- **Motion preset**: Nhiều kiểu (zoom in, zoom out, pan trái/phải) chọn theo scene index hoặc random.
- **Lower-third**: Box nửa trong suốt + tên sản phẩm / giá cố định vài giây.
- **Script pacing**: Dùng `script_optimizer.py` (nếu có) để fit đúng target_duration, tránh scene quá ngắn/dài.
- **Preview/thumbnail**: Frame đẹp cho YouTube/TikTok (scene hook + text).

### Mức 3 – Giống Veo/Sora thật (AI sinh video)

- **Veo 3 / Sora / Runway**: Gọi API “text/script → video” cho từng đoạn – **tốn tiền**, cần tích hợp API, xử lý độ dài clip và sync với voice.
- **Hướng lai**: Giữ ảnh product + Ken Burns + overlay + TTS tốt; chỉ 1–2 shot “hero” dùng AI video (nếu có API) để tăng cảm giác “native AI”.

---

## 3. Thứ tự đề xuất làm

1. **Text overlay** (title, giá, CTA) + dùng `templates.py` – thấy chất lượng lên rõ.
2. **Ken Burns** (zoom/pan nhẹ) trên từng scene – bớt tĩnh.
3. **ElevenLabs** (hoặc TTS khác) – giọng tự nhiên hơn.
4. **Caption** (1 dòng theo câu) – tăng retention và accessibility.
5. **Crossfade** giữa scene – mượt hơn.
6. (Tùy chọn) **Motion preset** đa dạng và **AI video API** cho vài shot đặc biệt.

---

## 4. File cần sửa chính

| File | Thay đổi chính |
|------|----------------|
| `video/render.py` | `make_premium_scene`: thêm Ken Burns; tạo TextClip title/price/CTA; composite lên clip; crossfade khi nối clip. |
| `video/ai_providers.py` | Implement `ElevenLabsTTSProvider.tts_to_file`; trong `render.py` chọn TTS theo env. |
| `video/templates.py` | Đã có sẵn; chỉ cần render.py đọc và dùng. |
| `video/render.py` | `load_font`: fallback font nếu thiếu file. |

Sau khi làm xong Mức 1, video affiliate sẽ “pro” hơn rõ, gần kiểu review AI (Veo3/Sora) về mặt trình bày và motion, dù vẫn dùng ảnh product chứ chưa cần API sinh video.
