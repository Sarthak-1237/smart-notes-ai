import streamlit as st
import google.generativeai as genai
import PyPDF2
import sqlite3

# --- PAGE SETUP ---
st.set_page_config(page_title="Apex Smart Notes", page_icon="🚀", layout="centered")

# --- DATABASE SETUP (SQLite) ---
def init_db():
    conn = sqlite3.connect('apex_notes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            notes_content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_note_to_db(filename, content):
    conn = sqlite3.connect('apex_notes.db')
    c = conn.cursor()
    c.execute('INSERT INTO saved_notes (filename, notes_content) VALUES (?, ?)', (filename, content))
    conn.commit()
    conn.close()

def get_all_notes():
    conn = sqlite3.connect('apex_notes.db')
    c = conn.cursor()
    c.execute('SELECT filename, notes_content FROM saved_notes ORDER BY id DESC')
    data = c.fetchall()
    conn.close()
    return data

# Initialize the database as soon as the app starts
init_db()

# --- PREMIUM UI DESIGN (LIVE WALLPAPER) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(15, 23, 42, 0.85), rgba(30, 27, 75, 0.85)), url("https://media.giphy.com/media/xTiTnxpQ3ghPiB2Hp6/giphy.gif");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp > header {
        background-color: transparent !important;
    }
    
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #FF8F8F;
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(5px);
        transition: all 0.3s ease;
        padding: 20px;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: rgba(255, 255, 255, 0.15);
        border-color: #FF4B4B;
        transform: scale(1.01);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8F8F 100%);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 18px;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 75, 75, 0.5);
        color: white;
        border: none;
    }
    
    h1, h2, h3 { color: #FF8F8F !important; }
    
    .stAlert {
        border-radius: 12px;
        border-left: 5px solid #4CAF50;
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        color: white;
    }
    
    .stMarkdown p, .stMarkdown li { color: #E2E8F0 !important; }
    
    /* Style for the Expanders in the Vault */
    [data-testid="stExpander"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- MAIN HEADER ---
st.markdown("<h1 style='text-align: center;'>🚀 Apex Smart Notes</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #CBD5E1;'>AI-Powered Lecture Summarizer & Flashcard Generator ✨</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR (Security & Team) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135679.png", width=80) 
    st.markdown("### 🛡️ Your Secure Key")
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    st.markdown("---")
    st.markdown("### 👑 Apex Warriors")
    st.markdown("""
    * 👨‍💻 **Sarthak Ashok Gawnar**
    * 👨‍💻 **Om Vitthal Nellawar**
    * 👨‍💻 **Abhishek Ashwin Dawada**
    """)
    st.markdown("---")
    st.markdown("🔥 *Swarajya Hackfest 2026*")

# --- API KEY & APP LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    
    try:
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = valid_models[0] 
        for m in valid_models:
            if 'flash' in m:
                model_name = m
                break
        model = genai.GenerativeModel(model_name)

        # --- CREATE TABS ---
        tab1, tab2 = st.tabs(["📝 Generate Notes", "📚 My Saved Vault"])

        # ====== TAB 1: GENERATION ======
        with tab1:
            st.markdown("<p style='text-align: center; font-size: 16px;'>🎯 Drop your massive lecture PDFs below. Our AI tutor will instantly crush it down and <b>save it to your database.</b></p>", unsafe_allow_html=True)
            st.write("")
            uploaded_file = st.file_uploader("", type=["pdf"], help="Supports PDFs up to 50MB.")

            if uploaded_file is not None:
                if uploaded_file.type != "application/pdf":
                    st.error("🚨 Error: This app only accepts PDF files.")
                    st.stop()
                
                max_size_bytes = 52428800 
                if uploaded_file.size > max_size_bytes:
                    st.error("🚨 Error: That file is too big! Please upload a PDF under 50MB.")
                    st.stop()

                if st.button("✨ Generate & Save to Vault ✨"):
                    with st.spinner("🧠 AI is reading your PDF... Please wait a few seconds!"):
                        try:
                            pdf_reader = PyPDF2.PdfReader(uploaded_file)
                            extracted_text = ""
                            for page in pdf_reader.pages:
                                text = page.extract_text()
                                if text:
                                    extracted_text += text
                            
                            if not extracted_text.strip():
                                st.error("⚠️ Uh oh! We couldn't read any text from this PDF. It might be a scanned image or empty.")
                            else:
                                text_snippet = extracted_text[:20000] 
                                
                                prompt = f"""
                                You are an expert tutor preparing a student for an exam.
                                Please analyze the text and provide:
                                1. A brief Summary.
                                2. A structured list of Key Points.
                                3. Generate exactly 5 Flashcards.
                                Here is the text:
                                {text_snippet}
                                """
                                
                                response = model.generate_content(prompt)
                                
                                # --- DATABASE SAVE MAGIC ---
                                save_note_to_db(uploaded_file.name, response.text)
                                # ---------------------------
                                
                                st.success(f"✅ Apex Study Guide Generated and Saved to Vault! (Powered by {model_name})")
                                st.markdown("---")
                                st.markdown(response.text)
                                st.balloons() 
                        
                        except Exception as pdf_error:
                            st.error(f"❌ Error reading the PDF: {pdf_error}. The file might be corrupted.")

        # ====== TAB 2: THE DATABASE VAULT ======
        with tab2:
            st.markdown("<h3 style='color: white;'>🗄️ Your Saved AI Notes</h3>", unsafe_allow_html=True)
            st.write("All previously generated notes are stored securely in your local SQLite database.")
            
            saved_data = get_all_notes()
            
            if len(saved_data) == 0:
                st.info("Your vault is empty! Go generate some notes in the other tab.")
            else:
                for row in saved_data:
                    filename = row[0]
                    content = row[1]
                    # Create a clickable dropdown box for each saved note
                    with st.expander(f"📄 Notes from: {filename}"):
                        st.markdown(content)

    except Exception as e:
        st.error(f"❌ An unexpected error occurred during setup: {e}")
else:
    st.warning("⚠️ API key configuration is required to use this app.")
