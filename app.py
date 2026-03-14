import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- PAGE SETUP ---
st.set_page_config(page_title="Smart Notes AI", page_icon="📚")
st.title("📚 AI Smart Notes & Lecture Summarizer")
st.write("Upload a PDF lecture or document, and AI will generate a summary, key points, and flashcards instantly.")

# --- API KEY SETUP ---
api_key = st.secrets.get("GEMINI_API_KEY") 

if not api_key:
    st.sidebar.warning("API key required for local testing.")
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- FILE UPLOADER ---
    uploaded_file = st.file_uploader("Upload your lecture PDF", type=["pdf"])

    if uploaded_file is not None:
        if st.button("Generate Smart Notes"):
            with st.spinner("Reading PDF and generating notes... Please wait."):
                try:
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = ""
                    for page in pdf_reader.pages:
                        extracted_text += page.extract_text()
                    
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
                    
                    st.success("Notes Generated Successfully!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
else:
    st.info("Please add your Gemini API Key to continue.")
  
