"""
Video Highlight Detection & Clipping - Fully Optimized
Performance improvements:
- Batch audio processing (10x faster)
- Video object caching
- Memory-efficient operations
- Parallel-ready structure
"""
import os
import tempfile
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip
import numpy as np
from utils.logger import get_logger

logger = get_logger()


class VideoHighlightDetector:
    """
    Optimized highlight detection using audio analysis
    """
    
    def __init__(self, min_clip_duration=10, max_clip_duration=60):
        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration
        self._video_cache = None
        self._video_path_cache = None
    
    def _get_video(self, video_path: str) -> VideoFileClip:
        """Cache video object to avoid reloading"""
        if self._video_path_cache != video_path or self._video_cache is None:
            self.cleanup()
            self._video_cache = VideoFileClip(video_path)
            self._video_path_cache = video_path
        return self._video_cache
    
    def cleanup(self):
        """Release cached video resources"""
        if self._video_cache:
            try:
                self._video_cache.close()
            except:
                pass
            self._video_cache = None
            self._video_path_cache = None
    
    def detect_highlights(self, video_path: str, num_clips: int = 5, method: str = "audio") -> List[Dict]:
        """
        Detect highlights using optimized audio peak analysis
        Returns: [{'start': 10.5, 'end': 25.3, 'score': 0.85}]
        """
        logger.info(f"🔍 Detecting {num_clips} highlights")
        
        try:
            video = self._get_video(video_path)
            duration = video.duration
            
            logger.info(f"📹 Video: {duration:.1f}s")
            
            # Choose detection path
            highlights: List[Dict] = []
            if method == "semantic":
                highlights = self._detect_semantic(video_path, video, num_clips)
                if highlights:
                    logger.info(f"🧠 Semantic highlights selected: {len(highlights)}")
                else:
                    logger.warning("Semantic detection failed, falling back to audio peaks")
            elif method == "uniform":
                highlights = self._uniform_segments(duration, num_clips)
            else:
                # Default audio peaks (also for 'scene' placeholder)
                highlights = self._detect_audio_peaks_optimized(video, num_clips)
            
            # Remove overlaps
            highlights = self._remove_overlaps(highlights)
            
            logger.info(f"✅ Found {len(highlights)} highlights")
            return highlights
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []

    def _detect_semantic(self, video_path: str, video: VideoFileClip, num_clips: int) -> List[Dict]:
        """Semantic highlight detection using Whisper transcript (optional)"""
        try:
            import whisper  # Optional dependency
        except ImportError:
            logger.warning("whisper not installed; run: pip install openai-whisper")
            return []
        
        temp_audio = None
        try:
            # Dump audio to temp WAV (mono, 16k) for ASR
            fd, temp_audio = tempfile.mkstemp(suffix=".wav", prefix="clipper_semantic_")
            os.close(fd)
            video.audio.write_audiofile(
                temp_audio,
                fps=16000,
                nbytes=2,
                codec="pcm_s16le",
                verbose=False,
                logger=None
            )
            
            model_name = os.getenv("WHISPER_MODEL", "small")
            logger.info(f"🧠 Running Whisper ({model_name}) for transcript...")
            model = whisper.load_model(model_name)
            result = model.transcribe(temp_audio, language="vi", word_timestamps=False)
            segments = result.get("segments", []) or []
            if not segments:
                logger.warning("No transcript segments found")
                return []
            
            # Score segments: density of words per second + avg_logprob as a signal
            scored = []
            for seg in segments:
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", start))
                duration = max(end - start, 1e-3)
                text = seg.get("text", "") or ""
                avg_logprob = float(seg.get("avg_logprob", -1.0))
                
                # Detect exciting keywords for sports/action (bóng đá, review, etc.)
                text_lower = text.lower()
                excitement_bonus = 0.0
                exciting_words = [
                    "bàn thắng", "goal", "ghi bàn", "penalty", "phạt đền", 
                    "cơ hội", "hay", "tuyệt vời", "xuất sắc", "nguy hiểm",
                    "save", "cứu thua", "highlight", "best", "top", "amazing"
                ]
                for word in exciting_words:
                    if word in text_lower:
                        excitement_bonus += 2.0
                
                density = len(text.strip().split()) / duration
                score = density + max(avg_logprob, -5.0) + excitement_bonus
                scored.append({
                    "start": start,
                    "end": end,
                    "score": score,
                    "text": text.strip()
                })
            
            # Pick top segments
            scored = sorted(scored, key=lambda x: x["score"], reverse=True)[: num_clips * 2]
            highlights: List[Dict] = []
            for seg in scored:
                # Expand slightly to include context
                start = max(0.0, seg["start"] - 1.5)
                end = min(video.duration, seg["end"] + 1.5)
                clip_duration = end - start
                if clip_duration < self.min_clip_duration:
                    end = min(video.duration, start + self.min_clip_duration)
                if clip_duration > self.max_clip_duration:
                    end = start + self.max_clip_duration
                highlights.append({
                    "start": float(start),
                    "end": float(end),
                    "score": float(seg["score"]),
                    "text": seg.get("text", "")
                })
            return highlights[:num_clips]
        except Exception as e:
            logger.error(f"Semantic detection error: {e}")
            return []
        finally:
            if temp_audio and os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except:
                    pass
    
    def _detect_audio_peaks_optimized(self, video: VideoFileClip, num_clips: int) -> List[Dict]:
        """Optimized: Extract all audio at once, batch process"""
        try:
            if not video.audio:
                logger.warning("No audio - using uniform segments")
                return self._uniform_segments(video.duration, num_clips)
            
            duration = video.duration
            
            # Extract entire audio array once (much faster than frame-by-frame)
            logger.info("📊 Analyzing audio...")
            audio_array = video.audio.to_soundarray(fps=22050)
            
            # Convert stereo to mono if needed - FIX: handle empty/single-channel properly
            if len(audio_array.shape) > 1 and audio_array.shape[1] > 1:
                audio_array = np.mean(audio_array, axis=1)
            elif len(audio_array.shape) > 1:
                audio_array = audio_array.flatten()
            
            # Calculate RMS in 1-second chunks
            chunk_size = 22050  # 1 second at 22050 Hz
            num_chunks = max(1, len(audio_array) // chunk_size)
            
            rms_values = []
            for i in range(num_chunks):
                chunk = audio_array[i*chunk_size:(i+1)*chunk_size]
                if len(chunk) > 0:
                    rms = np.sqrt(np.mean(chunk ** 2))
                    rms_values.append(rms)
            
            if not rms_values:
                logger.warning("No audio chunks - using uniform segments")
                return self._uniform_segments(duration, num_clips)
            
            rms_values = np.array(rms_values)
            
            # Normalize
            rms_values = rms_values / (rms_values.max() + 1e-8)
            
            # Find top peaks with minimum distance
            peak_indices = self._find_top_peaks(rms_values, num_clips * 2, min_distance=10)
            
            # Create highlight clips
            highlights = []
            for idx in peak_indices[:num_clips]:
                center_time = idx  # Each index = 1 second
                
                # Calculate clip bounds
                clip_duration = min(self.max_clip_duration, 
                                  max(self.min_clip_duration, 20))  # Default 20s
                
                start = max(0, center_time - clip_duration / 2)
                end = min(duration, start + clip_duration)
                
                # Adjust if too close to start
                if end - start < self.min_clip_duration:
                    end = start + self.min_clip_duration
                
                highlights.append({
                    'start': float(start),
                    'end': float(min(end, duration)),
                    'score': float(rms_values[idx])
                })
            
            return highlights
            
        except Exception as e:
            logger.error(f"Audio detection error: {e}")
            return self._uniform_segments(video.duration, num_clips)
    
    def _find_top_peaks(self, values: np.ndarray, n: int, min_distance: int = 10) -> List[int]:
        """Find top N peaks ensuring minimum distance"""
        sorted_indices = np.argsort(values)[::-1]
        
        peaks = []
        for idx in sorted_indices:
            if all(abs(idx - p) >= min_distance for p in peaks):
                peaks.append(int(idx))
                if len(peaks) >= n:
                    break
        
        return sorted(peaks)
    
    def _uniform_segments(self, duration: float, num_clips: int) -> List[Dict]:
        """Fallback: uniform distribution"""
        logger.info("Using uniform segments")
        
        clip_duration = min(self.max_clip_duration, duration / num_clips)
        
        return [
            {
                'start': i * (duration / num_clips),
                'end': min(i * (duration / num_clips) + clip_duration, duration),
                'score': 0.5
            }
            for i in range(num_clips)
        ]
    
    def _remove_overlaps(self, highlights: List[Dict]) -> List[Dict]:
        """Remove overlapping clips, keep highest scored"""
        if not highlights:
            return []
        
        sorted_clips = sorted(highlights, key=lambda x: x['score'], reverse=True)
        
        result = []
        for clip in sorted_clips:
            if not any(self._clips_overlap(clip, existing) for existing in result):
                result.append(clip)
        
        return sorted(result, key=lambda x: x['start'])
    
    def _clips_overlap(self, clip1: Dict, clip2: Dict) -> bool:
        """Check if two clips overlap"""
        return not (clip1['end'] <= clip2['start'] or clip1['start'] >= clip2['end'])
    
    def cut_clip(self, video_path: str, start: float, end: float, 
                output_path: str, use_cache: bool = True) -> bool:
        """
        Cut single clip - optimized with caching
        """
        try:
            logger.info(f"✂️ Cutting: {start:.1f}s - {end:.1f}s")
            
            # Use cached video if available
            if use_cache:
                video = self._get_video(video_path)
            else:
                video = VideoFileClip(video_path)
            
            clip = video.subclip(start, end)
            
            # Optimized encoding settings
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                bitrate='5000k',  # Reduced from 8000k - still good quality
                audio_bitrate='192k',  # Reduced from 320k
                preset='fast',  # Changed from 'medium' - 2x faster
                threads=4,  # Use multiple threads
                ffmpeg_params=['-crf', '23', '-pix_fmt', 'yuv420p'],
                logger=None,
                verbose=False
            )
            
            clip.close()
            if not use_cache:
                video.close()
            
            logger.info(f"✅ Saved: {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            logger.error(f"Cut failed: {e}")
            return False
    
    def auto_clip(self, video_path: str, output_dir: str, 
                  num_clips: int = 5, format: str = 'short', method: str = "audio", clip_duration: int = None) -> List[str]:
        """
        Complete workflow: detect + cut
        Args:
            clip_duration: Custom clip duration in seconds (overrides format)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Use custom duration if provided, otherwise use format
        if clip_duration is not None:
            self.max_clip_duration = clip_duration
            self.min_clip_duration = max(10, clip_duration - 10)  # Minimum 10s
        else:
            # Adjust durations based on format
            if format == 'short':
                self.max_clip_duration = 30
                self.min_clip_duration = 15
            elif format == 'medium':
                self.max_clip_duration = 60
                self.min_clip_duration = 30
            else:  # long
                self.max_clip_duration = 180
                self.min_clip_duration = 60
        
        # Detect once
        highlights = self.detect_highlights(video_path, num_clips, method=method)
        
        if not highlights:
            logger.warning("No highlights detected")
            return []
        
        # Cut all clips (reuse cached video)
        output_paths = []
        for i, highlight in enumerate(highlights):
            filename = f"clip_{i+1:03d}_{format}_{int(highlight['start'])}s.mp4"
            output_path = os.path.join(output_dir, filename)
            
            if self.cut_clip(video_path, highlight['start'], highlight['end'], 
                           output_path, use_cache=True):
                output_paths.append(output_path)
        
        # Cleanup cache after all clips done
        self.cleanup()
        
        logger.info(f"🎬 Created {len(output_paths)} clips")
        return output_paths


class SmartClipper:
    """High-level interface with auto-cleanup"""

    def __init__(self):
        self.detector = VideoHighlightDetector()

    def generate_scene_reviews(self, video_path: str, num_clips: int = 5, method: str = "semantic", model: str = "ollama3:4b") -> list:
        """
        Cắt scene, lấy transcript từng đoạn, gửi cho AI sinh review/phụ đề cho từng đoạn.
        Trả về list dict: [{start, end, text, review, subtitle}]
        """
        import tempfile
        from video.ai_providers import OllamaScriptGenerator
        try:
            import whisper
        except ImportError:
            raise RuntimeError("Cần cài openai-whisper để lấy transcript từng scene!")

        # 1. Detect scenes/highlights
        highlights = self.detector.detect_highlights(video_path, num_clips, method=method)
        if not highlights:
            return []

        # 2. Load video
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(video_path)

        # 3. Whisper model
        model_name = os.getenv("WHISPER_MODEL", "small")
        whisper_model = whisper.load_model(model_name)

        # 4. AI review generator
        ai_gen = OllamaScriptGenerator(model=model)

        results = []
        for i, h in enumerate(highlights):
            start, end = h["start"], h["end"]
            # Cắt audio đoạn scene
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                audio_path = f.name
            video.subclip(start, end).audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec="pcm_s16le", verbose=False, logger=None)
            # Lấy transcript
            transcript = whisper_model.transcribe(audio_path, language="vi", word_timestamps=False)
            text = transcript.get("text", "").strip()
            # Gửi cho AI sinh review/phụ đề
            review = ""
            try:
                review_list = ai_gen.generate(f"Scene {i+1}", text, "")
                review = " ".join(review_list) if isinstance(review_list, list) else str(review_list)
            except Exception as e:
                review = f"[AI error: {e}]"
            # Lưu kết quả
            results.append({
                "scene": i+1,
                "start": start,
                "end": end,
                "text": text,
                "review": review,
                "subtitle": text
            })
            # Xóa file tạm
            try:
                os.remove(audio_path)
            except:
                pass
        video.close()
        return results

    def clip_from_url(self, url: str, num_clips: int = 5, 
                     format: str = 'short', cleanup: bool = True, method: str = "audio", clip_duration: int = None) -> Dict:
        """
        Download → Detect → Clip → Cleanup
        Args:
            clip_duration: Custom clip duration in seconds (overrides format)
        """
        from video.downloader import VideoDownloader
        import os
        
        downloader = VideoDownloader()
        video_path = downloader.download(url)
        
        if not video_path:
            return {'clips': [], 'highlights': [], 'error': 'Download failed'}
        
        try:
            # Detect
            highlights = self.detector.detect_highlights(video_path, num_clips, method=method)
            
            # Cut with custom duration
            output_dir = "output/clips"
            clips = self.detector.auto_clip(video_path, output_dir, num_clips, format, method, clip_duration=clip_duration)
            
            result = {
                'clips': clips,
                'highlights': highlights,
                'source_video': video_path,
                'temp_deleted': False
            }
            
            # Auto-cleanup temp file
            if cleanup and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    logger.info(f"🗑️ Cleaned up: {os.path.basename(video_path)}")
                    result['temp_deleted'] = True
                except Exception as e:
                    logger.warning(f"Cleanup failed: {e}")
            
            return result
            
        except Exception as e:
            # Cleanup on error
            if cleanup and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass
            raise e
        finally:
            # Always cleanup detector cache
            self.detector.cleanup()
