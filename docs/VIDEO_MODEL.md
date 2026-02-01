# Dùng mô hình video (image-to-video) trong dự án

Khi bật, mỗi scene affiliate có thể **sinh video từ ảnh sản phẩm** (thay cho ảnh tĩnh + motion). Hai lựa chọn:

---

## 1. Stable Video Diffusion (local – miễn phí, cần GPU)

- **Ảnh → video 2–4 giây** (model SVD-XT, ~25 frame).
- Chạy trên máy, **không tốn API**.
- Cần: GPU (khoảng 8GB+ VRAM), `torch`, `diffusers`.

### Cài đặt

```powershell
pip install torch diffusers transformers accelerate
```

### Bật

```powershell
$env:VIDEO_GENERATOR = "svd"
python main.py
```

Lần đầu sẽ tải model từ Hugging Face (~ vài GB). Sau đó mỗi scene sẽ gọi SVD: ảnh sản phẩm + câu script → video ngắn → ghép vào clip.

---

## 2. Runway API (trả phí)

- **Image-to-video** qua Runway (Gen-3).
- Cần: `RUNWAY_API_KEY`, `pip install runwayml`.

### Cài đặt

```powershell
pip install runwayml
```

### Bật

```powershell
$env:VIDEO_GENERATOR = "runway"
$env:RUNWAY_API_KEY = "your_api_key_here"
python main.py
```

Tạo API key tại [Runway](https://runwayml.com/). Chi phí theo credit (ví dụ ~5–10 credit/giây tùy model).

---

## Luồng trong code

1. **Render affiliate** (Product tab): với mỗi scene, nếu `VIDEO_GENERATOR` được set và có ảnh sản phẩm:
   - Gọi `video_gen.generate(image_path, prompt=script_line, output_path, duration)`.
   - Nếu thành công → dùng clip video đó (resize, fade, overlay title/CTA/caption).
   - Nếu lỗi hoặc không cấu hình → fallback **ảnh + motion** (zoom/pan/shake) như hiện tại.

2. **File**: `video/video_generator.py` – `StableVideoDiffusionGenerator`, `RunwayVideoGenerator`, `get_video_generator()`.

3. **Render**: `video/render.py` – trong `_build_scene_clip()` có đoạn thử `self.video_gen.generate(...)` trước khi gọi `make_premium_scene()`.

---

## Tắt mô hình video

Không set `VIDEO_GENERATOR` hoặc xóa biến env → toàn bộ scene dùng **ảnh + motion** (không gọi SVD/Runway).
