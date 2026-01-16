"""Story/Narrative Script Generator - For storytelling videos"""
from utils.logger import get_logger

logger = get_logger()


class StoryScriptGenerator:
    """Generate storytelling narrative scripts from article content"""
    
    def __init__(self):
        pass
    
    def generate(self, title: str, description: str, content: str, max_scenes: int = None) -> list:
        """
        Generate storytelling script from article content
        Returns pure narrative without product mentions or CTAs
        
        Args:
            title: Article title
            description: Article description/excerpt
            content: Full article text
            max_scenes: Maximum number of scenes (auto-calculated if None)
        
        Returns:
            list of scene texts (each ~15-30s when spoken, PURE NARRATIVE)
        """
        
        logger.info(f"📖 Generating story script: {title}")
        
        # Auto-calculate scenes based on content length if not specified
        if max_scenes is None:
            word_count = len(content.split())
            # ~20-30 seconds per scene, ~150 words per scene
            max_scenes = max(8, min(20, word_count // 150))
            logger.info(f"📊 Auto-calculated {max_scenes} scenes from {word_count} words")
        
        # Split content into logical chunks
        chunks = self._split_content(content, max_scenes)
        
        # Create pure narrative arc (no CTA, no product pitch)
        script = []
        
        # Scene 1: Hook/Introduction (just intro, no CTA)
        intro = f"{title}\n\n{description}"
        script.append(intro)
        
        # Scenes 2-N: Main content (pure storytelling)
        for i, chunk in enumerate(chunks, 1):
            scene_text = self._chunk_to_narration(chunk, i, len(chunks))
            if scene_text:
                script.append(scene_text)
        
        # Final scene: Conclusion (just wrapping up, no CTA or pricing)
        if len(script) > 1:
            conclusion = "Cảm ơn bạn đã theo dõi. Chúc bạn có một ngày tuyệt vời!"
            script.append(conclusion)
        
        logger.info(f"✅ Generated {len(script)} pure narrative scenes")
        return script[:max_scenes]
    
    def _split_content(self, content: str, max_chunks: int) -> list:
        """Split content into logical paragraphs/chunks"""
        # Split by double newline (paragraphs)
        paragraphs = content.split('\n\n')
        
        # Remove empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # If too many, group them
        if len(paragraphs) > max_chunks:
            return self._group_paragraphs(paragraphs, max_chunks)
        
        return paragraphs
    
    def _group_paragraphs(self, paragraphs: list, target_groups: int) -> list:
        """Group paragraphs into target number of chunks"""
        if not paragraphs or target_groups < 1:
            return paragraphs
        
        # Calculate items per group
        items_per_group = len(paragraphs) // target_groups
        if items_per_group < 1:
            items_per_group = 1
        
        groups = []
        current_group = []
        
        for para in paragraphs:
            current_group.append(para)
            if len(current_group) >= items_per_group:
                groups.append('\n\n'.join(current_group))
                current_group = []
        
        # Add remaining
        if current_group:
            if groups:
                groups[-1] += '\n\n' + '\n\n'.join(current_group)
            else:
                groups.append('\n\n'.join(current_group))
        
        return groups[:target_groups]
    
    def _chunk_to_narration(self, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Convert a content chunk into a natural narration"""
        # Remove extra spaces
        chunk = ' '.join(chunk.split())
        
        # Limit to ~100-150 words per scene (~20-30 seconds when spoken)
        words = chunk.split()
        if len(words) > 150:
            words = words[:150]
        
        narration = ' '.join(words)
        
        # Add transition if not first/last
        if chunk_num > 1 and chunk_num < total_chunks:
            narration = f"Tiếp theo, {narration}"
        elif chunk_num > 1:
            narration = f"Cuối cùng, {narration}"
        
        return narration
