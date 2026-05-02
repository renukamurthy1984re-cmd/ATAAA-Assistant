# -*- coding: utf-8 -*-
import streamlit as st
from gtts import gTTS
import base64
from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import json
import requests
from io import BytesIO
import streamlit.components.v1 as components
import math
import io
import numpy as np
import os
import pypdf
import time  # Added for retry logic
from PIL import Image
import ast

# --- 1. THE BRAIN ---
client = genai.Client(
    api_key=st.secrets["GOOGLE_API_KEY"],
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,             # Try up to 5 times
            initial_delay=2.0,      # Start with a 2-second wait
            max_delay=60.0,         # Don't wait more than a minute
            http_status_codes=[503] # Specifically retry on 503 errors
        )
    )
)

# --- 2. APP CONFIG ---
st.set_page_config(page_title="ATAAA-AI (All Time Anything Anywhere Assistant)", layout="wide")

IMAGE_URL = "https://github.com/rajamkumar20082006-blip/ATAA-Hub-Pro/blob/main/RG.jpg?raw=true"
BHEEM_SONG = "https://www.soundboard.com/handler/DownLoadTrack.ashx?cliptitle=Chhota+Bheem+Theme&filename=24/244337-43400a42-7067-4e0d-8b0d-77341e975765.mp3"
BHEEM_LOGO = "https://i.pinimg.com/originals/f3/8d/e7/f38de733220078044704040a469a7177.png"

if 'ata_quiz_memory' not in st.session_state:
    st.session_state.ata_quiz_memory = {}

# Initialize Quiz State Variables
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = []
if 'current_q_index' not in st.session_state: st.session_state.current_q_index = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'quiz_submitted' not in st.session_state: st.session_state.quiz_submitted = False
if 'selected_option' not in st.session_state: st.session_state.selected_option = None
if 'step' not in st.session_state: st.session_state.step = "WELCOME"
if 'user_data' not in st.session_state: 
    st.session_state.user_data = {"name": "", "lang": "en", "voice_type": "Normal", "gang": "Normal", "score": 0}
if 'current_solution' not in st.session_state: st.session_state.current_solution = ""
if 'show_hero' not in st.session_state: st.session_state.show_hero = False

