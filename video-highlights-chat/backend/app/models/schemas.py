from typing import List, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Chat request schema."""
    query: str = Field(..., description="The user's question about video highlights")
    max_results: Optional[int] = Field(5, description="Maximum number of results to return")

class VideoHighlight(BaseModel):
    """Video highlight schema."""
    id: int
    timestamp_start: float
    timestamp_end: float
    transcript: str
    summary: str
    video_id: Optional[int] = None
    video_filename: Optional[str] = None
    relevance: Optional[float] = None

class ChatResponse(BaseModel):
    """Chat response schema."""
    answer: str = Field(..., description="Answer constructed from video highlights")
    highlights: List[VideoHighlight] = Field(..., description="Relevant video highlights")
    total_highlights: int = Field(..., description="Total number of highlights found")
