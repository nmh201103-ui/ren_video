"""
Video Segmentation & Chapter Detection
Phân tích script để tách thành segments/chapters riêng biệt
"""
import re
from typing import List, Dict, Tuple
from utils.logger import get_logger

logger = get_logger()


class VideoSegmenter:
    """Detect natural segments in movie review scripts"""
    
    # Keywords cho từng loại segment (movie review)
    SEGMENT_KEYWORDS = {
        'intro': ['giới thiệu', 'tên phim', 'thể loại', 'ra mắt', 'đạo diễn'],
        'plot': ['câu chuyện', 'cốt truyện', 'nội dung', 'phim kể về', 'bối cảnh'],
        'highlight': ['đặc biệt', 'ấn tượng', 'nổi bật', 'điểm nhấn', 'khoảnh khắc'],
        'review': ['đánh giá', 'nhận xét', 'rating', 'điểm', 'xếp hạng'],
        'cta': ['xem ngay', 'check out', 'đừng bỏ lỡ', 'phải xem', 'trailer']
    }
    
    def __init__(self, min_segment_length: int = 3):
        self.min_segment_length = min_segment_length
    
    def detect_segments(self, script: List[str]) -> List[Dict]:
        """
        Phân tích script thành segments
        Returns: [{'type': 'intro', 'sentences': [...], 'start_idx': 0, 'end_idx': 1}]
        """
        if not script or len(script) < self.min_segment_length:
            return [{'type': 'full', 'sentences': script, 'start_idx': 0, 'end_idx': len(script)}]
        
        segments = []
        current_type = self._detect_sentence_type(script[0])
        current_sentences = [script[0]]
        start_idx = 0
        
        for i in range(1, len(script)):
            sentence = script[i]
            sentence_type = self._detect_sentence_type(sentence)
            
            # Nếu type thay đổi hoặc đủ dài → tạo segment mới
            if sentence_type != current_type or len(current_sentences) >= 3:
                segments.append({
                    'type': current_type,
                    'sentences': current_sentences,
                    'start_idx': start_idx,
                    'end_idx': i,
                    'duration_estimate': len(current_sentences) * 4.5  # ~4.5s/sentence
                })
                current_type = sentence_type
                current_sentences = [sentence]
                start_idx = i
            else:
                current_sentences.append(sentence)
        
        # Thêm segment cuối
        if current_sentences:
            segments.append({
                'type': current_type,
                'sentences': current_sentences,
                'start_idx': start_idx,
                'end_idx': len(script),
                'duration_estimate': len(current_sentences) * 4.5
            })
        
        logger.info(f"✂️ Detected {len(segments)} segments: {[s['type'] for s in segments]}")
        return segments
    
    def _detect_sentence_type(self, sentence: str) -> str:
        """Phát hiện loại câu (intro/plot/highlight/review/cta)"""
        sentence_lower = sentence.lower()
        
        # Score từng loại
        scores = {}
        for seg_type, keywords in self.SEGMENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in sentence_lower)
            if score > 0:
                scores[seg_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        # Fallback: dùng vị trí câu
        return 'plot'  # Default
    
    def suggest_clips(self, segments: List[Dict], target_duration: int = 60) -> List[Dict]:
        """
        Gợi ý cắt video thành clips ngắn (cho TikTok/Reels)
        target_duration: độ dài mỗi clip (giây)
        """
        clips = []
        current_clip = []
        current_duration = 0
        
        for segment in segments:
            seg_duration = segment['duration_estimate']
            
            if current_duration + seg_duration <= target_duration:
                current_clip.append(segment)
                current_duration += seg_duration
            else:
                # Lưu clip hiện tại
                if current_clip:
                    clips.append({
                        'segments': current_clip,
                        'duration': current_duration,
                        'title': self._generate_clip_title(current_clip)
                    })
                # Bắt đầu clip mới
                current_clip = [segment]
                current_duration = seg_duration
        
        # Lưu clip cuối
        if current_clip:
            clips.append({
                'segments': current_clip,
                'duration': current_duration,
                'title': self._generate_clip_title(current_clip)
            })
        
        logger.info(f"📹 Suggested {len(clips)} clips (target: {target_duration}s each)")
        return clips
    
    def _generate_clip_title(self, segments: List[Dict]) -> str:
        """Tạo title cho clip dựa trên segments"""
        types = [s['type'] for s in segments]
        
        if 'intro' in types and 'plot' in types:
            return "Giới thiệu & Cốt truyện"
        elif 'highlight' in types:
            return "Những điểm nhấn"
        elif 'review' in types:
            return "Đánh giá chi tiết"
        elif 'cta' in types:
            return "Lời kết & Gợi ý"
        else:
            return f"Phần {types[0].title()}"


class ProductSegmenter:
    """Segment detection cho product review (khác với movie)"""
    
    SEGMENT_KEYWORDS = {
        'hook': ['khám phá', 'giới thiệu', 'hôm nay', 'mới ra mắt'],
        'feature': ['tính năng', 'thiết kế', 'chất liệu', 'màu sắc', 'kích thước'],
        'benefit': ['lợi ích', 'tiện lợi', 'dễ dàng', 'giúp bạn', 'phù hợp'],
        'price': ['giá', 'chỉ có', 'khuyến mãi', 'giảm giá'],
        'cta': ['mua ngay', 'chốt đơn', 'link', 'đặt hàng']
    }
    
    def detect_segments(self, script: List[str]) -> List[Dict]:
        """Phân tích product script thành segments"""
        segmenter = VideoSegmenter()
        segmenter.SEGMENT_KEYWORDS = self.SEGMENT_KEYWORDS
        return segmenter.detect_segments(script)
