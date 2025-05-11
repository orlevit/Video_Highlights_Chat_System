import streamlit as st
import requests
import json
from datetime import datetime
import os

# API Configuration
API_URL = os.getenv("API_URL", "http://backend:8000")

# Page configuration
st.set_page_config(
    page_title="Video Highlights Chat",
    page_icon="🎬",
    layout="wide",
)

# App title and description
st.title("🎬 Video Highlights Chat")
st.markdown("""
Ask questions about video content and get answers based on the processed highlights!
""")

# Initialize session state for chat history if it doesn't exist
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to format the timestamp
def format_timestamp(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

# Function to send query to backend
def query_backend(question, max_results=5):
    try:
        response = requests.post(
            f"{API_URL}/api/chat/query",
            json={"query": question, "max_results": max_results},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error from API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to backend: {str(e)}")
        return None

# Chat input 
with st.container():
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_question = st.text_input("Ask about the video:", placeholder="What happened in the video?")
    
    with col2:
        max_results = st.number_input("Max results:", min_value=1, max_value=20, value=5)
    
    if st.button("Send"):
        if user_question:
            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # Get response from backend
            with st.spinner("Searching video highlights..."):
                response_data = query_backend(user_question, max_results)
            
            if response_data:
                # Add system message to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_data["answer"],
                    "highlights": response_data["highlights"],
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

# Display chat history
st.subheader("Chat History")
chat_container = st.container()

with chat_container:
    for message in st.session_state.chat_history:
        is_user = message["role"] == "user"
        
        # Create columns for avatar and message
        col1, col2 = st.columns([1, 9])
        
        with col1:
            # Avatar for user or assistant
            avatar = "👤" if is_user else "🎬"
            st.markdown(f"<h3>{avatar}</h3>", unsafe_allow_html=True)
        
        with col2:
            # Message container with appropriate styling
            if is_user:
                st.markdown(f"**You** ({message['timestamp']}):")
                st.markdown(message["content"])
            else:
                st.markdown(f"**Video Assistant** ({message['timestamp']}):")
                st.markdown(message["content"])
                
                # If there are highlights, show them in an expander
                if "highlights" in message and message["highlights"]:
                    with st.expander("Show detailed highlights"):
                        for idx, highlight in enumerate(message["highlights"]):
                            video_info = f" from {highlight.get('video_filename', 'video')}" if highlight.get('video_filename') else ""
                            st.markdown(f"**Highlight {idx+1}** (Time: {format_timestamp(highlight['timestamp_start'])} - {format_timestamp(highlight['timestamp_end'])}{video_info})")
                            
                            # Display highlight details in tabs
                            tab1, tab2 = st.tabs(["Summary", "Description"])
                            
                            with tab1:
                                st.markdown(highlight["summary"] if highlight["summary"] else "No summary available")
                            
                            with tab2:
                                st.markdown(highlight["transcript"])
                            
                            st.markdown("---")
        
        # Add a separator between messages
        st.markdown("---")

# Add a sidebar with information
with st.sidebar:
    st.subheader("About")
    st.markdown("""
    This application allows you to query video highlights stored in the database.
    
    The system will search for relevant moments in the video based on your questions
    and provide answers exclusively from the processed content.
    
    **How it works:**
    1. Ask a question about the video content
    2. The system searches the database for relevant highlights
    3. An answer is constructed from the matching highlights
    4. Expand the highlights section to see detailed information
    """)
