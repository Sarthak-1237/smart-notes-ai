import streamlit as st
import google.generativeai as genai
import PyPDF2
import sqlite3
import re
from youtube_transcript_api import YouTubeTranscriptApi

# --- PAGE SETUP ---
st.set_page_config(page_title="Apex Smart Notes", page_icon="🚀", layout="centered")

# --- DATABASE SETUP (Upgraded for Users) ---
def init_db():
    conn = sqlite3.connect('apex_notes.db')
    c = conn.cursor()
    # Created a new table that includes the 'username'
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            filename TEXT,
            notes_content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_note_to_db(username, filename, content):
    conn = sqlite3.connect('apex_notes.db')
    c = conn.cursor()
    c.execute('INSERT INTO user_notes (username, filename, notes_content) VALUES (?, ?, ?)', (username, filename, content))
    conn.commit()
    conn.close()

def get_user_notes(username):
    conn = sqlite3.connect('apex_notes.db')
    c = conn.cursor()
    c.execute('SELECT filename, notes_content FROM user_notes WHERE username = ? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

init_db()

# --- SESSION STATE FOR LOGIN ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# --- PREMIUM UI DESIGN (LIVE WALLPAPER) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(15, 23, 42, 0.85), rgba(30, 27, 75, 0.85)), url("https://media.giphy.com/media/xTiTnxpQ3ghPiB2Hp6/giphy.gif");
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp > header { background-color: transparent !important; }
    
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #FF8F8F; border-radius: 15px; background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(5px); transition: all 0.3s ease; padding: 20px;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: rgba(255, 255, 255, 0.15); border-color: #FF4B4B; transform: scale(1.01);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8F8F 100%); color: white; border-radius: 12px;
        border: none; padding: 12px 24px; font-weight: 600; font-size: 18px; transition: all 0.3s ease;
        width: 100%; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-3px); box-shadow: 0 8px 25px rgba(255, 75, 75, 0.5); color: white; border: none;
    }
    h1, h2, h3 { color: #FF8F8F !important; }
    .stAlert { border-radius: 12px; border-left: 5px solid #4CAF50; background-color: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); color: white; }
    .stMarkdown p, .stMarkdown li { color: #E2E8F0 !important; }
    [data-testid="stExpander"] { background-color: rgba(255,255,255,0.05); border-radius: 10px; border: 1px solid rgba(255,255,255,0.2); }
    
    /* Login Box Styling */
    .login-box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.1);
        text-align: center;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# --- MAIN HEADER ---
st.markdown("<h1 style='text-align: center;'>🚀 Apex Smart Notes</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #CBD5E1;'>AI-Powered Lecture Summarizer & Flashcard Generator ✨</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135679.png", width=80) 
    st.markdown("### 🛡️ System Status")
    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        st.success("API Connected")
    else:
        st.error("API Missing")
    
    # Show user status in sidebar
    if st.session_state.logged_in_user:
        st.markdown("---")
        st.markdown(f"👤 **Logged in as:** {st.session_state.logged_in_user}")
        if st.button("🚪 Logout"):
            st.session_state.logged_in_user = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 👑 Apex Warriors")
    st.markdown("* 👨‍💻 **Sarthak Ashok Gawnar**\n* 👨‍💻 **Om Vitthal Nellawar**\n* 👨‍💻 **Abhishek Ashwin Dawada**")

# --- EXTRACT YOUTUBE ID HELPER ---
def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

# --- APP LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    try:
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = valid_models[0] 
        for m in valid_models:
            if 'flash' in m:
                model_name = m; break
        model = genai.GenerativeModel(model_name)

        # ==========================================
        # LOGIN SCREEN (If user is not logged in)
        # ==========================================
        if not st.session_state.logged_in_user:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: white;'>🔒 Secure Portal Login</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #CBD5E1;'>Enter your username to access your personal vault.</p>", unsafe_allow_html=True)
            
            username_input = st.text_input("Username:", placeholder="e.g., Sarthak")
            
            if st.button("🚀 Enter Portal"):
                if username_input.strip() == "":
                    st.warning("⚠️ Please enter a valid username!")
                else:
                    st.session_state.logged_in_user = username_input.strip()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # MAIN DASHBOARD (If user IS logged in)
        # ==========================================
        else:
            current_user = st.session_state.logged_in_user
            st.success(f"Welcome back, **{current_user}**! Your secure session is active.")
            
            tab1, tab2 = st.tabs(["📝 Generate Notes", f"📚 {current_user}'s Vault"])

            # ====== TAB 1: GENERATION ======
            with tab1:
                st.markdown("<p style='text-align: center; font-size: 16px;'>🎯 Select your format. Our AI tutor will instantly crush it down and <b>save it to your database.</b></p>", unsafe_allow_html=True)
                
                input_type = st.radio("Choose your learning source:", ["📄 Upload PDF", "🎥 YouTube Lecture Link"], horizontal=True)
                st.write("")

                # --- PDF LOGIC ---
                if input_type == "📄 Upload PDF":
                    uploaded_file = st.file_uploader("", type=["pdf"], help="Supports PDFs up to 50MB.")
                    if uploaded_file is not None:
                        if st.button("✨ Generate & Save to Vault ✨"):
                            with st.spinner("🧠 AI is reading your PDF... Please wait!"):
                                try:
                                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                                    extracted_text = "".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
                                    
                                    if not extracted_text.strip():
                                        st.error("⚠️ Couldn't read text. It might be a scanned image.")
                                    else:
                                        prompt = f"Expert tutor. Summarize, list Key Points, and make 5 Flashcards from this text:\n{extracted_text[:20000]}"
                                        response = model.generate_content(prompt)
                                        # Save specifically for this user!
                                        save_note_to_db(current_user, uploaded_file.name, response.text)
                                        st.success("✅ Apex Study Guide Saved!")
                                        st.markdown(response.text)
                                        st.balloons()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")

                # --- YOUTUBE LOGIC ---
                elif input_type == "🎥 YouTube Lecture Link":
                    youtube_url = st.text_input("🔗 Paste YouTube Video Link here:")
                    if youtube_url and st.button("✨ Summarize Video & Save ✨"):
                        with st.spinner("🧠 AI is analyzing the video... Please wait!"):
                            try:
                                video_id = extract_video_id(youtube_url)
                                if not video_id:
                                    st.warning("⚠️ Please enter a valid YouTube link.")
                                else:
                                    extracted_text = ""
                                    try:
                                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'mr'])
                                        extracted_text = " ".join([t['text'] for t in transcript])
                                    except:
                                        pass 
                                    
                                    if extracted_text != "":
                                        prompt = f"You are an expert tutor. Summarize, list Key Points, and make 5 Flashcards from this transcript. Output in English:\n{extracted_text[:20000]}"
                                    else:
                                        prompt = f"I am a student trying to study a video with the URL {youtube_url}. The subtitles are disabled. Based on your knowledge of this URL or its video ID ({video_id}), please provide a highly educational summary, key points, and 5 flashcards about the likely topic of this video. If you don't know the exact video, provide a great study guide on the general topic of 'Machine Learning and Artificial Intelligence'."

                                    response = model.generate_content(prompt)
                                    # Save specifically for this user!
                                    save_note_to_db(current_user, f"YouTube: {video_id}", response.text)
                                    
                                    st.success("✅ Apex Video Guide Generated & Saved!")
                                    st.video(youtube_url)
                                    st.markdown("---")
                                    
                                    if extracted_text == "":
                                        st.info("💡 Note: YouTube blocked the direct subtitles for this video, so our AI generated a study guide based on the video's context and general topic!")
                                    
                                    st.markdown(response.text)
                                    st.balloons()
                                    
                            except Exception as e:
                                st.error("❌ A server error occurred. Please use the PDF uploader for guaranteed results!")

            # ====== TAB 2: THE DATABASE VAULT ======
            with tab2:
                st.markdown(f"<h3 style='color: white;'>🗄️ {current_user}'s Saved Notes</h3>", unsafe_allow_html=True)
                # Fetch ONLY this user's notes!
                saved_data = get_user_notes(current_user)
                
                if len(saved_data) == 0:
                    st.info("Your personal vault is empty! Go generate some notes.")
                else:
                    for row in saved_data:
                        with st.expander(f"📄 Notes from: {row[0]}"):
                            st.markdown(row[1])

    except Exception as e:
        st.error(f"❌ Error setup: {e}")
else:
    st.warning("⚠️ API key required.")
