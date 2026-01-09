import os
os.environ['LLM_PROVIDER'] = 'ollama'
from video.render import SmartVideoRenderer
r = SmartVideoRenderer()
print('Script generator class:', r.script_generator.__class__.__name__)
print('SceneSelector llm_client set:', r.scene_selector.llm_client is not None)
