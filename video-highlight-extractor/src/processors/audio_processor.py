import os
import logging
import tempfile
from pydub import AudioSegment
import speech_recognition as sr
from moviepy.editor import VideoFileClip

class AudioProcessor:
    def __init__(self):
        """Initialize the audio processor"""
        self.recognizer = sr.Recognizer()
    
    def extract_audio(self, video_path):
        """
        Extract audio from a video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Path to the extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            # Create temporary file for audio
            temp_audio_path = tempfile.mktemp(suffix='.wav')
            
            # Extract audio using moviepy
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(temp_audio_path, logger=None)
            
            logging.info(f"Extracted audio from {video_path} to {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            logging.error(f"Error extracting audio: {e}")
            return None
    
    def extract_audio_segment(self, video_path, start_time, end_time):
        """
        Extract audio segment from a video file for a specific time range
        
        Args:
            video_path (str): Path to the video file
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            
        Returns:
            str: Path to the extracted audio segment file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            # Create temporary file for audio segment
            temp_audio_path = tempfile.mktemp(suffix='.wav')
            
            # Extract audio segment using moviepy
            video = VideoFileClip(video_path)
            
            # Ensure times are within video bounds
            start_time = max(0, start_time)
            end_time = min(video.duration, end_time)
            
            audio_clip = video.subclip(start_time, end_time).audio
            audio_clip.write_audiofile(temp_audio_path, logger=None)
            
            logging.info(f"Extracted audio segment from {video_path} ({start_time}-{end_time}s) to {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            logging.error(f"Error extracting audio segment: {e}")
            return None
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe speech in an audio file
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Load audio file
            audio = AudioSegment.from_wav(audio_path)
            
            # Split audio into chunks if it's longer than 60 seconds
            # (SpeechRecognition works better with shorter audio)
            chunks = []
            if len(audio) > 60000:  # 60000ms = 60s
                chunk_size = 30000  # 30s chunks
                for i in range(0, len(audio), chunk_size):
                    chunks.append(audio[i:i+chunk_size])
            else:
                chunks = [audio]
            
            transcripts = []
            
            for i, chunk in enumerate(chunks):
                # Save chunk to temporary file
                chunk_path = tempfile.mktemp(suffix='.wav')
                chunk.export(chunk_path, format="wav")
                
                # Transcribe chunk
                with sr.AudioFile(chunk_path) as source:
                    audio_data = self.recognizer.record(source)
                    try:
                        text = self.recognizer.recognize_google(audio_data)
                        transcripts.append(text)
                    except sr.UnknownValueError:
                        logging.warning(f"Speech Recognition could not understand audio chunk {i+1}")
                    except sr.RequestError as e:
                        logging.error(f"Could not request results from Speech Recognition service: {e}")
                
                # Clean up temporary chunk file
                os.remove(chunk_path)
            
            # Combine transcripts
            full_transcript = " ".join(transcripts)
            
            logging.info(f"Transcribed audio: {audio_path[:50]}{'...' if len(audio_path) > 50 else ''}")
            return full_transcript
            
        except Exception as e:
            logging.error(f"Error transcribing audio: {e}")
            return ""
