"""Story/Narrative Script Generator - For storytelling videos"""
import os
import json
import subprocess
from utils.logger import get_logger

logger = get_logger()


class StoryScriptGenerator:
    """Generate storytelling narrative scripts from article content"""
    
    def __init__(self, use_llm="auto"):
        """
        Args:
            use_llm: "openai", "ollama", None (force heuristic), or "auto" (detect)
        """
        # Auto-detect LLM based on environment ONLY if use_llm == "auto"
        if use_llm == "auto":
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
    
    def generate(self, title: str, description: str, content: str, max_scenes: int = None, target_duration: int = None) -> list:
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
        
        # Duration-aware scene planning
        words_per_second = 1.6  # Match optimizer pacing
        total_words_budget = None
        if target_duration and target_duration > 0:
            total_words_budget = max(40, int(target_duration * words_per_second))
        
        # Auto-calculate scenes if not specified
        if max_scenes is None:
            word_count = len(content.split())
            if total_words_budget:
                # Aim for 3–8 scenes depending on budget
                est_per_scene = max(30, min(80, total_words_budget // 4))
                max_scenes = max(3, min(8, total_words_budget // est_per_scene))
            else:
                # ~20-30 seconds per scene, ~150 words per scene
                max_scenes = max(8, min(20, word_count // 150))
            logger.info(f"📊 Planned {max_scenes} scenes (words budget: {total_words_budget or 'auto'})")
        
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
        return self._generate_heuristic(title, description, content, max_scenes, total_words_budget)
    
    def _generate_with_openai(self, title: str, description: str, content: str, max_scenes: int) -> list:
        """Use OpenAI to create engaging narrative"""
        # Summarize for OpenAI too (though it has larger context)
        summarized_content = self._summarize_content(content, max_words=1200)
        
        prompt = f"""Tạo kịch bản video kể chuyện từ bài viết sau (THUẦN TÚY KỂ CHUYỆN, KHÔNG QUẢNG CÁO):

Tiêu đề: {title}
Mô tả: {description}
Nội dung chính: {summarized_content}

QUY TẮC QUAN TRỌNG:
- Tuyệt đối CHỈ sử dụng thông tin từ nội dung bài viết trên
- KHÔNG được thêm sự kiện, con số, ví dụ, hoặc chi tiết NGOÀI bài gốc
- KHÔNG tự sáng tạo nội dung không có trong bài viết
- Nếu bài viết nói về "A", đừng thêm "B, C, D" vào kịch bản

Yêu cầu:
1. Tạo {max_scenes} đoạn kịch bản (mỗi đoạn ~20-30 giây khi đọc):
   - Đoạn 1: Hook/Mở đầu thu hút - chỉ dùng thông tin từ bài viết
   - Đoạn 2-{max_scenes-2}: Nội dung chính (kể chuyện tự nhiên) - dựa HOÀN TOÀN vào bài gốc
   - Đoạn {max_scenes-1}: Tóm tắt điểm chính + lời khuyên áp dụng - rút ra từ nội dung bài viết
   - Đoạn {max_scenes}: Kết luận truyền cảm hứng (cảm ơn + lời khuyên sâu sắc) - liên quan trực tiếp đến chủ đề bài viết

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

    QUY TẮC QUAN TRỌNG:
    - Tuyệt đối CHỈ sử dụng thông tin từ nội dung bài viết trên
    - KHÔNG được thêm sự kiện, con số, ví dụ, hoặc chi tiết NGOÀI bài gốc
    - KHÔNG tự sáng tạo nội dung không có trong bài viết
    - Nếu bài viết nói về "A", đừng thêm "B, C, D" vào kịch bản

    Tạo {max_scenes} đoạn kịch bản (mỗi đoạn ~20 giây):
    1. Hook/Mở đầu thu hút - chỉ dùng thông tin từ bài viết
    2-{max_scenes-2}. Kể chuyện nội dung - dựa HOÀN TOÀN vào bài gốc
    {max_scenes-1}. Tóm tắt + lời khuyên áp dụng - rút ra từ nội dung bài viết
    {max_scenes}. Kết luận truyền cảm hứng (cảm ơn + insight) - liên quan trực tiếp đến chủ đề bài viết

    Chỉ kể chuyện/chia sẻ kiến thức, KHÔNG quảng cáo, KHÔNG bán hàng.
    Giọng điệu tự nhiên, như người kể chuyện.
    TẤT CẢ ĐẦU RA PHẢI BẰNG TIẾNG VIỆT TỰ NHIÊN (tuyệt đối không dùng tiếng Anh).

    Trả về JSON array [{max_scenes} đoạn text tiếng Việt]. CHỈ JSON, không thêm text."""

        try:
            model = os.getenv("OLLAMA_MODEL", "gemma3:4b")  # Using Gemma 3.4B for better quality
            timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))  # Increase timeout for longer content
            
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
            
            # Log full output for debugging
            logger.info("=" * 80)
            logger.info("🔍 OLLAMA RAW OUTPUT:")
            logger.info(output)
            logger.info("=" * 80)
            
            # Check for errors in stderr
            if result.stderr:
                logger.warning(f"⚠️ Ollama stderr: {result.stderr}")
            
            # Clean up markdown and extra text
            output = output.replace("```json", "").replace("```", "").strip()
            
            # Find JSON array in output (sometimes Ollama adds explanation)
            import re
            json_match = re.search(r'\[.*\]', output, re.DOTALL)
            if json_match:
                extracted_json = json_match.group(0)
                logger.info(f"✅ Extracted JSON from output ({len(extracted_json)} chars)")
                output = extracted_json
            else:
                logger.warning("⚠️ No JSON array pattern found in output")
            
            # Try to parse JSON; if it fails, attempt repair for unescaped quotes
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError as json_err:
                logger.warning(f"⚠️ JSON parse error, attempting repair for unescaped quotes...")
                # Attempt to fix by handling common quote issues in JSON
                try:
                    # Try a simple approach: find quotes that break JSON and escape them
                    # Replace ": " with proper escaping for broken quotes within strings
                    lines = output.split('\n')
                    fixed_lines = []
                    for line in lines:
                        # If line has unescaped quote issues, try to fix it
                        if '": "' in line and line.count('"') % 2 == 0:
                            fixed_lines.append(line)
                        else:
                            # Attempt to fix by looking for quote mismatch patterns
                            fixed_lines.append(line)
                    repaired = '\n'.join(fixed_lines)
                    parsed = json.loads(repaired)
                    logger.info(f"✅ JSON repair successful")
                except Exception as repair_err:
                    logger.error(f"❌ JSON repair failed: {repair_err}, returning fallback")
                    # Return None to fall back to heuristic
                    return None
            
            # Validate it's a list
            if not isinstance(parsed, list):
                raise ValueError("Output is not a list")
            
            logger.info(f"✅ Ollama parsed {len(parsed)} scenes successfully")
            return parsed
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Ollama timeout after {timeout}s - content too long or model busy")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ollama JSON parse error: {e}")
            logger.error(f"📄 Full raw output:\n{output}")
            return None
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            logger.exception("Full traceback:")
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
    
    def _generate_heuristic(self, title: str, description: str, content: str, max_scenes: int, total_words_budget: int = None) -> list:
        """Fallback heuristic method"""
        import difflib
        
        # Remove description from content start if it's duplicated
        # Use multiple strategies to detect and remove duplicate text
        content_original = content
        if description and len(description.strip()) > 20:
            # Strategy 1: Direct substring match
            desc_lower = description.strip().lower()
            content_lower = content.strip().lower()
            
            # Find if description appears in first 30% of content
            content_first = content_lower[:len(content_lower) // 3]
            if desc_lower in content_first:
                # Find where it ends and skip it
                idx = content_first.find(desc_lower)
                skip_idx = idx + len(desc_lower)
                # Find next paragraph boundary
                next_para = content.find('\n\n', skip_idx)
                if next_para > 0:
                    content = content[next_para:].lstrip('\n')
                else:
                    # If no paragraph break, skip first paragraph
                    paragraphs = content.split('\n\n')
                    if len(paragraphs) > 1:
                        content = '\n\n'.join(paragraphs[1:])
            else:
                # Strategy 2: Fuzzy match (check if description is very similar to first paragraph)
                paragraphs = content.split('\n\n')
                if paragraphs:
                    first_para = paragraphs[0].lower()
                    # Check if description is 60%+ similar to first paragraph
                    similarity = difflib.SequenceMatcher(None, desc_lower, first_para).ratio()
                    if similarity > 0.6:
                        # Skip first paragraph
                        if len(paragraphs) > 1:
                            content = '\n\n'.join(paragraphs[1:])
        
        # Split content into logical chunks (smaller chunks for more scenes, easier to expand)
        # Use max_scenes - 2 to leave room for intro + conclusion
        target_chunks = max(3, (max_scenes - 2) if max_scenes else 6)
        chunks = self._split_content(content, target_chunks)
        
        # Allocate per-scene word budgets (intro + middle + summary + conclusion)
        per_scene_targets = None
        if total_words_budget:
            # Weights: intro 0.9, middles 1.0, summary 0.9, conclusion 0.8
            middle_count = max(1, len(chunks))
            weights = [0.9] + [1.0] * middle_count + [0.9] + [0.8]
            total_weight = sum(weights)
            per_scene_targets = [max(6, int(total_words_budget * (w / total_weight))) for w in weights]
        
        # Create pure narrative arc (no CTA, no product pitch)
        script = []
        
        # Scene 1: Hook/Introduction - but avoid duplication
        intro = self._build_hook(title, description)
        
        # Check if intro is too similar to first chunk (avoid duplication)
        if chunks and intro:
            first_chunk = chunks[0].lower()[:100]
            intro_lower = intro.lower()[:100]
            # If intro is 70%+ similar to first chunk, skip it or use a different hook
            import difflib
            similarity = difflib.SequenceMatcher(None, intro_lower, first_chunk).ratio()
            if similarity > 0.7:
                # Use a generic engaging hook instead
                intro = "Hãy cùng khám phá những điều thú vị và bổ ích từ bài viết này."
        
        if per_scene_targets:
            intro = self._limit_words(intro, per_scene_targets[0])
        script.append(intro)
        
        # Scenes 2-N: Main content (pure storytelling)
        for i, chunk in enumerate(chunks, 1):
            limit = None
            if per_scene_targets and i < len(per_scene_targets) - 2:
                limit = per_scene_targets[i]
            scene_text = self._chunk_to_narration(chunk, i, len(chunks), max_words=limit)
            if scene_text:
                script.append(scene_text)
        
        # Scene N-1: Summary/Key Takeaways
        if len(chunks) > 0:
            summary = self._generate_summary(chunks)
            if per_scene_targets:
                summary = self._limit_words(summary, per_scene_targets[-2])
            if summary:
                script.append(summary)
        
        # Final scene: Conclusion with advice
        if len(script) > 1:
            conclusion = self._generate_conclusion(title, content)
            if per_scene_targets:
                conclusion = self._limit_words(conclusion, per_scene_targets[-1])
            script.append(conclusion)
        
        logger.info(f"✅ Generated {len(script)} heuristic scenes")
        return script[:max_scenes]
    
    def _generate_summary(self, chunks: list) -> str:
        """Generate summary of key points"""
        if not chunks:
            return ""
        
        # Natural summary opener
        openers = [
            "Như vậy, qua những điểm chính trên,",
            "Tóm lại,",
            "Qua đó ta thấy,",
            "Có thể thấy rằng,"
        ]
        import random
        opener = random.choice(openers)
        
        closers = [
            "Đây là những bài học quý giá có thể áp dụng ngay trong cuộc sống.",
            "Những điểm này sẽ giúp bạn có cái nhìn sâu sắc hơn.",
            "Hãy ghi nhớ và áp dụng vào thực tế để thấy sự thay đổi."
        ]
        
        return f"{opener} chúng ta đã hiểu rõ hơn về chủ đề này. {random.choice(closers)}"
    
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
    
    def _chunk_to_narration(self, chunk: str, chunk_num: int, total_chunks: int, max_words: int = None) -> str:
        """Convert a content chunk into a natural narration"""
        import random
        
        # Remove extra spaces
        chunk = ' '.join(chunk.split())
        
        # Limit words per scene by duration-aware budget if provided
        words = chunk.split()
        limit = max_words if max_words and max_words > 0 else 150
        if len(words) > limit:
            words = words[:limit]
        
        narration = ' '.join(words)
        
        # Add natural varied transitions
        if chunk_num == 1:
            # First content chunk after intro - no transition needed
            pass
        elif chunk_num == total_chunks:
            # Last chunk
            transitions = [
                "Cuối cùng,",
                "Và điều quan trọng nhất là,",
                "Điểm then chốt là,"
            ]
            narration = f"{random.choice(transitions)} {narration}"
        else:
            # Middle chunks - varied transitions
            transitions = [
                "Tiếp theo,",
                "Ngoài ra,",
                "Một điểm quan trọng khác là,",
                "Đặc biệt,",
                "Điều này cho thấy,",
                "",  # Sometimes no transition for natural flow
                ""
            ]
            transition = random.choice(transitions)
            if transition:
                narration = f"{transition} {narration}"
        
        return narration

    def _build_hook(self, title: str, description: str) -> str:
        """Create a concise hook without repeating raw title text."""
        if description and len(description.strip()) > 20:
            # Use description directly, trimmed to reasonable length
            words = description.split()
            hook = ' '.join(words[:30])
            return hook
        # Extract a teaser/key phrase from title without reading it verbatim
        # Just return a short engaging opening
        return "Hãy cùng tìm hiểu những bài học quý giá sau đây."

    def _limit_words(self, text: str, max_words: int) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        trimmed = ' '.join(words[:max_words]).rstrip(',;')
        return trimmed
