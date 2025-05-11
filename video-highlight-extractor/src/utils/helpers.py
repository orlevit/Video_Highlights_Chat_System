import os
import logging
import datetime
from tqdm import tqdm

from ..config import PATHS, VIDEO_CONFIG

def setup_logging():
    """Set up logging configuration"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"video_processing_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Logging initialized")
    return log_file

def get_video_files():
    """Get all video files from the videos directory"""
    videos_dir = PATHS['videos_dir']
    
    if not os.path.exists(videos_dir):
        logging.warning(f"Videos directory not found: {videos_dir}")
        return []
    
    video_files = []
    
    for filename in os.listdir(videos_dir):
        file_path = os.path.join(videos_dir, filename)
        
        if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in VIDEO_CONFIG['video_extensions']):
            video_files.append(file_path)
    
    logging.info(f"Found {len(video_files)} video files in {videos_dir}")
    return video_files

def format_time(seconds):
    """Format time in seconds to MM:SS format"""
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"

def print_highlights_summary(video_filename, highlights):
    """Print a summary of the highlights for a video"""
    print(f"\n{'='*80}")
    print(f"HIGHLIGHTS FOR: {os.path.basename(video_filename)}")
    print(f"{'='*80}")
    
    for i, highlight in enumerate(highlights):
        print(f"\n--- Highlight #{i+1} at {format_time(highlight.timestamp)} ---")
        print(f"Summary: {highlight.summary}")
        print(f"Description: {highlight.description[:150]}...")
    
    print(f"\n{'='*80}\n")

class ProgressBar:
    """Custom progress bar for multi-stage processing"""
    
    def __init__(self, total_videos):
        """Initialize progress tracking"""
        self.total_videos = total_videos
        self.current_video = 0
        self.pbar = None
    
    def update_stage(self, video_name, stage, total_stages=5):
        """Update progress bar for a new stage"""
        if self.pbar is None:
            self.pbar = tqdm(total=self.total_videos * total_stages, 
                            desc=f"Processing {total_stages} stages for {self.total_videos} videos")
        
        # Update description
        self.pbar.set_description(f"Video {self.current_video+1}/{self.total_videos} - {os.path.basename(video_name)} - {stage}")
        self.pbar.update(1)
    
    def next_video(self):
        """Move to next video"""
        self.current_video += 1
    
    def close(self):
        """Close the progress bar"""
        if self.pbar is not None:
            self.pbar.close()
