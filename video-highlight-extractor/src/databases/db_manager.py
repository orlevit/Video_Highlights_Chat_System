from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, MetaData, Table
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import numpy as np
import logging

from ..config import DB_CONFIG, LLM_CONFIG

Base = declarative_base()

class DBManager:
    def __init__(self):
        """Initialize database connection and session"""
        self.connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(self.connection_string, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        # Ensure tables exist
        try:
            Base.metadata.create_all(self.engine)
            logging.info("Database tables initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database tables: {e}")
            raise
    
    def add_video(self, filename, duration):
        """Add a new video to the database"""
        from .db_models import Video
        
        video = Video(filename=filename, duration=duration)
        self.session.add(video)
        self.session.commit()
        return video
    
    def add_highlight(self, video_id, timestamp, description, summary, embedding):
        """Add a new highlight to the database"""
        from .db_models import Highlight
        
        highlight = Highlight(
            video_id=video_id,
            timestamp=timestamp,
            description=description,
            summary=summary,
            embedding=embedding
        )
        self.session.add(highlight)
        self.session.commit()
        return highlight
    
    def get_similar_highlights(self, embedding, limit=5):
        """Find similar highlights using vector similarity search"""
        from .db_models import Highlight
        
        # Convert numpy array to list if needed
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        # Query similar highlights using L2 distance
        results = self.session.query(Highlight).\
            order_by(Highlight.embedding.l2_distance(embedding)).\
            limit(limit).all()
        
        return results
    
    def get_all_videos(self):
        """Get all videos from the database"""
        from .db_models import Video
        return self.session.query(Video).all()
    
    def get_highlights_by_video_id(self, video_id):
        """Get all highlights for a specific video"""
        from .db_models import Highlight
        return self.session.query(Highlight).filter(Highlight.video_id == video_id).all()
    
    def close(self):
        """Close the database session"""
        self.session.close()
