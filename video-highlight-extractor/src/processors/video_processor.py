import os
import cv2
import numpy as np
import logging
from tqdm import tqdm
from datetime import datetime
import tempfile

from ..config import VIDEO_CONFIG

class VideoProcessor:
    def __init__(self):
        """Initialize the video processor"""
        self.highlight_min_duration = VIDEO_CONFIG['highlight_min_duration']
        self.highlight_max_duration = VIDEO_CONFIG['highlight_max_duration']
    
    def extract_frames(self, video_path):
        """
        Extract every frame from a video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            list: List of tuples containing (timestamp, frame)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logging.info(f"Processing video: {video_path}")
        logging.info(f"FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")
        
        frames = []
        frame_count = 0
        
        with tqdm(total=total_frames, desc="Extracting frames") as pbar:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Process every frame
                timestamp = frame_count / fps
                frames.append((timestamp, frame))
                
                frame_count += 1
                pbar.update(1)
        
        cap.release()
        logging.info(f"Extracted {len(frames)} frames from video")
        
        return frames, duration
    
    def detect_scene_changes(self, frames, threshold=30):
        """
        Detect scene changes in the extracted frames
        
        Args:
            frames (list): List of tuples containing (timestamp, frame)
            threshold (int): Threshold for scene change detection
            
        Returns:
            list: List of timestamps where scene changes occur
        """
        if not frames or len(frames) < 2:
            return []
        
        scene_changes = []
        prev_frame = cv2.cvtColor(frames[0][1], cv2.COLOR_BGR2GRAY)
        
        for i in range(1, len(frames)):
            timestamp, frame = frames[i]
            curr_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference
            diff = cv2.absdiff(prev_frame, curr_frame)
            _, diff = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            diff_percentage = (cv2.countNonZero(diff) / (diff.shape[0] * diff.shape[1])) * 100
            
            # If difference is above threshold, mark as scene change
            if diff_percentage > threshold:
                scene_changes.append(timestamp)
            
            prev_frame = curr_frame
        
        logging.info(f"Detected {len(scene_changes)} scene changes")
        return scene_changes
    
    def identify_potential_highlights(self, scene_changes, video_duration):
        """
        Identify potential highlights based on scene changes
        
        Args:
            scene_changes (list): List of timestamps where scene changes occur
            video_duration (float): Total duration of the video
            
        Returns:
            list: List of tuples containing (start_time, end_time) for potential highlights
        """
        if not scene_changes:
            # If no scene changes detected, consider the whole video as one segment
            return [(0, min(video_duration, self.highlight_max_duration))]
        
        potential_highlights = []
        
        # Add first segment from start to first scene change
        if scene_changes[0] > self.highlight_min_duration:
            potential_highlights.append((0, min(scene_changes[0], self.highlight_max_duration)))
        
        # Process segments between scene changes
        for i in range(len(scene_changes) - 1):
            start_time = scene_changes[i]
            end_time = scene_changes[i + 1]
            
            segment_duration = end_time - start_time
            
            if segment_duration >= self.highlight_min_duration:
                # If segment is too long, cap it at max duration
                if segment_duration > self.highlight_max_duration:
                    end_time = start_time + self.highlight_max_duration
                
                potential_highlights.append((start_time, end_time))
        
        # Add last segment from last scene change to end of video
        last_start = scene_changes[-1]
        if video_duration - last_start >= self.highlight_min_duration:
            potential_highlights.append((last_start, min(video_duration, last_start + self.highlight_max_duration)))
        
        logging.info(f"Identified {len(potential_highlights)} potential highlights")
        return potential_highlights
    
    def extract_highlight_frames(self, video_path, start_time, end_time):
        """
        Extract representative frames from a highlight segment
        
        Args:
            video_path (str): Path to the video file
            start_time (float): Start time of the highlight segment
            end_time (float): End time of the highlight segment
            
        Returns:
            list: List of frames from the highlight segment
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate frame positions
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        # Extract a maximum of 5 evenly distributed frames
        num_frames = min(5, end_frame - start_frame)
        frame_indices = np.linspace(start_frame, end_frame - 1, num_frames, dtype=int)
        
        highlight_frames = []
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if ret:
                highlight_frames.append(frame)
        
        cap.release()
        return highlight_frames
    
    def save_highlight_clip(self, video_path, start_time, end_time, output_path=None):
        """
        Save a video clip of the highlight segment
        
        Args:
            video_path (str): Path to the video file
            start_time (float): Start time of the highlight segment
            end_time (float): End time of the highlight segment
            output_path (str, optional): Path to save the highlight clip
            
        Returns:
            str: Path to the saved highlight clip
        """
        from moviepy.editor import VideoFileClip
        
        if output_path is None:
            # Create temporary file for the clip
            filename = os.path.basename(video_path)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                tempfile.gettempdir(), 
                f"{name}_highlight_{timestamp}_{start_time:.1f}_{end_time:.1f}{ext}"
            )
        
        try:
            # Extract the clip
            with VideoFileClip(video_path) as video:
                # Ensure times are within video bounds
                start_time = max(0, start_time)
                end_time = min(video.duration, end_time)
                
                # Extract the subclip
                clip = video.subclip(start_time, end_time)
                clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            
            logging.info(f"Saved highlight clip to {output_path}")
            return output_path
        
        except Exception as e:
            logging.error(f"Error saving highlight clip: {e}")
            return None
