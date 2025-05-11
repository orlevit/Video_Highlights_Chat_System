import logging
import numpy as np
import google.generativeai as genai

from ..config import LLM_CONFIG

class EmbeddingService:
    def __init__(self):
        """Initialize the embedding service with Google's Generative AI"""
        if not LLM_CONFIG.get('api_key'):
            raise ValueError("Google API key is not set. Please set the GOOGLE_API_KEY environment variable.")
        
        # Configure the generative AI service
        genai.configure(api_key=LLM_CONFIG['api_key'])
        
        try:
            # Initialize the embedding model with the correct prefix format
            self.model_name = "models/embedding-001"
            logging.info(f"Embedding service initialized with model: {self.model_name}")
        except Exception as e:
            logging.error(f"Error initializing embedding service: {e}")
            raise
    
    def get_embedding(self, text):
        """
        Generate embedding vector for the given text
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            numpy.ndarray: Embedding vector
        """
        try:
            # Create the embedding task with the correct model name format
            embedding_task = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            
            # Get the embedding values
            embedding = embedding_task["embedding"]
            
            # Convert to numpy array
            embedding_array = np.array(embedding, dtype=np.float32)
            
            return embedding_array
            
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            # Return a zero vector of the expected dimension in case of error
            return np.zeros(LLM_CONFIG['embedding_dimension'], dtype=np.float32)
    
    def get_highlight_embedding(self, description, summary):
        """
        Generate embedding vector for a highlight by combining description and summary
        
        Args:
            description (str): Detailed description of the highlight
            summary (str): Short summary of the highlight
            
        Returns:
            numpy.ndarray: Embedding vector
        """
        # Combine description and summary for better embedding
        combined_text = f"{summary} {description}"
        return self.get_embedding(combined_text)