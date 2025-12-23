import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Catamaran KYC", layout="wide", page_icon="📑")

# Custom CSS for UI Enhancement
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .centered-title {
        text-align: center;
        color: #004a99;
        font-size: 42px;
        font-weight: 800;
        margin-top: -20px;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #004a99;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #003366;
        color: #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
try:
    # Securely fetch the API key from Streamlit Cloud Secrets
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ API Key not found. Please check your Streamlit Cloud Secrets configuration.")

# Use the Gemini 1.5 Pro model for deep reasoning
model = genai.GenerativeModel("gemini-1.5-pro")


# --- 3. RESOURCE LOADING ---
@st.cache_data
def load_resources():
    # Load the 2,000+ company list
    try:
        with open("companies.txt", "r", encoding="utf-8") as f:
            list_comp = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        list_comp = ["Reliance Industries", "TCS", "HDFC Bank"]

    # Load the 5-page detailed prompt
    try:
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
    except FileNotFoundError:
        prompt = "Perform a KYC on {company_name}."

    return list_comp, prompt


companies, prompt_template = load_resources()

# --- 4. CENTERED BRANDING ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

# --- 5. INPUT DASHBOARD ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("🔍 Entity Selection")
    entity_type = st.radio("Select Category:", ["Listed Company", "Private Company"], horizontal=True)

    if entity_type == "Listed Company":
        target = st.selectbox("Search Indian Listed Universe:", options=companies, index=None,
                              placeholder="Start typing name...")
    else:
        target = st.text_input("Enter Private Company Name:", placeholder="Full legal name of the entity")

with col2:
    st.subheader("📂 Supporting Documents")
    # UPDATED: Multiple file support enabled
    uploaded_files = st.file_uploader(
        "Upload Reports, DRHPs, or Financial Statements:",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

st.divider()

# --- 6. GENERATION LOGIC ---
if target:
    if st.button(f"🚀 Generate Deep Intelligence Report for {target}"):
        with st.status(f"Analyzing {target}...", expanded=True) as status:

            # Prepare contextual components
            # Using .replace() instead of .format() to avoid KeyErrors with 5-page prompts
            final_prompt = prompt_template.replace("{company_name}", target)
            contents = [final_prompt]

            # Process multiple files into the AI request
            if uploaded_files:
                status.write(f"Feeding {len(uploaded_files)} documents to Gemini...")
                for uploaded_file in uploaded_files:
                    contents.append({
                        "mime_type": uploaded_file.type,
                        "data": uploaded_file.getvalue()
                    })

            try:
                status.write("Synthesizing research modules...")
                response = model.generate_content(contents)

                # Store in session state so result persists for the download button
                st.session_state["kyc_note"] = response.text
                st.session_state["target_name"] = target
                status.update(label="Analysis Complete!", state="complete")
            except Exception as e:
                st.error(f"Generation Error: {e}")

# --- 7. OUTPUT & DOWNLOAD ---
if "kyc_note" in st.session_state:
    res_col1, res_col2 = st.columns([4, 1])

    with res_col1:
        st.success(f"Generated KYC for {st.session_state['target_name']}")

    with res_col2:
        # Create PDF using fpdf2
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, f"Catamaran KYC Report: {st.session_state['target_name']}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("helvetica", size=11)
        # Using multi_cell to handle long text wrap automatically
        pdf.multi_cell(0, 8, st.session_state["kyc_note"])

        # Binary output for download button
        pdf_bytes = pdf.output()

        st.download_button(
            label="📥 Download as PDF",
            data=pdf_bytes,
            file_name=f"{st.session_state['target_name']}_KYC.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown(st.session_state["kyc_note"])