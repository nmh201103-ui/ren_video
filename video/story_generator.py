"""Story/Narrative Script Generator - For storytelling videos"""
import os
import json
import subprocess
from utils.logger import get_logger

logger = get_logger()


class StoryScriptGenerator:
    """Generate storytelling narrative scripts from article content"""
    
    def __init__(self, use_llm=None):
        """
        Args:
            use_llm: "openai", "ollama", or None for heuristic
        """
        # Auto-detect LLM based on environment
        if use_llm is None:
            if os.getenv("OPENAI_API_KEY"):
                self.use_llm = "openai"
            elif self._has_ollama():
                self.use_llm = "ollama"
            else:
                self.use_llm = None
        else:
            self.use_llm = use_llm
        
        if self.use_llm == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("🤖 Story generator using OpenAI")
            except ImportError:
                self.use_llm = None
                logger.warning("OpenAI not available, using heuristic")
        elif self.use_llm == "ollama":
            logger.info("🤖 Story generator using Ollama")
        else:
            logger.info("📝 Story generator using heuristic")
    
    def _has_ollama(self):
        """Check if Ollama is installed"""
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, check=True, timeout=5)
            return True
        except:
            return False
    
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
        
        # Use LLM if available for better narrative
        if self.use_llm == "openai":
            try:
                script = self._generate_with_openai(title, description, content, max_scenes)
                if script:
                    logger.info(f"✅ Generated {len(script)} AI-powered scenes (OpenAI)")
                    return script
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}, falling back to heuristic")
        elif self.use_llm == "ollama":
            try:
                script = self._generate_with_ollama(title, description, content, max_scenes)
                if script:
                    logger.info(f"✅ Generated {len(script)} AI-powered scenes (Ollama)")
                    return script
            except Exception as e:
                logger.warning(f"Ollama failed: {e}, falling back to heuristic")
        
        # Fallback: Heuristic approach
        return self._generate_heuristic(title, description, content, max_scenes)
    
    def _generate_with_openai(self, title: str, description: str, content: str, max_scenes: int) -> list:
        """Use OpenAI to create engaging narrative"""
        # Summarize for OpenAI too (though it has larger context)
        summarized_content = self._summarize_content(content, max_words=1200)
        
        prompt = f"""Tạo kịch bản video kể chuyện từ bài viết sau (THUẦN TÚY KỂ CHUYỆN, KHÔNG QUẢNG CÁO):

Tiêu đề: {title}
Mô tả: {description}
Nội dung chính: {summarized_content}

Yêu cầu:
1. Tạo {max_scenes} đoạn kịch bản (mỗi đoạn ~20-30 giây khi đọc):
   - Đoạn 1: Hook/Mở đầu thu hút
   - Đoạn 2-{max_scenes-2}: Nội dung chính (kể chuyện tự nhiên)
   - Đoạn {max_scenes-1}: Tóm tắt điểm chính + lời khuyên áp dụng
   - Đoạn {max_scenes}: Kết luận truyền cảm hứng (cảm ơn + lời khuyên sâu sắc)

2. Giọng điệu: Tự nhiên, gần gũi, như người kể chuyện cho bạn nghe
3. KHÔNG quảng cáo sản phẩm, KHÔNG call-to-action
4. Tập trung vào nội dung câu chuyện/bài học + cách áp dụng vào cuộc sống

Trả về JSON array gồm {max_scenes} đoạn text tiếng Việt. Chỉ trả JSON, không giải thích."""

        response = self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        content_text = response.choices[0].message.content
        content_text = content_text.replace("```json", "").replace("```", "").strip()
        return json.loads(content_text)
    
    def _generate_with_ollama(self, title: str, description: str, content: str, max_scenes: int) -> list:
        """Use Ollama to create engaging narrative"""
        # Smart content summarization to fit Ollama context
        summarized_content = self._summarize_content(content, max_words=800)
        
        prompt = f"""Tạo kịch bản video storytelling từ bài viết (KHÔNG QUẢNG CÁO):

Tiêu đề: {title}
Nội dung chính: {summarized_content}

Tạo {max_scenes} đoạn kịch bản (mỗi đoạn ~20 giây):
1. Hook/Mở đầu thu hút
2-{max_scenes-2}. Kể chuyện nội dung (tự nhiên, gần gũi)
{max_scenes-1}. Tóm tắt + lời khuyên áp dụng
{max_scenes}. Kết luận truyền cảm hứng (cảm ơn + insight sâu sắc)

Chỉ kể chuyện/chia sẻ kiến thức, KHÔNG quảng cáo, KHÔNG bán hàng.
Giọng điệu tự nhiên, như người kể chuyện.

Trả về JSON array [{max_scenes} đoạn text tiếng Việt]. CHỈ JSON, không thêm text."""

        try:
            model = os.getenv("OLLAMA_MODEL", "gemma2:2b")
            timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))  # Increase timeout for longer content
            
            logger.info(f"🤖 Ollama: Using model {model}, timeout {timeout}s")
            
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout
            )
            
            output = result.stdout.strip()
            logger.info(f"📝 Ollama raw output length: {len(output)} chars")
            
            # Clean up markdown and extra text
            output = output.replace("```json", "").replace("```", "").strip()
            
            # Find JSON array in output (sometimes Ollama adds explanation)
            import re
            json_match = re.search(r'\[.*\]', output, re.DOTALL)
            if json_match:
                output = json_match.group(0)
            
            parsed = json.loads(output)
            
            # Validate it's a list
            if not isinstance(parsed, list):
                raise ValueError("Output is not a list")
            
            return parsed
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Ollama timeout after {timeout}s - content too long or model busy")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ollama JSON parse error: {e}")
            logger.debug(f"Raw output: {output[:500]}")
            return None
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            return None
    
    def _summarize_content(self, content: str, max_words: int = 800) -> str:
        """
        Smart content summarization to fit LLM context limits
        Instead of truncating, extract key paragraphs
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # If content is short enough, return as-is
        current_words = len(content.split())
        if current_words <= max_words:
            return content
        
        # Extract key paragraphs (first, middle, last)
        if len(paragraphs) <= 3:
            summary = '\n\n'.join(paragraphs)
        else:
            # Take intro, some middle parts, and conclusion
            key_paragraphs = []
            key_paragraphs.append(paragraphs[0])  # Intro
            
            # Sample middle paragraphs
            middle_count = min(len(paragraphs) - 2, 3)
            step = (len(paragraphs) - 2) // middle_count if middle_count > 0 else 1
            for i in range(1, len(paragraphs) - 1, step):
                key_paragraphs.append(paragraphs[i])
                if len(key_paragraphs) >= 5:  # Limit total paragraphs
                    break
            
            key_paragraphs.append(paragraphs[-1])  # Conclusion
            summary = '\n\n'.join(key_paragraphs)
        
        # If still too long, truncate words
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + '...'
        
        logger.info(f"📊 Content summarized: {current_words} → {len(summary.split())} words")
        return summary
    
    def _generate_heuristic(self, title: str, description: str, content: str, max_scenes: int) -> list:
        """Fallback heuristic method"""
        
    def _generate_heuristic(self, title: str, description: str, content: str, max_scenes: int) -> list:
        """Fallback heuristic method"""
        # Split content into logical chunks
        chunks = self._split_content(content, max_scenes - 3)  # Leave room for intro + summary + conclusion
        
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
        
        # Scene N-1: Summary/Key Takeaways
        if len(chunks) > 0:
            summary = self._generate_summary(chunks, title)
            if summary:
                script.append(summary)
        
        # Final scene: Conclusion with advice
        if len(script) > 1:
            conclusion = self._generate_conclusion(title, content)
            script.append(conclusion)
        
        logger.info(f"✅ Generated {len(script)} heuristic scenes")
        return script[:max_scenes]
    
    def _generate_summary(self, chunks: list, title: str) -> str:
        """Generate summary of key points"""
        if not chunks:
            return ""
        
        # Extract key phrases from chunks
        key_points = []
        for chunk in chunks[:3]:  # First 3 chunks
            words = chunk.split()
            # Get first meaningful sentence
            if len(words) > 0:
                key_points.append(words[0])
        
        if key_points:
            return f"Tóm lại, những điểm chính của '{title}' là: {', '.join(set(key_points[:3]))}. Đó là những bài học quý giá mà chúng ta có thể áp dụng vào cuộc sống hàng ngày."
        
        return "Những điểm chính từ bài viết này sẽ giúp bạn có cái nhìn sâu sắc hơn về vấn đề."
    
    def _generate_conclusion(self, title: str, content: str) -> str:
        """Generate inspiring conclusion with advice"""
        # Analyze content sentiment/type
        content_lower = content.lower()
        
        # Different conclusions based on content
        if any(word in content_lower for word in ['học', 'bài học', 'kinh nghiệm']):
            return f"Hy vọng qua '{title}', bạn đã học được những điều bổ ích. Hãy áp dụng những kiến thức này vào cuộc sống để thấy sự thay đổi tích cực. Cảm ơn vì đã lắng nghe và chúc bạn thành công!"
        elif any(word in content_lower for word in ['câu chuyện', 'chuyện', 'sự kiện']):
            return f"Câu chuyện này cho ta thấy rằng mỗi trải nghiệm đều có giá trị riêng. Hãy suy ngẫm và tìm cách ứng dụng vào tình huống của chính mình. Cảm ơn các bạn đã theo dõi!"
        elif any(word in content_lower for word in ['lợi ích', 'tác dụng', 'cách']):
            return f"Những lợi ích và cách tiếp cận từ '{title}' chắc chắn sẽ giúp ích cho bạn. Hãy thử áp dụng và chia sẻ kết quả với mọi người. Cảm ơn đã xem và chúc bạn may mắn!"
        else:
            return f"Bài viết '{title}' đã mang đến nhiều thông tin bổ ích. Hãy dành thời gian suy ngẫm và tìm cách áp dụng vào cuộc sống của bạn. Cảm ơn vì đã theo dõi chúng tôi!"
    
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
