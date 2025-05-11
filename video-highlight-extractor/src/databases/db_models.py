from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .db_manager import Base
from ..config import LLM_CONFIG

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    duration = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with highlights
    highlights = relationship("Highlight", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Video(id={self.id}, filename='{self.filename}', duration={self.duration})>"


class Highlight(Base):
    __tablename__ = 'highlights'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    embedding = Column(Vector(LLM_CONFIG['embedding_dimension']))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with video
    video = relationship("Video", back_populates="highlights")
    
    def __repr__(self):
        return f"<Highlight(id={self.id}, video_id={self.video_id}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Convert highlight to dictionary"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'timestamp': self.timestamp,
            'description': self.description,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
