from video.render import SmartVideoRenderer


class DummyTTS:
    def tts_to_file(self, text, voice=None):
        return None  # simulate TTS provider failure


def test_renderer_handles_missing_tts(tmp_path):
    r = SmartVideoRenderer()
    r.tts = DummyTTS()
    out = tmp_path / "out.mp4"
    data = {"title": "Test", "description": "Mô tả sản phẩm xịn", "image_urls": []}
    ok = r.render(data, str(out))
    assert ok is True
    assert out.exists()
