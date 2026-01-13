# 🔧 Fix Lỗi Colab SadTalker API

## ❌ Lỗi Hiện Tại

```
ERROR: Command 'python inference.py --driven_audio ... --enhancer gfpgan' 
returned non-zero exit status 1.
```

## 🎯 Nguyên Nhân

1. **GFPGAN enhancer đang gây lỗi** - model này hay bị crash
2. **Preprocessing mode "full" quá nặng** - dễ timeout/fail
3. **Thiếu error handling** trong Colab notebook

## ✅ Giải Pháp - Update Colab Notebook

### Option 1: Quick Fix (Khuyến nghị)

Trong notebook `SadTalker_Colab_Free.ipynb`, tìm cell API endpoint và sửa lại:

```python
# Cell API Endpoint - SỬA LẠI
from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Save uploaded files
        image = request.files['image']
        audio = request.files['audio']
        
        os.makedirs('/tmp/avatar_input', exist_ok=True)
        os.makedirs('/tmp/results', exist_ok=True)
        
        image_path = '/tmp/avatar_input/input.jpg'
        audio_path = '/tmp/avatar_input/input.wav'
        
        image.save(image_path)
        audio.save(audio_path)
        
        # Get optional parameters
        preprocess = request.form.get('preprocess', 'crop')  # crop = faster & stable
        still_mode = request.form.get('still_mode', 'true') == 'true'
        enhancer = request.form.get('enhancer', 'none')  # none = avoid GFPGAN errors
        
        # Build command - FIX: Use safer parameters
        cmd = [
            'python', 'inference.py',
            '--driven_audio', audio_path,
            '--source_image', image_path,
            '--result_dir', '/tmp/results',
            '--preprocess', preprocess  # 'crop' instead of 'full'
        ]
        
        # Add still mode
        if still_mode:
            cmd.append('--still')
        
        # Add enhancer only if not 'none'
        if enhancer and enhancer != 'none':
            cmd.extend(['--enhancer', enhancer])
        
        # Run inference with timeout
        result = subprocess.run(
            cmd, 
            cwd='/content/SadTalker',
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            # Return detailed error
            return {
                'error': f'Inference failed: {result.stderr}',
                'stdout': result.stdout,
                'command': ' '.join(cmd)
            }, 500
        
        # Find output video
        output_dir = '/tmp/results'
        video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
        
        if not video_files:
            return {'error': 'No video generated'}, 500
        
        video_path = os.path.join(output_dir, video_files[0])
        
        return send_file(video_path, mimetype='video/mp4')
        
    except subprocess.TimeoutExpired:
        return {'error': 'Processing timeout (>2 minutes)'}, 500
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}

# Run ngrok tunnel
from flask_ngrok import run_with_ngrok
run_with_ngrok(app)
app.run()
```

### Option 2: Dùng Notebook Mới (Easiest)

Tôi đã update code, bạn chỉ cần:

1. **Restart Colab runtime**:
   - Runtime → Restart runtime
   
2. **Chạy lại setup cells** (Cell 1-4)
   - Đợi 5-10 phút cài đặt

3. **Chạy Cell 5 (API Server)** với code mới ở trên

4. **Copy ngrok URL** và set lại:
   ```powershell
   $env:COLAB_API_URL="<new-url>"
   ```

### Option 3: Alternative - Dùng RestoreFormer

Nếu muốn giữ enhancer (face restoration), dùng RestoreFormer thay vì GFPGAN:

```python
# Trong command
cmd.extend(['--enhancer', 'RestoreFormer'])  # Stable hơn GFPGAN
```

## 🚀 Test Fix

### Test 1: Check Colab đang chạy

```powershell
# PowerShell
$response = Invoke-WebRequest -Uri "$env:COLAB_API_URL/health"
$response.StatusCode  # Phải là 200
```

### Test 2: Test API với parameters mới

Python client đã được update để gửi:
- `preprocess='crop'` (thay vì 'full')
- `enhancer='none'` (tắt GFPGAN)
- `still_mode='true'`

Chạy lại video generator để test!

## 📊 So Sánh Settings

| Parameter | Old (Lỗi) | New (Fix) | Notes |
|-----------|-----------|-----------|-------|
| preprocess | full | **crop** | Crop nhanh & ổn định hơn |
| enhancer | gfpgan | **none** | Tắt để tránh crash |
| still_mode | - | **true** | Tối ưu cho ảnh tĩnh |
| timeout | 180s | 120s | Detect fail sớm hơn |
| retry | 0 | **1** | Retry 1 lần nếu fail |

## 🎯 Kết Quả Mong Đợi

### Trước Fix:
```
❌ Colab API failed: {"error":"Command ... exit status 1"}
⚠️ Avatar failed, using static scene
```

### Sau Fix:
```
✅ Video created successfully: assets/temp/avatar_scene_0.mp4
🎙️ Using AI avatar video for scene 0
```

## 🆘 Nếu Vẫn Lỗi

### Troubleshooting Steps:

1. **Check Colab logs** trong notebook cell:
   ```python
   # Thêm debug trong API endpoint
   print(f"Command: {' '.join(cmd)}")
   print(f"CWD: {os.getcwd()}")
   print(f"Files exist: img={os.path.exists(image_path)}, audio={os.path.exists(audio_path)}")
   ```

2. **Test SadTalker manually** trong Colab:
   ```python
   # New cell trong Colab
   !cd /content/SadTalker && python inference.py \
     --driven_audio /tmp/avatar_input/input.wav \
     --source_image /tmp/avatar_input/input.jpg \
     --result_dir /tmp/results \
     --still \
     --preprocess crop
   ```

3. **Check dependencies**:
   ```python
   # New cell
   !pip list | grep -E "torch|opencv|face"
   ```

4. **Fallback to D-ID** (paid but reliable):
   ```python
   # Trong main code
   avatar_backend="did"  # Thay vì "colab"
   ```
   Cần set: `$env:DID_API_KEY="your-api-key"`

## 💡 Best Practices

1. **Test Colab trước khi render nhiều videos**:
   - Render 1 video test first
   - Check logs carefully
   
2. **Keep Colab session alive**:
   - Colab timeout sau 12h idle
   - Chạy cell nào đó mỗi vài giờ
   
3. **Monitor GPU usage** trong Colab:
   ```python
   !nvidia-smi
   ```
   
4. **Prepare images properly**:
   - Face phải rõ, frontal
   - Resolution: 512x512 trở lên
   - Format: JPG/PNG

## 🎓 Advanced: Dùng Local SadTalker (No Colab)

Nếu có GPU local (NVIDIA):

```bash
# Clone SadTalker
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker

# Install
pip install -r requirements.txt

# Download checkpoints
bash scripts/download_models.sh

# Run local
python inference.py \
  --driven_audio input.wav \
  --source_image face.jpg \
  --result_dir ./results \
  --still --preprocess crop
```

Không cần Colab, chạy direct trên máy!

---

## 📞 Support

Nếu vẫn không fix được:
1. Check logs trong Colab notebook
2. Post error message đầy đủ
3. Check ngrok URL còn active không (ngrok timeout sau 8h)
