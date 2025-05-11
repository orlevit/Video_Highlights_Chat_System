#!/usr/bin/env python3
import os
import sys
import logging
import time
import argparse

# Import processors and services only when needed to avoid circular imports
from .utils.helpers import setup_logging, get_video_files, print_highlights_summary, ProgressBar

def process_video(video_path, db_manager, progress_bar=None):
    """
    Process a video file to extract and store highlights
    
    Args:
        video_path (str): Path to the video file
        db_manager (DBManager): Database manager instance
        progress_bar (ProgressBar, optional): Progress bar for tracking processing stages
        
    Returns:
        tuple: (video_id, list of highlights)
    """
    # Import here to avoid circular imports
    from .processors.video_processor import VideoProcessor
    from .processors.audio_processor import AudioProcessor
    from .llm.llm_service import LLMService
    from .llm.llm_embeddings import EmbeddingService
    
    # Initialize processors and services
    video_processor = VideoProcessor()
    audio_processor = AudioProcessor()
    llm_service = LLMService()
    embedding_service = EmbeddingService()
    
    # Start processing
    logging.info(f"Processing video: {video_path}")
    
    # Extract frames and get video duration
    if progress_bar:
        progress_bar.update_stage(video_path, "Extracting frames")
    frames, duration = video_processor.extract_frames(video_path)
    
    # Detect scene changes
    if progress_bar:
        progress_bar.update_stage(video_path, "Detecting scene changes")
    scene_changes = video_processor.detect_scene_changes(frames)
    
    # Identify potential highlights
    potential_highlights = video_processor.identify_potential_highlights(scene_changes, duration)
    
    # Add video to database
    video_filename = os.path.basename(video_path)
    video = db_manager.add_video(video_filename, duration)
    
    highlights = []
    
    # Process each potential highlight
    for i, (start_time, end_time) in enumerate(potential_highlights):
        if progress_bar:
            progress_bar.update_stage(
                video_path, 
                f"Processing highlight {i+1}/{len(potential_highlights)}"
            )
        
        # Extract highlight frames
        highlight_frames = video_processor.extract_highlight_frames(
            video_path, start_time, end_time
        )
        
        # Extract audio segment and transcribe
        audio_segment_path = audio_processor.extract_audio_segment(
            video_path, start_time, end_time
        )
        transcript = ""
        if audio_segment_path:
            transcript = audio_processor.transcribe_audio(audio_segment_path)
            # Clean up temporary audio file
            if os.path.exists(audio_segment_path):
                os.remove(audio_segment_path)
        
        # Generate highlight description using LLM
        result = llm_service.generate_highlight_description(
            highlight_frames, transcript, start_time, end_time
        )
        
        description = result.get("description", "")
        summary = result.get("summary", "")
        
        # Generate embedding for the highlight
        embedding = embedding_service.get_highlight_embedding(description, summary)
        
        # Add highlight to database
        highlight = db_manager.add_highlight(
            video.id, start_time, description, summary, embedding.tolist()
        )
        
        highlights.append(highlight)
    
    if progress_bar:
        progress_bar.update_stage(video_path, "Completed")
    
    logging.info(f"Processed {len(highlights)} highlights for video: {video_path}")
    return video.id, highlights

def run_demo():
    """Run the demo for video processing and highlight extraction"""
    # Set up logging
    setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Video Highlight Extractor")
    parser.add_argument("--video", help="Path to a specific video file to process")
    parser.add_argument("--list-videos", action="store_true", help="List available videos")
    args = parser.parse_args()
    
    # Import here to avoid circular imports
    from .databases.db_manager import DBManager
    
    # Initialize database manager
    db_manager = DBManager()
    
    try:
        # Get video files
        if args.video:
            if not os.path.exists(args.video):
                logging.error(f"Video file not found: {args.video}")
                sys.exit(1)
            video_files = [args.video]
        else:
            video_files = get_video_files()
        
        # List videos if requested
        if args.list_videos:
            print("\nAvailable video files:")
            for i, video_file in enumerate(video_files):
                print(f"{i+1}. {os.path.basename(video_file)}")
            sys.exit(0)
        
        if not video_files:
            logging.error("No video files found. Please add videos to the 'videos' directory.")
            sys.exit(1)
        
        # Initialize progress bar
        progress_bar = ProgressBar(len(video_files))
        
        # Process each video
        for video_path in video_files:
            video_id, highlights = process_video(video_path, db_manager, progress_bar)
            
            # Print highlights summary
            print_highlights_summary(video_path, highlights)
            
            # Move to next video
            progress_bar.next_video()
        
        # Close progress bar
        progress_bar.close()
        
        # Print overall summary
        videos = db_manager.get_all_videos()
        print(f"\nProcessed {len(videos)} videos with a total of {sum(len(db_manager.get_highlights_by_video_id(v.id)) for v in videos)} highlights")
        
    except KeyboardInterrupt:
        logging.info("Processing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error in processing: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Close database connection
        db_manager.close()

if __name__ == "__main__":
    run_demo()
