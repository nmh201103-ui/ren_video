from video.ai_providers import GTTSProvider, ElevenLabsTTSProvider, DIDAvatarProvider


def test_gtts_provider_creates_file():
    p = GTTSProvider()
    f = p.tts_to_file("Xin chào, đây là kiểm tra.")
    assert f is not None


def test_elevenlabs_provider_unconfigured_returns_none():
    p = ElevenLabsTTSProvider(api_key=None)
    assert p.tts_to_file("test") is None


def test_did_provider_unconfigured_returns_none():
    p = DIDAvatarProvider(api_key=None, api_secret=None)
    assert p.create_avatar_clip("test") is None