# --- 3. VOICE ENGINE ---
def play_ata_voice(text):
    gang = st.session_state.user_data['gang']
    name = st.session_state.user_data['name']
    lang = st.session_state.user_data['lang']
    prefix, suffix = "", ""
    if gang == "Chhotta Bheem Gang":
        prefix = f"Bheem here! Ladoo power! {name}, "
        suffix = " Let's go to Dholakpur!"
    elif gang == "MotuPatulu Crew":
        prefix = f"Motu here! Khaali pet dimaag ki batti nahi jalti! {name}, "
        suffix = " Where is my Samosa?"
    elif gang == "Little Singham":
        prefix = "Ata maajhi satakli! Little Singham here! "
        suffix = " Jai Hind!"
    try:
        tts = gTTS(text=f"{prefix} {text} {suffix}", lang=lang)
        tts_fp = io.BytesIO()
        tts.write_to_fp(tts_fp)
        b64 = base64.b64encode(tts_fp.getvalue()).decode()
        st.markdown(f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">', unsafe_allow_html=True)
    except:
        st.info("Preparing voice...")

# --- 4. THE SCREENS ---
if st.session_state.step == "WELCOME":
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 70px;'>ATAA</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(IMAGE_URL, use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>HELLO BUDDY</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>WELCOME TO ATAA: THE AI Powered Study Assistant</h3>", unsafe_allow_html=True)
    if st.button("🏆 Let's Win This Academic Year!", use_container_width=True, key="welcome_btn"):
        st.session_state.step = "DETAILS"
        st.rerun()

elif st.session_state.step == "DETAILS":
    st.title("Student Details")
    st.session_state.user_data['name'] = st.text_input("Enter Your Name")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("SELECT TAMIL LANGUAGE", use_container_width=True, key="lang_ta"): st.session_state.user_data['lang'] = 'ta'
    with col_b:
        if st.button("SELECT ENGLISH LANGUAGE", use_container_width=True, key="lang_en"): st.session_state.user_data['lang'] = 'en'
    
    v_type = st.radio("Choose Voice Mode:", ["NORMAL VOICE", "SELECT CARTOON VOICE"])
    if v_type == "SELECT CARTOON VOICE":
        st.session_state.user_data['voice_type'] = "Cartoon"
        st.session_state.user_data['gang'] = st.selectbox("Pick your Hero Gang:", ["Chhotta Bheem Gang", "MotuPatulu Crew", "Little Singham"])
    
    if st.button("Get Started", use_container_width=True, key="start_btn"):
        st.session_state.step = "AI_GEN"
        st.rerun()

elif st.session_state.step == "AI_GEN":
    st.header(f"ATAA Hub - {st.session_state.user_data['name']}")
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ Text Search", "📸 Camera", "🎧 Listening to Notes", "👑sports"])
    
    with tab1:
        user_input = st.text_area("Type your question here:", height=150, key="t1_input")
        if st.button("✨ Get Step-by-Step Answer", use_container_width=True, key="t1_btn"):
            if user_input:
                with st.spinner("ATAA is thinking..."):
                    max_retries = 3
                    for i in range(max_retries):
                        try:
                            models_list = [m.name for m in client.models.list()]
                            best_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models_list else models_list[0]
                            lang_name = "Tamil" if st.session_state.user_data['lang'] == 'ta' else "English"
                            response = client.models.generate_content(
                                model=best_model,
                                contents=f"Explain in simple step-by-step points in {lang_name}: {user_input}"
                            )
                            st.session_state.current_solution = response.text
                            st.success("Answer Ready!")
                            break 
                        except Exception as e:
                            if "503" in str(e) and i < max_retries - 1:
                                st.warning(f"Server busy. Retrying in {i+2} seconds...")
                                time.sleep(i + 2)
                            else:
                                st.error(f"Brain Error: {e}")

    with tab2:
        uploaded_img = st.file_uploader("Upload a photo of your book/homework", type=['jpg', 'jpeg', 'png'], key="t2_upload")
        if uploaded_img:
            st.image(uploaded_img, width=300)
            if st.button("✨ Solve from Image", use_container_width=True, key="t2_btn"):
                with st.spinner("ATAA is reading..."):
                    max_retries = 3
                    for i in range(max_retries):
                        try:
                            models_list = [m.name for m in client.models.list()]
                            best_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models_list else models_list[0]
                            lang_name = "Tamil" if st.session_state.user_data['lang'] == 'ta' else "English"
                            img = Image.open(uploaded_img)
                            response = client.models.generate_content(
                                model=best_model,
                                contents=[img, f"Read all text and solve this in simple step-by-step points in {lang_name}."]
                            )
                            st.session_state.current_solution = response.text
                            st.success("Answer Ready!")
                            break
                        except Exception as e:
                            if "503" in str(e) and i < max_retries - 1:
                                st.warning(f"Server busy. Retrying in {i+2} seconds...")
                                time.sleep(i + 2)
                            else:
                                st.error(f"Brain Error: {e}")

    with tab3:
        st.subheader("🎧 Listening to your Notes")
        st.info("I will read your notes aloud to help you memorize them!")
        listen_choice = st.radio("How should I read?", ["Read my Typed Text", "Read from my Image/Photo"])
        
        if listen_choice == "Read my Typed Text":
            input_text = st.text_area("Paste the passage here:", height=200, key="read_text_input")
            if st.button("🔊 Read My Notes Now", use_container_width=True):
                if input_text:
                    st.session_state.current_solution = input_text
                    play_ata_voice(input_text)
                else:
                    st.warning("Please paste some text first!")
        else:
            read_img = st.file_uploader("Upload the note image:", type=['jpg', 'jpeg', 'png'], key="read_img_input")
            
            if read_img:
                st.image(read_img, width=300)
                
                # BUTTON 1: Extract the text from the image
                if st.button("🔍 Step 1: Extract Text", use_container_width=True):
                    with st.spinner("Converting image to clear text..."):
                        try:
                            models_list = [m.name for m in client.models.list()]
                            best_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models_list else models_list[0]
                            lang_name = "Tamil" if st.session_state.user_data['lang'] == 'ta' else "English"
                            
                            img = Image.open(read_img)
                            response = client.models.generate_content(
                                model=best_model,
                                contents=[img, f"Read all text and explain it in simple step-by-step points in {lang_name}."]
                            )
                            
                            # Store the result in session state so it stays on screen
                            st.session_state.current_solution = response.text
                            st.success("Text Extracted successfully!")
                        except Exception as e:
                            st.error(f"Brain Error: {e}")

                # BUTTON 2: Show this button ONLY if text has been extracted
                if st.session_state.current_solution:
                    st.info("Text is ready! Click below to listen.")
                    if st.button("🔊 Step 2: Read My Notes Aloud", use_container_width=True):
                        play_ata_voice(st.session_state.current_solution)
    

    if st.session_state.current_solution:
        st.markdown("---")
        st.markdown(st.session_state.current_solution)
        if st.button("🔊 HEAR ANSWER", use_container_width=True, key="global_play"):
            play_ata_voice(st.session_state.current_solution)

        if st.button("Ready For Quizzes →", use_container_width=True, key="quiz_go"):
            st.session_state.step = "QUIZ"
            st.rerun()


elif st.session_state.step == "QUIZ":
    st.header("Daily Quiz - Test Your Knowledge!")
    st.subheader("Generate Quizzes From:")
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        quiz_text_input = st.text_area("Type Your Question/Context to Have Quizzes", height=150, key="quiz_text")
    
    with col_input2:
        quiz_img_input = st.file_uploader("Drag and Drop Files Here (Images)", type=['jpg', 'jpeg', 'png'], key="quiz_img")
        if quiz_img_input: st.image(quiz_img_input, width=150)

    if st.button("✨ Generate 15 Quizzes", use_container_width=True, key="gen_quiz_btn"):
        context_text = ""
        unique_quiz_id = ""

        if quiz_text_input:
            context_text = quiz_text_input
            unique_quiz_id = f"text_{hash(quiz_text_input)}"
        elif quiz_img_input:
            with st.spinner("ATAA is reading the image..."):
                max_retries = 3
                for i in range(max_retries):
                    try:
                        models_list = [m.name for m in client.models.list()]
                        best_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models_list else models_list[0]
                        img = Image.open(quiz_img_input)
                        response_text = client.models.generate_content(
                            model=best_model,
                            contents=[img, "Extract all textbook text from this image as context for a quiz."]
                        )
                        context_text = response_text.text
                        unique_quiz_id = f"img_{hash(response_text.text)}"
                        break
                    except Exception as e:
                        if "503" in str(e) and i < max_retries - 1:
                            st.warning(f"Server busy. Retrying in {i+2} seconds...")
                            time.sleep(i + 2)
                        else:
                            st.error(f"Error reading image: {e}")
                            st.stop()
        else:
            st.warning("Please provide either text or an image!")
            st.stop()

        if context_text:
            with st.spinner("ATAA is formulating 15 challenging questions..."):
                max_retries = 3
                for i in range(max_retries):
                    try:
                        models_list = [m.name for m in client.models.list()]
                        best_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models_list else models_list[0]
                        lang_name = "Tamil" if st.session_state.user_data['lang'] == 'ta' else "English"

                        quiz_prompt = f"""
                        You are a professional quiz maker.
                        Based ONLY on the Command, generate EXACTLY 15 multiple-choice questions in {lang_name}.
                        Format each question as a Python list of dictionaries:
                        [
                            {{
                                'question': 'The text of the question',
                                'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                                'correct_answer': 'Option X',
                                'hint': 'A simple, non-obvious clue for the correct answer'
                            }},
                            ... (Repeat for 15 questions)
                        ]
                        Context: {context_text[:15000]}
                        """
                        
                        response_quiz = client.models.generate_content(model=best_model, contents=quiz_prompt)
                        raw_text = response_quiz.text
                        if raw_text.startswith("```python") or raw_text.startswith("```json"):
                             raw_text = raw_text.replace("```python", "").replace("```json", "").replace("```", "")
                        
                        start_idx = raw_text.find('[')
                        end_idx = raw_text.rfind(']') + 1
                        if start_idx != -1 and end_idx != 0:
                            cleaned_list_str = raw_text[start_idx:end_idx].strip()
                            st.session_state.quiz_data = ast.literal_eval(cleaned_list_str)
                            st.session_state.ata_quiz_memory[unique_quiz_id] = st.session_state.quiz_data
                            st.session_state.current_q_index = 0
                            st.session_state.score = 0
                            st.session_state.quiz_submitted = False
                            st.success(f"15 questions generated in {lang_name}!")
                            st.rerun()
                            break
                        else:
                            st.error("Format Error: AI did not generate a proper list.")
                    except Exception as e:
                        if "503" in str(e) and i < max_retries - 1:
                            st.warning(f"Server busy. Retrying in {i+2} seconds...")
                            time.sleep(i + 2)
                        else:
                            st.error(f"Brain Error: {e}")
                            st.stop()

    if st.session_state.quiz_data:
        num_qs = len(st.session_state.quiz_data)
        current_idx = st.session_state.current_q_index
        q_data = st.session_state.quiz_data[current_idx]
        
        st.markdown("---")
        st.markdown(f"### Question {current_idx + 1} of {num_qs}")
        flashcard_html = f'''
        <div style="background-color: #f0f8ff; padding: 25px; border-radius: 20px; border: 3px solid #FF8C00; box-shadow: 5px 5px 15px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="color: #2f4f4f; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{q_data['question']}</h3>
        </div>
        '''
        st.markdown(flashcard_html, unsafe_allow_html=True)
        with st.expander("💡 Need a Hint?"):
            st.info(q_data['hint'])

        options = q_data['options']
        correct_ans = q_data['correct_answer']
        if st.session_state.quiz_submitted:
            for opt in options:
                is_correct = (opt == correct_ans)
                was_selected_by_user = (opt == st.session_state.selected_option)
                
                border_style = "1px solid #ccc"
                bg_color = "#FFFFFF"
                feedback_icon = ""

                if is_correct:
                    border_style = "3px solid #32CD32" 
                    bg_color = "#C8F7C5"
                    feedback_icon = " ✅"
                elif was_selected_by_user and not is_correct:
                    border_style = "3px solid #DC143C" 
                    bg_color = "#F7C5C5"
                    feedback_icon = " ❌"

                st.markdown(f'''
                    <div style="background:{bg_color}; border:{border_style}; padding:15px; border-radius:12px; color:black; margin-bottom:10px;">
                        <b>{opt}</b> {feedback_icon}
                    </div>
                ''', unsafe_allow_html=True)
            
            if st.session_state.selected_option == correct_ans:
                st.success("✅Supreme, Brilliant! That is the Correct Answer!")
            else:
                st.error(f"❌ Noble attempt! The correct answer was: **{correct_ans}**")

            if current_idx + 1 < num_qs:
                if st.button("Next Question →", use_container_width=True, key=f"next_q_{current_idx}"):
                    st.session_state.current_q_index += 1
                    st.session_state.quiz_submitted = False
                    st.session_state.selected_option = None
                    st.rerun()
            else:
                if st.button("Curious to See the Score", use_container_width=True, key="see_score_btn"):
                    st.session_state.step = "SCORE"
                    st.session_state.user_data['score'] = st.session_state.score 
                    st.rerun()
        else:
            with st.form(key=f"form_q_{current_idx}"):
                user_selection = st.radio("Choose the correct option:", options, key=f"q_radio_{current_idx}")
                submit_btn = st.form_submit_button("Submit Answer", type='primary')
                if submit_btn:
                    st.session_state.quiz_submitted = True
                    st.session_state.selected_option = user_selection
                    if user_selection == correct_ans:
                         st.session_state.score += 1 
                    st.rerun()

elif st.session_state.step == "SCORE":
    
    st.balloons()
    name = st.session_state.user_data['name']
    x = st.session_state.user_data['score']
    total_questions = 15
    
    appreciation_msg = ""
    appreciation_pic_url = ""

    if x == 15:
        appreciation_msg = "🏆 **Supreme! Brilliant!** A perfect score reflects your incredible dedication! You Deserve This! 🪄"
        appreciation_pic_url = "https://github.com/rajamkumar20082006-blip/ATAA-Hub-Pro/blob/main/GR.jpg?raw=true"        
    elif 10 <= x <= 14:
        appreciation_msg = "🔥 Legendary! Incredible! A single trophy leads to many more, guiding you straight to the crown👑"
        appreciation_pic_url = "https://github.com/rajamkumar20082006-blip/ATAA-Hub-Pro/blob/main/Trophy.jpg?raw=true"
    elif 5 <= x <= 9:
        appreciation_msg = "⭐ Fabulous! Majestic! An auspicious beginning! Such steady advancement is the vital bridge between potential and final victory! You’ve earned this—Enjoy!🍹"
        appreciation_pic_url = "https://github.com/rajamkumar20082006-blip/ATAA-Hub-Pro/blob/main/Cake.jpg?raw=true"
    elif 1 <= x <= 4:
        appreciation_msg = "💫 Noteworthy! Laudable! A rudimentary start is the inevitable precursor to a monumental achievement; Remain steadfast in your pursuit !"
        appreciation_pic_url = "https://github.com/rajamkumar20082006-blip/ATAA-Hub-Pro/blob/main/Ballons.jpg?raw=true"
    elif x == 0:
        appreciation_msg = "Noble attempt! Respectable try! Every expert was once a beginner who refused to quit; Refocus and Conquer the Next Challenge🎈"
        appreciation_pic_url = "https://github.com/rajamkumar20082006-blip/ATAA-Hub-Pro/blob/main/snow.jpg?raw=true"
    
    reward_html = f'''
    <div style="text-align: center; padding: 20px; font-family: 'Segoe UI', sans-serif;">
        <h1 style="color: #FF671F; font-size: 50px;">Congratulations, {name}!</h1>
        <h2 style="color: #09e809; font-size: 40px;">Your Score: {x} / {total_questions} Points</h2>
        <div style="font-size: 28px; color: #FF1493; font-weight: bold; margin-bottom: 40px;">{appreciation_msg}</div>
        <img src="{appreciation_pic_url}" style="width: 100%; max-width: 800px; border-radius: 30px; box-shadow: 0px 20px 40px rgba(0,0,0,0.5);">
    </div>
    '''
    st.markdown('<h1 style="color: #0e689c; text-align: center;">ATAAA Proficiency Honors</h1>', unsafe_allow_html=True)
    st.markdown(reward_html, unsafe_allow_html=True)
    
    if st.button("Start Again"):
        st.session_state.step = "WELCOME"
        st.rerun()
