import os
os.environ['LLM_STYLE']='veo3'
from video.ai_providers import OllamaScriptGenerator

capt = {}

def fake_run(prompt, timeout=60):
    capt['prompt'] = prompt
    return 'Cực hấp dẫn! Mua ngay.'

if __name__ == '__main__':
    g = OllamaScriptGenerator(model='gemma3:4b')
    g._run_cli = fake_run
    s = g.generate('Test Title', 'Một sản phẩm thử', '199000')
    p = capt.get('prompt', '')
    print('PROMPT (repr):', repr(p))
    print('PROMPT (full):')
    print(p)

    print('SENTENCES:', s)
