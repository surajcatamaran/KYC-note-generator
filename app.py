import streamlit as st
from google import genai
from fpdf import FPDF
import time

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Catamaran KYC", layout="wide", page_icon="📑")

st.markdown("""
    <style>
    .centered-title { text-align: center; color: #004a99; font-size: 42px; font-weight: 800; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #004a99; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE CLIENT ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ GEMINI_API_KEY missing in Secrets.")

RESEARCH_AGENT = 'deep-research-pro-preview-12-2025'


# --- 3. HELPER FUNCTIONS ---
def clean_for_pdf(text):
    """Replaces non-Latin-1 characters to prevent PDF export errors."""
    # Common Gemini characters that break FPDF
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "—": "-", "–": "-", "•": "*", "…": "..."
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Force encode to latin-1 and ignore anything else that remains
    return text.encode("latin-1", "replace").decode("latin-1")


@st.cache_data
def load_assets():
    try:
        with open("companies.txt", "r", encoding="utf-8") as f:
            list_comp = [line.strip() for line in f.readlines()]
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
    except:
        list_comp, prompt = ["Reliance", "TCS"], "Research KYC for {company_name}"
    return list_comp, prompt


companies, prompt_template = load_assets()

# --- 4. DASHBOARD UI ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("🔍 Entity Search")
    e_type = st.radio("Category", ["Listed Universe", "Private Entity"], horizontal=True)
    target = st.selectbox("Search", companies, index=None) if e_type == "Listed Universe" else st.text_input(
        "Enter Company Name")

with col2:
    st.subheader("📂 Document Vault")
    uploaded_files = st.file_uploader("Upload supporting docs (No Limit):", accept_multiple_files=True)

st.divider()

# --- 5. DEEP RESEARCH ENGINE ---
if target:
    if st.button(f"🚀 Launch Gemini 3 Deep Research for {target}"):
        with st.status(f"Conducting deep research on {target}...", expanded=True) as status:
            final_prompt = prompt_template.replace("{company_name}", target)
            try:
                interaction = client.interactions.create(input=final_prompt, agent=RESEARCH_AGENT, background=True)
                while True:
                    res = client.interactions.get(id=interaction.id)
                    if res.status == "completed":
                        # Fixed: Correct way to access the final text
                        st.session_state["kyc_note"] = res.outputs[-1].text
                        st.session_state["target_name"] = target
                        status.update(label="Complete!", state="complete")
                        break
                    elif res.status == "failed":
                        st.error("Research agent failed.")
                        break
                    status.write("Agent is browsing web sources and reasoning...")
                    time.sleep(20)
            except Exception as e:
                st.error(f"Error: {e}")

# --- 6. DISPLAY & DOWNLOAD ---
if "kyc_note" in st.session_state:
    res_col1, res_col2 = st.columns([4, 1])
    with res_col2:
        # CLEAN TEXT FOR PDF
        pdf_ready_text = clean_for_pdf(st.session_state["kyc_note"])

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, f"KYC Report: {st.session_state['target_name']}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("helvetica", size=10)
        # multi_cell now receives sanitized text
        pdf.multi_cell(0, 7, pdf_ready_text)

        st.download_button(
            label="📥 Download PDF",
            data=pdf.output(),
            file_name=f"KYC_{st.session_state['target_name'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    st.markdown("---")
    st.markdown(st.session_state["kyc_note"])