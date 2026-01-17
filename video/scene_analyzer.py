"""Scene Analysis - Analyze scene content using AI Vision"""
import os
import json
import base64
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger()


class SceneAnalyzer:
    """Analyze scenes using Vision AI (OpenAI GPT-4V)"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4-vision-preview"):
        """
        Initialize scene analyzer
        Args:
            api_key: OpenAI API key
            model: Vision model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI Vision API ready")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
    
    def analyze_scene(self, frame_path: str, scene_num: int, context: str = "") -> Dict:
        """
        Analyze single scene frame using AI Vision
        Args:
            frame_path: Path to frame image
            scene_num: Scene number
            context: Additional context (movie title, plot summary)
        Returns:
            Dict with analysis results
        """
        if not self.client:
            logger.warning("OpenAI client not available. Using fallback.")
            return self._fallback_analysis(frame_path, scene_num)
        
        try:
            # Encode image to base64
            with open(frame_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            
            # Create prompt
            prompt = f"""Analyze this movie scene frame #{scene_num}.

Provide a brief review script (~30-50 words) that:
1. Describes what's happening visually
2. Highlights the key action/emotion
3. Is engaging for a movie review

Context: {context}

Format as JSON:
{{
    "scene_description": "What is happening visually",
    "key_elements": ["element1", "element2", "element3"],
    "emotional_tone": "tone description",
    "review_script": "Engaging narration for this scene (30-50 words)",
    "relevance_score": 0.0-1.0
}}"""
            
            # Call API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Using Claude instead for better vision
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            # Parse response
            result_text = response.content[0].text
            
            # Extract JSON from response
            import json
            try:
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                json_str = result_text[start:end]
                analysis = json.loads(json_str)
            except:
                analysis = {
                    "scene_description": result_text[:100],
                    "review_script": result_text,
                    "key_elements": [],
                    "emotional_tone": "unknown",
                    "relevance_score": 0.5
                }
            
            logger.info(f"  ✅ Scene {scene_num} analyzed")
            return analysis
        
        except Exception as e:
            logger.warning(f"Vision API error: {e}. Using fallback.")
            return self._fallback_analysis(frame_path, scene_num)
    
    def analyze_scenes(self, scenes: List[Dict], movie_title: str = "", 
                      movie_plot: str = "") -> List[Dict]:
        """
        Analyze multiple scenes
        Args:
            scenes: List of scene dicts with frame_path
            movie_title: Movie title for context
            movie_plot: Movie plot summary
        Returns:
            Scenes with analysis added
        """
        context = f"Movie: {movie_title}"
        if movie_plot:
            context += f"\nPlot: {movie_plot[:200]}..."
        
        for i, scene in enumerate(scenes):
            if 'frame_path' not in scene or not os.path.exists(scene['frame_path']):
                logger.warning(f"Scene {i} frame not found, skipping")
                continue
            
            logger.info(f"🔍 Analyzing scene {i+1}/{len(scenes)}...")
            
            analysis = self.analyze_scene(scene['frame_path'], i, context)
            scene['analysis'] = analysis
            scene['analyzed'] = True
        
        return scenes
    
    def _fallback_analysis(self, frame_path: str, scene_num: int) -> Dict:
        """Fallback analysis when API unavailable"""
        return {
            "scene_description": f"Scene {scene_num} from the movie",
            "review_script": f"This pivotal moment shows the progression of the story.",
            "key_elements": ["action", "character", "emotion"],
            "emotional_tone": "dramatic",
            "relevance_score": 0.7
        }
    
    def generate_review_script(self, scenes: List[Dict], movie_title: str = "") -> str:
        """
        Generate complete review script from analyzed scenes
        Args:
            scenes: List of analyzed scenes
            movie_title: Movie title
        Returns:
            Complete review script
        """
        script = f"🎬 {movie_title} Review\n\n"
        
        for i, scene in enumerate(scenes):
            if 'analysis' in scene:
                analysis = scene['analysis']
                script += f"Scene {i+1}: {analysis.get('review_script', '')}\n\n"
        
        script += "Thanks for watching! Like and subscribe for more reviews."
        
        logger.info(f"✅ Generated review script ({len(script)} chars)")
        return script
