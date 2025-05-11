from typing import Dict, List, Any
import logging

from app.data.database import Database
from app.models.schemas import VideoHighlight, ChatResponse

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat interactions with video highlights."""
    
    @staticmethod
    async def process_query(query: str, max_results: int = 5) -> ChatResponse:
        """
        Process a user query and return relevant video highlights.
        
        Args:
            query: The user's question
            max_results: Maximum number of results to return
            
        Returns:
            ChatResponse with answer and relevant highlights
        """
        # Search for relevant highlights in the database
        highlights_data = await Database.get_highlights_by_query(query, max_results)
        
        # If no results found with query search, fallback to returning recent highlights
        if not highlights_data:
            logger.info(f"No results found for query: {query}. Falling back to recent highlights.")
            highlights_data = await Database.get_all_highlights(max_results)
        
        # Convert raw data to VideoHighlight models
        highlights = [
            VideoHighlight(
                id=h["id"],
                timestamp_start=h["timestamp_start"],
                timestamp_end=h["timestamp_end"],
                transcript=h["transcript"],
                summary=h["summary"],
                video_id=h.get("video_id"),
                video_filename=h.get("video_filename", ""),
                relevance=h.get("relevance", 0.0)
            )
            for h in highlights_data
        ]
        
        # Construct an answer based on the retrieved highlights
        answer = ChatService._construct_answer(query, highlights)
        
        return ChatResponse(
            answer=answer,
            highlights=highlights,
            total_highlights=len(highlights)
        )
    
    @staticmethod
    def _construct_answer(query: str, highlights: List[VideoHighlight]) -> str:
        """
        Construct a coherent answer from the retrieved highlights.
        
        Args:
            query: The user's question
            highlights: List of retrieved video highlights
            
        Returns:
            A constructed answer based on the highlights
        """
        if not highlights:
            return "I couldn't find any relevant information about that in the video."
        
        # Sort highlights by timestamp to maintain chronological order
        sorted_highlights = sorted(highlights, key=lambda h: h.timestamp_start)
        
        # For timing references in the answer
        def format_time(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}:{secs:02d}"
        
        # Construct the answer based on the highlights
        answer_parts = []
        
        # # Get the video filename from the first highlight (assuming same video)
        # video_name = sorted_highlights[0].video_filename if sorted_highlights[0].video_filename else "the video"
        
        # # Introduce the answer
        # answer_parts.append(f"Based on {video_name}, here's what I found:")
        
        # Add information from each highlight
        for i, highlight in enumerate(sorted_highlights):
            # Add timestamp reference
            time_ref = f"At {format_time(highlight.timestamp_start)}"
            
            # Add content - prefer the summary if available, otherwise use transcript
            if highlight.summary and len(highlight.summary.strip()) > 0:
                content = highlight.summary
            else:
                content = highlight.transcript
            
            # Combine parts for this highlight
            highlight_text = f"{time_ref}: {content}"
            answer_parts.append(highlight_text)
        
        # Join all parts with newlines
        answer = "\n\n".join(answer_parts)
        
        return answer
