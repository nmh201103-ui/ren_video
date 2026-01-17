"""Scene Detection - Automatically detect scene boundaries in video"""
import os
import json
import tempfile
from typing import List, Dict, Tuple
import cv2
import numpy as np
from utils.logger import get_logger

logger = get_logger()


class SceneDetector:
    """Detect scene boundaries using visual analysis"""
    
    def __init__(self, threshold: float = 27.0):
        """
        Initialize scene detector
        Args:
            threshold: Brightness change threshold for scene detection (0-100)
        """
        self.threshold = threshold
        self.scenes = []
        self.temp_frames = []
    
    def detect_scenes(self, video_path: str, max_scenes: int = 12) -> List[Dict]:
        """
        Detect scenes in video
        Args:
            video_path: Path to video file
            max_scenes: Maximum number of scenes to extract
        Returns:
            List of scene dicts with start, end, duration, and frame
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Cannot open video: {video_path}")
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"📹 Video: {fps}fps, {total_frames} frames")
            
            scenes = []
            prev_frame = None
            scene_start = 0
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resample frame for faster processing
                small_frame = cv2.resize(frame, (640, 360))
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # Calculate brightness difference
                    diff = np.mean(np.abs(gray.astype(float) - prev_frame.astype(float)))
                    
                    # Scene change detected
                    if diff > self.threshold:
                        scene_end = frame_count
                        duration = (scene_end - scene_start) / fps
                        
                        if duration > 1.0:  # Minimum 1 second per scene
                            scenes.append({
                                'start': scene_start / fps,
                                'end': scene_end / fps,
                                'duration': duration,
                                'frame_idx': scene_start,
                                'thumbnail': frame.copy()
                            })
                            logger.info(f"  Scene {len(scenes)}: {duration:.1f}s ({scene_start}-{scene_end} frames)")
                        
                        scene_start = scene_end
                
                prev_frame = gray
                frame_count += 1
                
                # Progress
                if frame_count % int(fps * 10) == 0:  # Every 10 seconds
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"  Processing: {progress:.1f}%")
            
            # Add final scene
            if frame_count - scene_start > fps:
                duration = (frame_count - scene_start) / fps
                scenes.append({
                    'start': scene_start / fps,
                    'end': frame_count / fps,
                    'duration': duration,
                    'frame_idx': scene_start,
                    'thumbnail': None
                })
            
            cap.release()
            
            # Limit to max_scenes
            if len(scenes) > max_scenes:
                # Distribute evenly
                step = len(scenes) // max_scenes
                scenes = scenes[::step][:max_scenes]
            
            logger.info(f"✅ Detected {len(scenes)} scenes")
            self.scenes = scenes
            return scenes
        
        except Exception as e:
            logger.exception("Scene detection failed")
            return []
    
    def extract_scene_frames(self, video_path: str, scenes: List[Dict], 
                           output_dir: str = "assets/temp/scene_frames") -> List[Dict]:
        """
        Extract representative frame from each scene
        Args:
            video_path: Path to video
            scenes: List of detected scenes
            output_dir: Where to save frames
        Returns:
            Updated scenes with frame paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        for i, scene in enumerate(scenes):
            # Extract middle frame of scene
            mid_frame_idx = int((scene['start'] + scene['end']) / 2 * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame_idx)
            
            ret, frame = cap.read()
            if ret:
                output_path = os.path.join(output_dir, f"scene_{i:03d}.jpg")
                cv2.imwrite(output_path, frame)
                scene['frame_path'] = output_path
                logger.info(f"  Extracted frame: {output_path}")
        
        cap.release()
        return scenes
    
    def save_scenes(self, output_path: str):
        """Save scene data to JSON"""
        data = [{k: v for k, v in s.items() if k != 'thumbnail'} for s in self.scenes]
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Scenes saved: {output_path}")
    
    def load_scenes(self, input_path: str) -> List[Dict]:
        """Load scene data from JSON"""
        with open(input_path, 'r') as f:
            self.scenes = json.load(f)
        
        logger.info(f"📂 Loaded {len(self.scenes)} scenes from {input_path}")
        return self.scenes
