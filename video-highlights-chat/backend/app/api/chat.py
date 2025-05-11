from fastapi import APIRouter, Depends, HTTPException
import logging

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/query", response_model=ChatResponse)
async def process_chat_query(request: ChatRequest) -> ChatResponse:
    """
    Process a chat query about video highlights.
    
    Args:
        request: The chat request containing the user's query
        
    Returns:
        ChatResponse with answer and relevant highlights
    """
    try:
        logger.info(f"Received chat query: {request.query}")
        
        # Validate the request
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Process the query through the chat service
        response = await ChatService.process_query(
            query=request.query,
            max_results=request.max_results
        )
        
        logger.info(f"Found {response.total_highlights} highlights for query: {request.query}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
