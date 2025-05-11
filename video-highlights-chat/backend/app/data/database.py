import asyncpg
import logging
from typing import Dict, List, Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
pool: Optional[asyncpg.Pool] = None

async def init_db() -> None:
    """Initialize the database connection pool."""
    global pool
    try:
        # Create a connection pool
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=20
        )
        logger.info("Database connection pool established")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise

class Database:
    """Database access layer for video highlights data."""
    
    @staticmethod
    async def get_highlights_by_query(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for video highlights based on a query using text similarity.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching highlight records
        """
        if not pool:
            await init_db()
            
        # Using text similarity with ts_vector and ts_query for basic search
        # This can be enhanced with embedding-based vector similarity if needed
        sql = """
        SELECT 
            h.id, 
            h.timestamp,
            h.description AS transcript,
            h.summary,
            v.filename AS video_filename,
            v.id AS video_id,
            ts_rank_cd(
                to_tsvector('english', h.description || ' ' || h.summary), 
                plainto_tsquery('english', $1)
            ) AS relevance
        FROM 
            highlights h
        JOIN
            videos v ON h.video_id = v.id
        WHERE 
            to_tsvector('english', h.description || ' ' || h.summary) @@ 
            plainto_tsquery('english', $1)
        ORDER BY 
            relevance DESC
        LIMIT $2
        """
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, query, limit)
                
                # Convert to list of dictionaries
                results = [
                    {
                        "id": row["id"],
                        "timestamp_start": row["timestamp"],
                        # Estimate timestamp_end as 10 seconds after start for UI purposes
                        "timestamp_end": row["timestamp"] + 10.0,
                        "transcript": row["transcript"],
                        "summary": row["summary"],
                        "video_id": row["video_id"],
                        "video_filename": row["video_filename"],
                        "relevance": float(row["relevance"])
                    }
                    for row in rows
                ]
                
                return results
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    @staticmethod
    async def get_all_highlights(limit: int = 100) -> List[Dict[str, Any]]:
        """Get all video highlights up to a limit."""
        if not pool:
            await init_db()
            
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT 
                        h.id, 
                        h.timestamp,
                        h.description AS transcript,
                        h.summary,
                        v.filename AS video_filename,
                        v.id AS video_id
                    FROM 
                        highlights h
                    JOIN
                        videos v ON h.video_id = v.id
                    ORDER BY 
                        h.timestamp
                    LIMIT $1
                    """, 
                    limit
                )
                
                results = [
                    {
                        "id": row["id"],
                        "timestamp_start": row["timestamp"],
                        # Estimate timestamp_end as 10 seconds after start for UI purposes
                        "timestamp_end": row["timestamp"] + 10.0,
                        "transcript": row["transcript"],
                        "summary": row["summary"],
                        "video_id": row["video_id"],
                        "video_filename": row["video_filename"]
                    }
                    for row in rows
                ]
                
                return results
        except Exception as e:
            logger.error(f"Failed to fetch highlights: {e}")
            return []
    
    @staticmethod
    async def get_highlights_by_vector_similarity(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for video highlights based on vector embedding similarity.
        This is a placeholder for future implementation when embeddings are available.
        
        Args:
            query_embedding: The embedding vector of the query
            limit: Maximum number of results to return
            
        Returns:
            List of matching highlight records
        """
        if not pool:
            await init_db()
            
        # Using cosine similarity with pgvector
        # This requires embeddings to be populated in the highlights table
        sql = """
        SELECT 
            h.id, 
            h.timestamp,
            h.description AS transcript,
            h.summary,
            v.filename AS video_filename,
            v.id AS video_id,
            1 - (h.embedding <=> $1::vector) AS similarity
        FROM 
            highlights h
        JOIN
            videos v ON h.video_id = v.id
        WHERE 
            h.embedding IS NOT NULL
        ORDER BY 
            h.embedding <=> $1::vector
        LIMIT $2
        """
        
        try:
            async with pool.acquire() as conn:
                # Check if embeddings exist in the database
                has_embeddings = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM highlights WHERE embedding IS NOT NULL LIMIT 1)"
                )
                
                if not has_embeddings:
                    logger.warning("No embeddings found in database, falling back to text search")
                    # Fallback to text-based search if no embeddings are available
                    query_text = "converted from embedding"  # Placeholder
                    return await Database.get_highlights_by_query(query_text, limit)
                
                rows = await conn.fetch(sql, query_embedding, limit)
                
                results = [
                    {
                        "id": row["id"],
                        "timestamp_start": row["timestamp"],
                        "timestamp_end": row["timestamp"] + 10.0,  # Estimate
                        "transcript": row["transcript"],
                        "summary": row["summary"],
                        "video_id": row["video_id"],
                        "video_filename": row["video_filename"],
                        "relevance": float(row["similarity"])
                    }
                    for row in rows
                ]
                
                return results
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            # Fallback to text-based search if vector search fails
            query_text = "fallback from vector search"  # Placeholder
            return await Database.get_highlights_by_query(query_text, limit)
