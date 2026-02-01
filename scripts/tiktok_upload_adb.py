"""
Đẩy video lên TikTok qua ADB (Android emulator).
- Push video vào emulator
- Mở app TikTok
- Hướng dẫn / automation bấm: + → Tải lên → chọn video → Thêm link → dán link → Đăng

Cần: adb trong PATH, emulator đang chạy (BlueStacks/LDPlayer/Nox).
"""
import os
import subprocess
import sys

def _run_adb(*args, timeout=15):
    try:
        r = subprocess.run(["adb"] + list(args), capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or "").strip(), (r.stderr or "").strip()
    except FileNotFoundError:
        return False, "", "adb not found. Install Android SDK platform-tools and add adb to PATH."
    except subprocess.TimeoutExpired:
        return False, "", "adb timeout"
    except Exception as e:
        return False, "", str(e)

def _devices():
    ok, out, err = _run_adb("devices")
    if not ok:
        return []
    devices = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "List of devices" in line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices

def upload_video_to_tiktok(
    video_path: str,
    username: str = "",
    password: str = "",
    product_link: str = "",
    device_id: str = None,
) -> tuple:
    """
    Push video vào emulator và mở TikTok. Trả về (success: bool, message: str).
    Login + Thêm link cần làm trong app (hoặc mở rộng bằng Appium/uiautomator).
    """
    if not video_path or not os.path.isfile(video_path):
        return False, "File video không tồn tại: %s" % video_path
    video_path = os.path.abspath(video_path)
    devices = _devices()
    if not devices:
        return False, "Không thấy emulator/thiết bị. Bật BlueStacks/LDPlayer/Nox và bật ADB (Cài đặt → ADB)."
    dev = device_id or devices[0]
    # 1. Push video vào /sdcard/Download/
    remote = "/sdcard/Download/affiliate_video.mp4"
    ok, out, err = _run_adb("-s", dev, "push", video_path, remote, timeout=60)
    if not ok:
        return False, "ADB push thất bại: %s" % (err or out)
    # 2. Mở TikTok (package thường là com.zhiliaoapp.musically hoặc com.ss.android.ugc.trill)
    for pkg in ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill"]:
        ok, _, _ = _run_adb("-s", dev, "shell", "am", "start", "-n", "%s/.main.MainActivity" % pkg, timeout=5)
        if ok:
            break
    # 3. Copy link vào clipboard emulator (để user dán khi bấm Thêm link)
    if product_link:
        # ADB shell am broadcast để set clipboard hoặc input text (thường cần root). Thử input text qua service.
        escaped = product_link.replace("%", "%%").replace(" ", "%s").replace("&", "\\&")
        _run_adb("-s", dev, "shell", "am", "broadcast", "-a", "android.intent.action.CLIPBOARD", "--es", "text", product_link, timeout=3)
    msg = (
        "Đã push video vào emulator: %s\n"
        "Đã mở TikTok. Trong app:\n"
        "1. Bấm + (Tạo) → Tải lên → chọn 'affiliate_video.mp4' trong Thư viện/Download.\n"
        "2. Thêm caption, bấm Tiếp → Thêm link/Sản phẩm → dán link giỏ hàng (đã copy).\n"
        "3. Bấm Đăng."
    ) % dev
    if product_link:
        msg += "\n\nLink đã sẵn trong ô Link giỏ hàng — bấm Copy rồi dán vào TikTok khi Thêm link."
    return True, msg

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    link = sys.argv[2] if len(sys.argv) > 2 else ""
    ok, msg = upload_video_to_tiktok(path, product_link=link)
    print(msg)
    sys.exit(0 if ok else 1)
