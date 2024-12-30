# Importing libraries
import streamlit as st
import speech_recognition as sr
import time
from pydub import AudioSegment
import io
import os
import google.generativeai as genai
import json
from pathlib import Path

# Setting Webpage Configurations
st.set_page_config(page_icon="🎤", page_title="Speech to Text", layout="wide")

# Configure Gemini API
genai.configure(api_key='AIzaSyC1qf-a4Ce5GxO1Z7Ow5dbSdYtQSuTQuFw')  # Replace with your actual API key
model = genai.GenerativeModel('gemini-1.5-flash')  # Using the latest model

st.title(":rainbow[Speech to Text]🔊")

st.divider() 

# Initialize the recognizer
recognizer = sr.Recognizer()

# Define storage file path
STORAGE_FILE = "transcription_data.json"

# Function to load data from storage
def load_stored_data():
    try:
        if Path(STORAGE_FILE).exists():
            with open(STORAGE_FILE, 'r') as f:
                data = json.load(f)
                return data
        return {'transcriptions': [], 'ai_responses': {}, 'default_prompt': "Add a title, Correct all grammatical errors and rewrite in a clear, concise and professional manner:\n[The Transcription]"}
    except Exception as e:
        st.error(f"Error loading stored data: {e}")
        return {'transcriptions': [], 'ai_responses': {}, 'default_prompt': "Add a title, Correct all grammatical errors and rewrite in a clear, concise and professional manner:\n[The Transcription]"}

# Function to save data to storage
def save_stored_data():
    try:
        data = {
            'transcriptions': st.session_state.transcriptions,
            'ai_responses': st.session_state.ai_responses,
            'default_prompt': st.session_state.default_prompt
        }
        with open(STORAGE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error saving data: {e}")

# Initialize all session states from stored data
stored_data = load_stored_data()
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcriptions' not in st.session_state:
    st.session_state.transcriptions = stored_data['transcriptions']
if 'ai_responses' not in st.session_state:
    st.session_state.ai_responses = stored_data['ai_responses']
if 'default_prompt' not in st.session_state:
    st.session_state.default_prompt = stored_data['default_prompt']

# Create two columns for microphone and file upload
col1, col2 = st.columns(2)

with col1:
    st.subheader("Record Audio")
    # Toggle recording state
    if st.button('🎤 ' + ('Stop Recording' if st.session_state.recording else 'Start Recording')):
        st.session_state.recording = not st.session_state.recording

    # Capture and process audio while recording is active
    if st.session_state.recording:
        with sr.Microphone() as source:
            st.caption("Recording... Click 'Stop Recording' when finished")
            try:
                audio = recognizer.record(source, duration=20)
                with st.spinner('Transcribing...'):
                    text = recognizer.recognize_google(audio)
                    st.session_state.transcriptions.append(text)
                    save_stored_data()  # Save after adding new transcription
            except sr.UnknownValueError:
                st.error("Sorry, I could not understand what you said.")
            except sr.RequestError as e:
                st.error(f"Error connecting to the recognition service: {e}")

with col2:
    st.subheader("Upload Audio")
    uploaded_file = st.file_uploader("Choose an audio file", type=['wav', 'mp3', 'm4a'])
    
    if uploaded_file is not None:
        if st.button("Transcribe Audio File"):
            with st.spinner('Transcribing uploaded audio...'):
                try:
                    # Save the uploaded file temporarily
                    bytes_data = uploaded_file.read()
                    temp_filename = "temp_audio"
                    
                    # Convert and save audio to WAV format if needed
                    if uploaded_file.type == "audio/mp3":
                        audio = AudioSegment.from_mp3(io.BytesIO(bytes_data))
                        audio.export(f"{temp_filename}.wav", format="wav")
                    elif uploaded_file.type == "audio/x-m4a":
                        audio = AudioSegment.from_file(io.BytesIO(bytes_data), format="m4a")
                        audio.export(f"{temp_filename}.wav", format="wav")
                    else:  # WAV file
                        with open(f"{temp_filename}.wav", "wb") as f:
                            f.write(bytes_data)

                    # Transcribe the audio file
                    with sr.AudioFile(f"{temp_filename}.wav") as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                        st.session_state.transcriptions.append(text)
                    
                    # Clean up temporary file
                    if os.path.exists(f"{temp_filename}.wav"):
                        os.remove(f"{temp_filename}.wav")
                        
                except Exception as e:
                    st.error(f"Error processing audio: {str(e)}")

st.divider()

# Display all transcriptions with copy and remove buttons
if st.session_state.transcriptions:
    st.write("### Transcriptions:")
    for i, text in enumerate(st.session_state.transcriptions):
        col1, col2, col3, col4 = st.columns([0.7, 0.1, 0.1, 0.1])
        with col1:
            st.info(text)
        with col2:
            if st.button('🤖', key=f'ai_{i}'):
                with st.spinner('AI is thinking...'):
                    response = model.generate_content(text)
                    st.session_state.ai_responses[i] = response.text
        with col3:
            if st.button('📋', key=f'copy_{i}'):
                st.write('Copied!')
                st.code(text)
        with col4:
            if st.button('🗑️', key=f'remove_{i}'):
                st.session_state.transcriptions.pop(i)
                if i in st.session_state.ai_responses:
                    del st.session_state.ai_responses[i]
                save_stored_data()  # Save after removing
                st.rerun()
        
        # Display AI response if it exists for this transcription
        if i in st.session_state.ai_responses:
            with st.expander("AI Response", expanded=True):
                st.write(st.session_state.ai_responses[i])

# Add a section to set default prompt
with st.sidebar:
    st.write("### AI Settings")
    new_prompt = st.text_area(
        "Set Default AI Prompt",
        value=st.session_state.default_prompt,
        help="This prompt will be used as the default for all AI interactions."
    )
    if new_prompt != st.session_state.default_prompt:
        st.session_state.default_prompt = new_prompt
        save_stored_data()  # Save after updating prompt

st.divider()



