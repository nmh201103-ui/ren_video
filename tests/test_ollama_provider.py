import os
from importlib import reload


def test_ollama_selection(monkeypatch):
    # ensure environment selection picks OllamaScriptGenerator
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    # reload module to pick up env-based defaults if it was imported earlier
    from video import render
    reload(render)
    r = render.SmartVideoRenderer()
    # class should be available and selected
    cls_name = r.script_generator.__class__.__name__
    assert cls_name in ("OllamaScriptGenerator",), f"Unexpected script generator: {cls_name}"
    assert hasattr(r.script_generator, "create_match")
