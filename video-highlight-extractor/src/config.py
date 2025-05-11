import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('DB_NAME', 'video_highlights')
}

# LLM configuration
LLM_CONFIG = {
    'api_key': os.getenv('GOOGLE_API_KEY'),
    'model': 'models/gemini-2.0-flash-lite',
    'embedding_dimension': 768
}

# Video processing configuration
VIDEO_CONFIG = {
    'highlight_min_duration': 1.0,  # Minimum duration for a highlight in seconds
    'highlight_max_duration': 10.0,  # Maximum duration for a highlight in seconds
    'video_extensions': ['.mp4', '.mov', '.avi']
}

# Path configuration
PATHS = {
    'videos_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videos')
}