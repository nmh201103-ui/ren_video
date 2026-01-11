# Affiliate Video Creator

## Quick Start

### 1. Setup Chrome với Remote Debugging

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


## AI Providers & Configuration

Set the following environment variables to enable services:

- `OPENAI_API_KEY` (required to use OpenAI LLM for script generation)
- `OPENAI_MODEL` (optional, e.g. `gpt-4`)
- `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` (optional, for ElevenLabs TTS)
- `DID_API_KEY` and `DID_API_SECRET` (optional, for D-ID avatar provider)
- `DID_API_URL` (optional, custom D-ID endpoint)
- `OLLAMA_MODEL` (optional, e.g. `gemma3:4b`) — if set, the renderer will attempt to use the local Ollama model via the `ollama` CLI. Alternatively set `LLM_PROVIDER=ollama` to prefer Ollama over OpenAI.
- `LLM_STYLE` (optional, e.g. `veo3` or `sora`) — if set, the script prompts will adopt a short, punchy TikTok/Shorts style (hooks, short sentences, CTA) suitable for veo3/sora-like videos.

Notes:
- Ensure `ollama` is installed and on your PATH (https://ollama.com) and the model (for example `gemma3:4b`) is downloaded locally (e.g. `ollama pull gemma3:4b`).
- Example usage:

```bash
# use installed ollama model with veo3 style
export OLLAMA_MODEL=gemma3:4b
export LLM_STYLE=veo3
python scripts/validate_render.py
```

If Ollama is not available, the renderer will fall back to simple heuristic script lines. For production use prefer OpenAI or a robust hosted LLM if available.

You can also control renderer features via constructor flags: `use_avatars`, `use_stock_videos`.

Run a quick validation run:

```bash
python scripts/validate_render.py
```

## Performance tips

- Preload remote assets to reduce render stalls (the renderer now downloads assets concurrently when possible).
- For large jobs, pin `Pillow<10` only if you depend on legacy behavior, or keep latest and ensure third-party libs are compatible.
- Increase `threads` argument in `write_videofile` for faster encoding if you have CPU resources.

