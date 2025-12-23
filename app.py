import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import io

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Catamaran KYC note generator", layout="wide")

# Setup Gemini API (Securely via Secrets)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API Key not found. Please add GEMINI_API_KEY to your Secrets.")

# Change this to your preferred model (e.g., gemini-1.5-pro or gemini-2.5-flash)
MODEL_ID = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_ID)


# --- 2. DATA LOADING ---
def load_data():
    try:
        with open("companies.txt", "r", encoding="utf-8") as f:
            public_companies = [line.strip() for line in f.readlines()]
    except:
        public_companies = ["Reliance Industries", "TCS", "HDFC Bank"]

    try:
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            template = f.read()
    except:
        template = "Prepare a KYC for {company_name}."
    return public_companies, template


public_companies, prompt_template = load_data()


# --- 3. PDF GENERATOR HELPER ---
def generate_pdf(text, company_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"KYC Report: {company_name}", ln=True, align='C')
    pdf.ln(10)

    # Content
    pdf.set_font("Arial", size=12)
    # multi_cell handles line breaks and long text automatically
    pdf.multi_cell(0, 10, text)

    # Return as bytes
    return pdf.output(dest='S').encode('latin-1', 'replace')


# --- 4. USER INTERFACE ---
st.title("🇮🇳 Indian Company KYC Intelligence")

# Choice of Company Type
company_type = st.radio("Select Category:", ["Listed Company", "Private Company"])

if company_type == "Listed Company":
    selected_company = st.selectbox("Search listed company:", options=public_companies, index=None)
else:
    selected_company = st.text_input("Enter private company name:")

# NEW: File Uploader Component
st.subheader("📁 Supporting Documents")
uploaded_file = st.file_uploader("Upload DRHP, Financials, or Reports (PDF/JPG/PNG):",
                                 type=["pdf", "png", "jpg", "jpeg"])

# --- 5. GENERATION LOGIC ---
if selected_company:
    if st.button(f"Generate KYC Note for {selected_company}"):
        with st.spinner("Analyzing data and uploaded files..."):

            # Prepare Prompt
            final_prompt = prompt_template.replace("{company_name}", selected_company)

            # Prepare Content (Text + File if available)
            contents = [final_prompt]
            if uploaded_file is not None:
                # Get file bytes and mime type for Gemini
                file_data = uploaded_file.getvalue()
                contents.append({
                    "mime_type": uploaded_file.type,
                    "data": file_data
                })

            # Call AI
            try:
                response = model.generate_content(contents)
                # Store result in session state so the download button can see it
                st.session_state["kyc_result"] = response.text
                st.session_state["current_company"] = selected_company
            except Exception as e:
                st.error(f"Error calling AI: {e}")

# --- 6. DISPLAY & DOWNLOAD ---
if "kyc_result" in st.session_state:
    st.divider()

    # Download Button at the top of results
    pdf_bytes = generate_pdf(st.session_state["kyc_result"], st.session_state["current_company"])
    st.download_button(
        label="📄 Download the note as PDF",
        data=pdf_bytes,
        file_name=f"KYC_{st.session_state['current_company'].replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

    st.subheader(f"Report for {st.session_state['current_company']}")
    st.markdown(st.session_state["kyc_result"])