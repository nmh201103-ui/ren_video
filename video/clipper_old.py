"""
Video Highlight Detection & Clipping - Optimized
Tự động phát hiện phần hay trong video và cắt thành clips
"""
import os
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip
import numpy as np
from utils.logger import get_logger

logger = get_logger()


class VideoHighlightDetector:
    """
    Detect highlights in video using:
    - Audio peaks (loud moments = exciting)
    - Uniform segments (fallback)
    """
    
    def __init__(self, min_clip_duration=10, max_clip_duration=60):
        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration
        self._video_cache = None
        self._video_path_cache = None
    
    def _get_video(self, video_path: str) -> VideoFileClip:
        """Cache video object to avoid reloading"""
        if self._video_path_cache != video_path or self._video_cache is None:
            if self._video_cache:
                self._video_cache.close()
            self._video_cache = VideoFileClip(video_path)
            self._video_path_cache = video_path
        return self._video_cache
    
    def cleanup(self):
        """Close cached video"""
        if self._video_cache:
            self._video_cache.close()
            self._video_cache = None
            self._video_path_cache = None
    
    def detect_highlights(self, video_path: str, num_clips: int = 5) -> List[Dict]:
        """
        Phát hiện highlights - Optimized version
        Returns: [{'start': 10.5, 'end': 25.3, 'score': 0.85}]
        """
        logger.info(f"🔍 Detecting {num_clips} highlights in: {os.path.basename(video_path)}")
        
        try:
            video = self._get_video(video_path)
            duration = video.duration
            
            logger.info(f"📹 Video: {duration:.1f}s")
            
            # Fast audio-based detection
            highlights = self._detect_audio_peaks_fast(video, num_clips)
            
            # Remove overlaps
            highlights = self._remove_overlaps(highlights)
            
            logger.info(f"✅ Found {len(highlights)} highlights")
            return highlights
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def _detect_audio_peaks_fast(self, video: VideoFileClip, num_clips: int) -> List[Dict]:
        """Optimized audio peak detection using batch processing"""
        try:
            if not video.audio:
                logger.warning("No audio - using uniform")
                return self._uniform_segments(video.duration, num_clips)
            
            # Batch process audio in chunks (much faster)
            duration = int(video.duration)
            chunk_size = 1.0  # 1 second chunks
            
            # Extract audio array once
            audio_array = video.audio.to_soundarray(fps=22050)
            
            # Convert stereo to mono
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)
            
            # Calculate RMS in chunks
            samples_per_chunk = int(22050 * chunk_size)
            num_chunks = len(audio_array) // samples_per_chunk
            
            rms_values = []
            for i in range(num_chunks):
                start_idx = i * samples_per_chunk
                end_idx = start_idx + samples_per_chunk
                chunk = audio_array[start_idx:end_idx]
                rms = np.sqrt(np.mean(chunk ** 2))
                rms_values.append((i * chunk_size, rms))
            
            if not rms_values:
                return self._uniform_segments(video.duration, num_clips)
            
            # Normalize and find peaks
            times, vals = zip(*rms_values)
            vals = np.array(vals)
            vals = vals / (vals.max() + 1e-8)  # Avoid div by zero
            
            # Find top peaks with minimum distance
            peak_indices = self._find_top_peaks(vals, num_clips * 3, min_distance=10)
            
            # Create highlights
            highlights = []
            for idx in peak_indices[:num_clips]:
                start = max(0, times[idx] - self.max_clip_duration / 2)
                end = min(duration, start + self.max_clip_duration)
                
                # Adjust to fit duration constraints
                if end - start > self.max_clip_duration:
                    end = start + self.max_clip_duration
                if end - start < self.min_clip_duration:
                    end = start + self.min_clip_duration
                
                highlights.append({
                    'start': start,
                    'end': min(end, duration),
                    'score': float(vals[idx])
                })
            
            return highlights
            
        except Exception as e:
            logger.error(f"Audio detection failed: {e}")
            return self._uniform_segments(video.duration, num_clips)
    
    def _find_top_peaks(self, values: np.ndarray, n: int, min_distance: int = 10) -> List[int]:
        """Find top N peaks with minimum distance between them"""
        # Get indices sorted by value
        sorted_indices = np.argsort(values)[::-1]
        
        peaks = []
        for idx in sorted_indices:
            # Check distance from existing peaks
            if all(abs(idx - p) >= min_distance for p in peaks):
                peaks.append(idx)
                if len(peaks) >= n:
                    break
        
        return sorted(peaks)  # Return in chronological order
                    peaks.append({
                        'start': max(0, times[i] - self.max_clip_duration // 2),
                        'end': min(duration, times[i] + self.max_clip_duration // 2),
                        'score': float(vals[i]),
                        'reason': 'audio_peak'
                    })
            
            # Sort by score
            peaks.sort(key=lambda x: x['score'], reverse=True)
            
            # Limit duration
            for peak in peaks:
                peak_duration = peak['end'] - peak['start']
                if peak_duration > self.max_clip_duration:
                    center = (peak['start'] + peak['end']) / 2
                    peak['start'] = center - self.max_clip_duration / 2
                    peak['end'] = center + self.max_clip_duration / 2
                elif peak_duration < self.min_clip_duration:
                    peak['end'] = peak['start'] + self.min_clip_duration
            
            return peaks[:num_clips * 2]  # Return more than needed for filtering
            
        except Exception as e:
            logger.error(f"Audio peak detection failed: {e}")
            return self._uniform_segments(video.duration, num_clips)
    
    def _uniform_segments(self, duration: float, num_clips: int) -> List[Dict]:
        """Fallback: divide video into uniform segments"""
        logger.info("Using uniform segmentation (no audio/scene detection)")
        
        clip_duration = min(self.max_clip_duration, duration / num_clips)
        clips = []
        
        for i in range(num_clips):
            start = i * (duration / num_clips)
            end = start + clip_duration
            
            if end > duration:
                end = duration
            
            if end - start >= self.min_clip_duration:
                clips.append({
                    'start': start,
                    'end': end,
                    'score': 0.5,
                    'reason': 'uniform'
                })
        
        return clips
    
    def _remove_overlaps(self, highlights: List[Dict]) -> List[Dict]:
        """Remove overlapping clips, keep highest scored ones"""
        if not highlights:
            return []
        
        # Sort by score
        sorted_clips = sorted(highlights, key=lambda x: x['score'], reverse=True)
        
        result = []
        for clip in sorted_clips:
            # Check overlap with existing clips
            overlaps = False
            for existing in result:
                if not (clip['end'] <= existing['start'] or clip['start'] >= existing['end']):
                    overlaps = True
                    break
            
            if not overlaps:
                result.append(clip)
        
        # Sort by start time
        result.sort(key=lambda x: x['start'])
        
        return result
    
    def cut_clip(self, video_path: str, start: float, end: float, output_path: str) -> bool:
        """Cut a clip from video"""
        try:
            logger.info(f"✂️ Cutting clip: {start:.1f}s - {end:.1f}s")
            
            video = VideoFileClip(video_path)
            clip = video.subclip(start, end)
            
            # Write with high quality
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                bitrate='8000k',
                audio_bitrate='320k',
                preset='medium',
                ffmpeg_params=[
                    '-crf', '18',
                    '-pix_fmt', 'yuv420p',
                ],
                logger=None
            )
            
            clip.close()
            video.close()
            
            logger.info(f"✅ Clip saved: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cut clip: {e}")
            return False
    
    def auto_clip(self, video_path: str, output_dir: str, 
                  num_clips: int = 5, format: str = 'short') -> List[str]:
        """
        Automatically detect highlights and cut clips
        format: 'short' (15-30s), 'medium' (45-60s)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Adjust clip duration based on format
        if format == 'short':
            self.max_clip_duration = 30
            self.min_clip_duration = 15
        elif format == 'medium':
            self.max_clip_duration = 60
            self.min_clip_duration = 30
        
        # Detect highlights
        highlights = self.detect_highlights(video_path, num_clips)
        
        if not highlights:
            logger.warning("No highlights found")
            return []
        
        # Cut clips
        output_paths = []
        for i, highlight in enumerate(highlights):
            filename = f"clip_{i+1}_{format}_{int(highlight['start'])}s.mp4"
            output_path = os.path.join(output_dir, filename)
            
            success = self.cut_clip(
                video_path,
                highlight['start'],
                highlight['end'],
                output_path
            )
            
            if success:
                output_paths.append(output_path)
        
        logger.info(f"🎬 Created {len(output_paths)} clips in: {output_dir}")
        return output_paths


class SmartClipper:
    """High-level interface for video clipping"""
    
    def __init__(self):
        self.detector = VideoHighlightDetector()
    
    def clip_from_url(self, url: str, num_clips: int = 5, 
                     format: str = 'short', cleanup: bool = True) -> Dict:
        """
        Complete workflow: download → detect → clip
        
        Args:
            url: Video URL
            num_clips: Number of clips to extract
            format: 'short' or 'medium'
            cleanup: Auto-delete downloaded video after processing (default: True)
            
        Returns: {'clips': [...], 'highlights': [...], 'temp_deleted': bool}
        """
        from video.downloader import VideoDownloader
        import os
        
        # Download
        downloader = VideoDownloader()
        video_path = downloader.download(url)
        
        if not video_path:
            return {'clips': [], 'highlights': [], 'error': 'Download failed'}
        
        try:
            # Detect highlights
            highlights = self.detector.detect_highlights(video_path, num_clips)
            
            # Cut clips
            output_dir = "output/clips"
            clips = self.detector.auto_clip(video_path, output_dir, num_clips, format)
            
            result = {
                'clips': clips,
                'highlights': highlights,
                'source_video': video_path,
                'temp_deleted': False
            }
            
            # Auto-cleanup: Delete downloaded video
            if cleanup:
                try:
                    os.remove(video_path)
                    logger.info(f"🗑️ Cleaned up temp file: {video_path}")
                    result['temp_deleted'] = True
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
            
            return result
            
        except Exception as e:
            # Cleanup on error too
            if cleanup and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    logger.info(f"🗑️ Cleaned up temp file after error")
                except:
                    pass
            raise e
