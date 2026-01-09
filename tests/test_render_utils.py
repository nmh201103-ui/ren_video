from video.render import SmartVideoRenderer


def test_preload_assets_handles_non_http():
    r = SmartVideoRenderer()
    assert r._preload_assets(["img1.jpg", "http://example.invalid/img.png"]) is True
