import os
from importlib import reload


def test_autoswitch_to_ollama(monkeypatch, tmp_path):
    # Simulate no OpenAI available by ensuring OpenAI env is not set and monkeypatching OpenAIScriptGenerator to have no client
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('LLM_PROVIDER', '')

    # Fake that ollama exists on PATH
    monkeypatch.setenv('PATH', str(tmp_path))
    # create a fake 'ollama' executable file in PATH
    (tmp_path / 'ollama').write_text('#!/bin/sh\n')

    # reload modules to pick up environment
    from video import render
    reload(render)
    r = render.SmartVideoRenderer()
    assert r.script_generator.__class__.__name__ == 'OllamaScriptGenerator'
