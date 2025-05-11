import os
import logging
import json
import re
import google.generativeai as genai
import cv2
import base64
import numpy as np
from ..config import LLM_CONFIG

class LLMService:
    def __init__(self):
        """Initialize the LLM service with Google's Generative AI"""
        if not LLM_CONFIG.get('api_key'):
            raise ValueError("Google API key is not set. Please set the GOOGLE_API_KEY environment variable.")
        
        # Configure the generative AI service
        genai.configure(api_key=LLM_CONFIG['api_key'])
        self.model_name = LLM_CONFIG['model']
        
        try:
            # Initialize the generative model
            self.model = genai.GenerativeModel(self.model_name)
            logging.info(f"LLM service initialized with model: {self.model_name}")
        except Exception as e:
            logging.error(f"Error initializing LLM service: {e}")
            raise
    
    def generate_highlight_description(self, frames, transcript, start_time, end_time):
        """
        Generate a detailed description of a video highlight using the LLM
        
        Args:
            frames (list): List of frames from the highlight
            transcript (str): Transcribed speech from the highlight
            start_time (float): Start time of the highlight
            end_time (float): End time of the highlight
            
        Returns:
            dict: Dictionary containing description and summary
        """
        # Format the prompt
        system_prompt = """
        You are a video analysis assistant that generates detailed descriptions of video highlights.
        
        Analyze the provided frames and transcript to create:
        1. A detailed description of what's happening in the highlight segment
        2. A concise summary highlighting the most important elements
        
        Focus on:
        - Key objects, people, and actions visible in the frames
        - Important speech content from the transcript
        - The overall context and significance of this moment
        
        Return your analysis in JSON format with two fields:
        - "description": A detailed paragraph (100-150 words) describing the highlight
        - "summary": A concise summary (25-35 words) of the key moment
        """
        
        # Convert frames to base64 for inclusion in the prompt
        frame_descriptions = []
        
        # Select up to 3 representative frames to avoid exceeding context limits
        selected_frames = frames[:min(3, len(frames))]
        
        for i, frame in enumerate(selected_frames):
            # Convert frame to RGB format
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize frame to reduce size while maintaining aspect ratio
            height, width = frame_rgb.shape[:2]
            max_dimension = 512
            
            if height > max_dimension or width > max_dimension:
                scale = max_dimension / max(height, width)
                new_height = int(height * scale)
                new_width = int(width * scale)
                frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
            
            # Create frame description
            frame_descriptions.append(f"Frame {i+1} - At approximately {start_time + (i * ((end_time - start_time) / len(selected_frames))):.2f} seconds")
        
        # Create the user prompt
        user_prompt = f"""
        VIDEO HIGHLIGHT ANALYSIS (Time: {start_time:.2f}s to {end_time:.2f}s)
        
        TRANSCRIPT:
        {transcript if transcript else '[No speech detected]'}
        
        FRAMES:
        {chr(10).join(frame_descriptions)}
        
        Based on these frames and transcript, please provide a detailed description and summary of this video highlight.
        """
        
        try:
            # Prepare the images for the model
            image_parts = []
            for frame in selected_frames:
                # Convert frame to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to reduce size
                height, width = frame_rgb.shape[:2]
                max_dimension = 512
                if height > max_dimension or width > max_dimension:
                    scale = max_dimension / max(height, width)
                    new_height = int(height * scale)
                    new_width = int(width * scale)
                    frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
                
                # Encode frame as JPEG bytes
                _, buffer = cv2.imencode('.jpg', frame_rgb)
                image_bytes = buffer.tobytes()
                
                # Add to image parts
                image_parts.append({
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                })
            
            # Create generation config
            generation_config = {
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            # Create the parts for the multi-modal message
            parts = [
                {"text": system_prompt + "\n\n" + user_prompt}
            ]
            
            # Add the image parts
            for img in image_parts:
                parts.append(img)
            
            # Generate response from LLM
            response = self.model.generate_content(
                parts,
                generation_config=generation_config
            )
            
            # Parse the response
            content = response.text.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Also try without markdown code blocks
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: create a structured result
                logging.warning("Failed to parse JSON response from LLM, creating structured response manually")
                result = {
                    "description": content[:500],  # Use first 500 chars as description
                    "summary": content[:100]       # Use first 100 chars as summary
                }
            
            return result
            
        except Exception as e:
            logging.error(f"Error generating highlight description: {e}")
            # Return a default response in case of error
            return {
                "description": f"Highlight from {start_time:.2f}s to {end_time:.2f}s. " + 
                              (f"Transcript: {transcript[:100]}..." if transcript else "No transcript available."),
                "summary": f"Video segment from {start_time:.2f}s to {end_time:.2f}s"
            }