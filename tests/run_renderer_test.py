from tests.test_renderer_audio_fallback import test_renderer_handles_missing_tts
from pathlib import Path
p = Path('output') / 'tmp_test_out'
try:
    test_renderer_handles_missing_tts(p)
    print('test passed')
except Exception as e:
    print('test failed:', e)
