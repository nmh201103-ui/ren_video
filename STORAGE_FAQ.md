# 💾 Storage & Performance FAQ

## ❓ Câu hỏi thường gặp

### 1. **Có phải tải video về không?**

**Với URL (YouTube/TikTok):**
- ✅ **CÓ** - Phải tải về máy trước khi xử lý
- 📥 Download vào: `assets/temp/downloads/`
- ⏱️ Thời gian: 30s - 5 phút tùy video size

**Với Local File:**
- ❌ **KHÔNG** - Đọc trực tiếp từ file có sẵn
- 🚀 Nhanh hơn nhiều!

---

### 2. **Làm nặng máy không?**

**Disk Space:**
```
Video gốc (tạm):    ~100-500MB (tự động XÓA sau khi xong)
Clips output:       ~20-50MB mỗi clip
```

**RAM Usage:**
```
Download:           ~50-100MB
Video processing:   ~500MB-1GB (moviepy load video vào RAM)
Peak usage:         ~1-2GB
```

**CPU Usage:**
```
Download:           10-20% (network bound)
Audio analysis:     30-50% (1-2 cores)
Video cutting:      60-80% (encoding - tất cả cores)
```

**Có lag không?**
- ⚠️ Khi đang cut video: **CÓ LAG** - CPU/RAM cao
- ✅ Chạy background thread → UI vẫn responsive
- 💡 Khuyến nghị: Đừng mở quá nhiều app khác

---

### 3. **Có tự động xóa không?**

**✅ MỚI UPDATE - TỰ ĐỘNG DỌN DẸP!**

**Video tạm (từ URL):**
```
✅ TỰ ĐỘNG XÓA ngay sau khi cut xong
📍 Location: assets/temp/downloads/video_id.mp4
🗑️ Cleanup: Tự động
💾 Tiết kiệm: 100-500MB mỗi video
```

**Clips output:**
```
❌ KHÔNG XÓA - đây là output bạn cần!
📍 Location: output/clips/clip_001.mp4
💾 Giữ lại để upload TikTok/YouTube
```

**Khi nào bị giữ lại?**
- ⚠️ Nếu app crash giữa chừng
- ⚠️ User tắt app force (Ctrl+C)
- 💡 Xóa thủ công: Delete thư mục `assets/temp/`

---

### 4. **Ước tính dung lượng**

**Video 5 phút (Full HD):**
```
Download:           ~200MB (temp - tự xóa)
5 clips @ 20s each: ~40MB total
Net storage:        40MB (chỉ clips)
```

**Video 30 phút (Full HD):**
```
Download:           ~1GB (temp - tự xóa)
10 clips @ 30s each: ~150MB total
Net storage:        150MB (chỉ clips)
```

**1 giờ video:**
```
Download:           ~2GB (temp - tự xóa)
10 clips @ 30s:     ~200MB
Net storage:        200MB
```

---

### 5. **Làm thế nào để tối ưu?**

**✅ Dùng Local File nếu có thể:**
```
1. Download video 1 lần bằng IDM/JDownloader
2. Lưu vào: E:\videos\movie.mp4
3. App → Local File → Browse
4. Không tốn thời gian download lại
```

**✅ Xóa clips cũ định kỳ:**
```powershell
# Manual cleanup
Remove-Item output\clips\* -Force
```

**✅ Tăng RAM nếu xử lý video dài:**
- Video < 10 phút: 4GB RAM OK
- Video 10-30 phút: 8GB RAM khuyên dùng
- Video > 30 phút: 16GB RAM tốt nhất

---

## 🔄 Workflow Chi Tiết

### **URL Method:**
```
1. Download video          [200MB temp]
   ↓
2. Load vào RAM           [500MB RAM]
   ↓
3. Analyze audio          [CPU 50%]
   ↓
4. Cut 5 clips            [40MB output]
   ↓
5. 🗑️ XÓA video temp     [Tiết kiệm 200MB!]
   ↓
6. Chỉ còn clips         [40MB net]
```

### **Local File Method:**
```
1. Read file có sẵn      [0MB download]
   ↓
2. Load vào RAM          [500MB RAM]
   ↓
3. Analyze audio         [CPU 50%]
   ↓
4. Cut 5 clips           [40MB output]
   ↓
5. File gốc giữ nguyên  [Không động chạm]
```

---

## 📊 So Sánh

| Tiêu chí | URL Method | Local File |
|----------|------------|------------|
| Download time | 1-5 phút | 0s |
| Temp storage | 0MB (auto xóa) | 0MB |
| Output storage | 40-200MB | 40-200MB |
| Total time | 3-10 phút | 2-5 phút |
| RAM usage | 1-2GB | 1-2GB |
| CPU usage | 60-80% | 60-80% |

---

## 🛠️ Manual Cleanup

**Xóa toàn bộ temp files:**
```powershell
# PowerShell
Remove-Item assets\temp\downloads\* -Force
```

**Xóa clips cũ:**
```powershell
# Xóa tất cả
Remove-Item output\clips\* -Force

# Xóa clips > 7 ngày
Get-ChildItem output\clips -Recurse | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | 
  Remove-Item -Force
```

**Check disk usage:**
```powershell
# Xem dung lượng temp
Get-ChildItem assets\temp -Recurse | 
  Measure-Object -Property Length -Sum | 
  Select-Object @{Name="Size(MB)";Expression={$_.Sum/1MB}}

# Xem dung lượng clips
Get-ChildItem output\clips -Recurse | 
  Measure-Object -Property Length -Sum | 
  Select-Object @{Name="Size(MB)";Expression={$_.Sum/1MB}}
```

---

## 🎯 Khuyến Nghị

### **Máy yếu (4GB RAM, CPU i3):**
- ✅ Dùng Local File
- ✅ Cắt video < 10 phút
- ✅ Tối đa 5 clips
- ⚠️ Tránh chạy nhiều app cùng lúc

### **Máy trung bình (8GB RAM, CPU i5):**
- ✅ URL hoặc Local File đều OK
- ✅ Video < 30 phút
- ✅ 5-10 clips
- ✅ Có thể mở Chrome cùng lúc

### **Máy mạnh (16GB+ RAM, CPU i7+):**
- ✅ URL method - thoải mái
- ✅ Video dài OK (1-2 giờ)
- ✅ 10+ clips
- ✅ Multitask không vấn đề

---

## 🔔 Lưu Ý

### **Tự động xóa khi:**
- ✅ Cut xong thành công
- ✅ Xảy ra lỗi (cleanup on error)
- ✅ App đóng bình thường

### **KHÔNG xóa khi:**
- ⚠️ App crash (Ctrl+C force)
- ⚠️ Mất điện đột ngột
- ⚠️ Kill process bằng Task Manager

### **Trong trường hợp đó:**
→ Xóa thủ công folder `assets/temp/downloads/`

---

## 📞 Support

**App chạy chậm?**
→ Giảm số clips, dùng Local File

**Hết dung lượng?**
→ Xóa clips cũ trong `output/clips/`

**Temp files không tự xóa?**
→ Update code mới nhất (đã fix!)

---

**Happy Clipping! 🎬✨**
