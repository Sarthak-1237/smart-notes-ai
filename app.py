import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- PAGE SETUP ---
st.set_page_config(page_title="Apex Smart Notes AI", page_icon="📚")
st.title("📚 Apex Smart Notes & Lecture Summarizer")
st.write("Welcome, Apex Warrior! Upload any text-based PDF lecture/document, and our AI will break it down into a short summary, key bullet points, and revision flashcards in seconds.")

# --- SIDEBAR (Security & Team) ---
st.sidebar.markdown("# Your Secure Key")
st.sidebar.markdown("""
*Your Gemini API Key is stored safely as a secret. It is not visible to anyone.*
""")
api_key = st.secrets.get("GEMINI_API_KEY")

st.sidebar.markdown("---")
st.sidebar.markdown("# Apex Warriors Team")
st.sidebar.markdown("""
* Sarthak Ashok Gawnar
* Om Vitthal Nellawar
* Abhishek Ashwin Dawada
""")

# --- API KEY & MODEL SETUP ---
if api_key:
    genai.configure(api_key=api_key)
    
    try:
        # --- AUTO-DETECT MODEL (Defensive Hackathon Move) ---
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = valid_models[0] 
        for m in valid_models:
            if 'flash' in m:
                model_name = m
                break
        model = genai.GenerativeModel(model_name)

        # --- FILE UPLOADER ---
        uploaded_file = st.file_uploader("Upload your text-based PDF", type=["pdf"], help="Supports PDFs up to 50MB. Make sure the text is highlightable.")

        if uploaded_file is not None:
            # 🚨 DEFENSIVE CHECK 1: Ensure it's not a secret attack/wrong type
            if uploaded_file.type != "application/pdf":
                st.error("Error: This app only accepts PDF files.")
                st.stop()
            
            # 🚨 DEFENSIVE CHECK 2: Limit file size to 50MB (52,428,800 bytes)
            max_size_bytes = 52428800 
            if uploaded_file.size > max_size_bytes:
                st.error("Error: That file is too big! Please upload a PDF under 50MB.")
                st.stop()

            # --- PROCESS PDF ---
            if st.button("Generate Apex Study Guide"):
                with st.spinner("Processing PDF and generating notes... This takes about 10-30 seconds."):
                    try:
                        pdf_reader = PyPDF2.PdfReader(uploaded_file)
                        extracted_text = ""
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                extracted_text += text
                        
                        # --- SCANNED/BLANK PDF CHECK ---
                        if not extracted_text.strip():
                            st.error("Uh oh! We couldn't read any text from this PDF. It might be a scanned image or empty.")
                        
                        # --- TEXT IS GOOD - SEND TO GEMINI ---
                        else:
                            # 🚨 Limit extracted text to prevent overloading Gemini for very long documents
                            text_snippet = extracted_text[:20000] 
                            
                            prompt = f"""
                            You are an expert tutor preparing a student for an exam.
                            I am giving you text extracted from a lecture/document.
                            Please analyze it and provide:
                            1. A brief, high-level Summary of the entire topic.
                            2. A structured list of the most important Key Points in clear bullet points.
                            3. Generate exactly 5 specific Flashcards or Quiz Questions for active revision.
                            Here is the text:
                            {text_snippet}
                            """
                            
                            response = model.generate_content(prompt)
                            
                            st.success(f"Apex Study Guide Generated! (Powered by {model_name})")
                            st.markdown("---")
                            st.markdown(response.text)
                    
                    except Exception as pdf_error:
                        st.error(f"Error reading the PDF: {pdf_error}. The file might be corrupted.")
                        
    except Exception as e:
        st.error(f"An unexpected error occurred during setup: {e}")
else:
    st.info("API key configuration is required to use this app.")                with st.spinner("Reading PDF and generating notes... Please wait."):
                    
                    # --- READ THE PDF ---
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = ""
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text += text
                    
                    # --- CHECK IF IT IS BLANK/SCANNED ---
                    if not extracted_text.strip():
                        st.error("Uh oh! We couldn't read any text from this PDF. It might be a scanned image or empty.")
                    
                    # --- IF TEXT IS GOOD, GENERATE NOTES ---
                    else:
                        prompt = f"""
                        You are an expert tutor. I am giving you the text from a lecture/document. 
                        Please do the following:
                        1. Provide a short Summary of the overall topic.
                        2. Extract the most important Key Points (in bullet points).
                        3. Generate 3-5 Flashcards or Quiz Questions for revision.
                        
                        Here is the text:
                        {extracted_text}
                        """
                        
                        response = model.generate_content(prompt)
                        
                        st.success(f"Notes Generated Successfully! (Powered by {model_name})")
                        st.markdown(response.text)
                        
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please add your Gemini API Key to continue.")
