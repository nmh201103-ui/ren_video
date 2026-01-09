import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class SceneSelector:
    """Map sentences to image/video assets using keywords and optional LLM scoring."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def _keyword_score(self, sentence: str, asset_desc: str) -> int:
        """Score asset by number of keyword matches with sentence."""
        words = set(re.findall(r"\w+", sentence.lower()))
        asset_words = set(re.findall(r"\w+", asset_desc.lower()))
        return len(words & asset_words)

    def match(self, assets: List[str], sentences: List[str]) -> List[Tuple[str, str]]:
        """Return (sentence, asset) pairs using keyword scoring + round-robin fallback."""
        if not assets:
            return [(s, None) for s in sentences]

        pairs = []
        used_assets = set()
        n_assets = len(assets)

        for i, s in enumerate(sentences):
            # Score all assets
            scored = sorted(
                [(self._keyword_score(s, a), a) for a in assets],
                key=lambda x: x[0],
                reverse=True
            )

            # Pick top unused asset if score >0
            selected = None
            for score, asset in scored:
                if score > 0 and asset not in used_assets:
                    selected = asset
                    break

            # fallback: top asset or round-robin
            if not selected:
                selected = scored[0][1] if scored else assets[i % n_assets]
                if selected in used_assets:
                    selected = assets[i % n_assets]

            pairs.append((s, selected))
            used_assets.add(selected)

            # allow reuse if all used
            if len(used_assets) >= n_assets:
                used_assets.clear()

        return pairs

    def llm_match(self, assets: List[str], sentences: List[str]) -> List[Tuple[str, str]]:
        """Use LLM to assign assets; fallback to heuristic if fails."""
        if not self.llm_client:
            logger.debug("No LLM client provided; using heuristic matching")
            return self.match(assets, sentences)

        try:
            prompt = "Map each sentence to the best asset index (0-based). Return JSON array.\n\n"
            prompt += "Sentences:\n" + "\n".join(f"{i}: {s}" for i, s in enumerate(sentences)) + "\n"
            prompt += "Assets:\n" + "\n".join(f"{i}: {a}" for i, a in enumerate(assets))

            resp = self.llm_client.create_match(prompt)
            import json
            idx_map = json.loads(resp)

            pairs = []
            for si, ai in enumerate(idx_map):
                asset = assets[int(ai)] if ai is not None and int(ai) < len(assets) else assets[si % len(assets)]
                pairs.append((sentences[si], asset))
            return pairs

        except Exception as e:
            logger.warning("LLM matching failed: %s", e)
            return self.match(assets, sentences)
