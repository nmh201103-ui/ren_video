import os
from importlib import reload


def test_ollama_generates_style_prompt(monkeypatch):
    # Use Ollama provider and set style to veo3
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_STYLE", "veo3")
    from video.ai_providers import OllamaScriptGenerator
    # capture prompt passed to _run_cli
    captured = {}
    def fake_run_cli(prompt, timeout=60):
        captured['prompt'] = prompt
        return "Cực hấp dẫn! Mua ngay. Giá tốt."

    gen = OllamaScriptGenerator(model="gemma3:4b")
    gen._run_cli = fake_run_cli
    sentences = gen.generate("Test Title", "Test description", "199000")

    # The prompt should include style guidance
    assert ('hook' in captured['prompt'].lower() or 'gây chú ý' in captured['prompt'].lower())
    assert isinstance(sentences, list)
