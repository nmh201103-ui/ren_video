"""Script Duration Optimizer - Compress/expand script to fit target duration"""
import os
from utils.logger import get_logger

logger = get_logger()


class ScriptDurationOptimizer:
    """Optimize script length to fit target video duration"""
    
    def __init__(self):
        # Conservative TTS speed to match real GTTS pacing (~96 WPM)
        self.words_per_second = 1.6
    
    def optimize(self, script: list, target_duration: int) -> list:
        """
        Optimize script to fit target duration
        Args:
            script: List of scene texts
            target_duration: Target video duration in seconds
        Returns:
            Optimized script that fits duration
        """
        if not script:
            return script
        
        # Calculate current estimated duration
        current_duration = self._estimate_duration(script)
        
        logger.info(f"📊 Script duration: {current_duration:.1f}s → Target: {target_duration}s")
        
        # If within 10% tolerance, keep as-is
        tolerance = target_duration * 0.1
        if abs(current_duration - target_duration) <= tolerance:
            logger.info("✅ Script duration acceptable, no optimization needed")
            return script
        
        # Enforce total words budget across scenes for tighter control
        max_total_words = max(1, int(target_duration * self.words_per_second))
        return self._fit_to_budget(script, max_total_words)
    
    def _estimate_duration(self, script: list) -> float:
        """Estimate total duration from script"""
        total_words = sum(len(text.split()) for text in script)
        return total_words / self.words_per_second
    
    def _fit_to_budget(self, script: list, max_total_words: int) -> list:
        """Fit script to a total words budget, allocating per scene."""
        # Weights: favor intro/conclusion slightly
        raw_counts = [len(s.split()) for s in script]
        weights = []
        for i, c in enumerate(raw_counts):
            if i == 0 or i == len(raw_counts) - 1:
                weights.append(c * 1.0)
            else:
                weights.append(c * 0.8)
        total_weight = max(1, sum(weights))
        
        # Per-scene target words derived from weights, with floor to avoid empties
        per_scene_targets = [max(6, int(max_total_words * (w / total_weight))) for w in weights]
        
        # Normalize to exactly match budget (adjust last scene)
        diff = max_total_words - sum(per_scene_targets)
        if per_scene_targets:
            per_scene_targets[-1] = max(6, per_scene_targets[-1] + diff)
        
        fitted = []
        for i, text in enumerate(script):
            words = text.split()
            target = per_scene_targets[i] if i < len(per_scene_targets) else len(words)
            if target < len(words):
                # Truncate and keep sentence-like ending
                truncated = ' '.join(words[:target]).rstrip(',;')
                if i not in [0, len(script) - 1]:
                    truncated += '.'
                fitted.append(truncated)
            else:
                fitted.append(text)
        
        final_duration = self._estimate_duration(fitted)
        logger.info(f"✅ Fitted total ~{final_duration:.1f}s with budget {max_total_words} words")
        return fitted
    
    def _expand(self, script: list, target_duration: int) -> list:
        """Expand script to fill longer duration by adding brief transitions."""
        logger.info(f"📝 Expanding script to {target_duration}s")
        max_total_words = int(target_duration * self.words_per_second)
        current_words = sum(len(s.split()) for s in script)
        if current_words >= max_total_words:
            return script
        transitions = [
            "Và đây là điều quan trọng...",
            "Điều này cho thấy...",
            "Thật thú vị...",
            "Ngoài ra...",
        ]
        expanded = []
        for i, text in enumerate(script):
            expanded.append(text)
            if 0 < i < len(script) - 1 and sum(len(s.split()) for s in expanded) < max_total_words:
                expanded.append(transitions[i % len(transitions)])
        return expanded
