from video.ai_providers import MotionPlanner


class DummyClip:
    def __init__(self):
        self._pos = None
    def set_position(self, fn):
        self._pos = fn
        return self
    def resize(self, fn):
        return self


def test_apply_preset_returns_clip():
    m = MotionPlanner()
    c = DummyClip()
    out = m.apply_preset(c, 0, 3.0)
    assert isinstance(out, DummyClip)


def test_spline_motion_or_fallback():
    m = MotionPlanner()
    c = DummyClip()
    # If scipy not installed, this should fallback to preset
    out = m.spline_motion(c, None, 3.0)
    assert out is not None
