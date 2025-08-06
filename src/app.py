# app.py

import streamlit as st
from streamlit_mic_recorder import mic_recorder
import logging
from services import GoogleCloudServices
import config

st.set_page_config(layout="wide", page_title="AI Voice Translator")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
st.title("AI Real-time Voice Translator")
st.markdown("Select your languages, choose a voice, record your speech, and get the translation!")
@st.cache_resource
def load_google_services():
    try:
        return GoogleCloudServices(credentials=config.CREDENTIALS)
    except Exception as e:
        st.error(f"Failed to load Google Cloud services. Please check your .env configuration. Error: {e}")
        return None
services = load_google_services()
if not services:
    st.stop()

if 'original_text' not in st.session_state:
    st.session_state.original_text = ""
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""
if 'translated_audio' not in st.session_state:
    st.session_state.translated_audio = None

# --- SIDEBAR: CONTROL AND SETTINGS ---
st.sidebar.header("Translation Settings")

# --- WIDGET 1 & 2: LANGUAGE OPTION ---
source_language_names = list(config.SUPPORTED_SOURCE_LANGUAGES.keys())
selected_source_language_name = st.sidebar.selectbox("1. Select Your Source Language:", options=source_language_names, index=0)
source_lang_code = config.SUPPORTED_SOURCE_LANGUAGES[selected_source_language_name]
st.sidebar.markdown("---")
target_language_names = list(config.SUPPORTED_LANGUAGES.keys())
selected_target_language_name = st.sidebar.selectbox("2. Select Target Language:", options=target_language_names)
lang_info = config.SUPPORTED_LANGUAGES[selected_target_language_name]
target_lang_code = lang_info["lang_code"]
voices = lang_info["voices"]

# --- WIDGET 3: VOICE OPTION ---
voice_names = list(voices.keys())
selected_voice_name = st.sidebar.selectbox("3. Select Voice Type:", options=voice_names)
target_voice_code = voices[selected_voice_name]

# --- WIDGET 4: TOGGLE TEXT-TO-SPEECH ---
st.sidebar.markdown("---")
# Nilai default 'True' berarti fitur ini aktif saat pertama kali dibuka
enable_tts = st.sidebar.toggle("Enable Text-to-Speech Output", value=True)


# --- MAIN UI & LOGIC ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Speak in: **{selected_source_language_name}**")
    audio_info = mic_recorder(start_prompt="🔴 Click to Record", stop_prompt="⏹️ Click to Stop", just_once=False, use_container_width=True, key='recorder')

with col2:
    st.subheader(f"Translation to: **{selected_target_language_name}**")
    
    if audio_info:
        audio_bytes = audio_info['bytes']

        st.session_state.translated_audio = None 
        
        with st.status(f"Translating your voice...", expanded=True) as status:
            status.write("Step 1: Transcribing your voice to text...")
            original_text = services.transcribe_audio(audio_bytes=audio_bytes, language_code=source_lang_code)

            if original_text:
                st.session_state.original_text = original_text
                status.update(label="✅ Transcription successful!", state="running")
                
                status.write(f"Step 2: Translating text to **{selected_target_language_name}**...")
                translated_text = services.translate_text(text=original_text, target_language=target_lang_code)

                if translated_text:
                    st.session_state.translated_text = translated_text
                    
                    if enable_tts:
                        status.update(label="✅ Translation successful!", state="running")
                        status.write(f"Step 3: Synthesizing audio with **{selected_voice_name}** voice...")
                        
                        translated_audio = services.text_to_speech(text=translated_text, voice_code=target_voice_code)
                        
                        if translated_audio:
                            st.session_state.translated_audio = translated_audio
                            status.update(label="🎉 Process Complete!", state="complete", expanded=False)
                        else:
                            status.update(label="❌ Failed to synthesize audio.", state="error", expanded=True)
                    else:
                        status.update(label="🎉 Translation Complete! (TTS is off)", state="complete", expanded=False)
                
                else:
                    st.session_state.translated_text = ""
                    status.update(label="❌ Failed to translate text.", state="error", expanded=True)
            else:
                st.session_state.original_text = ""
                st.session_state.translated_text = ""
                status.update(label="❌ Could not detect speech.", state="error", expanded=True)

    if st.session_state.original_text:
        st.info(f"**Original Text:**\n\n{st.session_state.original_text}")
    if st.session_state.translated_text:
        st.success(f"**Translated Text:**\n\n{st.session_state.translated_text}")
    if st.session_state.translated_audio:
        st.audio(st.session_state.translated_audio, format="audio/wav", autoplay=True)