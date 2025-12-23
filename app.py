import streamlit as st
from google import genai
from fpdf import FPDF
import time

# --- 1. PAGE CONFIG & MODERN UI ---
st.set_page_config(page_title="Catamaran KYC", layout="wide", page_icon="📑")

st.markdown("""
    <style>
    .centered-title {
        text-align: center; color: #004a99; font-size: 42px;
        font-weight: 800; margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #004a99; color: white; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE GEMINI 3 SDK ---
try:
    # Using the new Google GenAI SDK
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("⚠️ Configure GEMINI_API_KEY in Streamlit Secrets.")

# Gemini 3 Deep Research Agent ID (Preview Dec 2025)
RESEARCH_AGENT = 'deep-research-pro-preview-12-2025'


# --- 3. RESOURCE LOADING ---
@st.cache_data
def load_assets():
    try:
        with open("companies.txt", "r", encoding="utf-8") as f:
            list_comp = [line.strip() for line in f.readlines()]
    except:
        list_comp = ["Reliance Industries", "TCS"]

    try:
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
    except:
        prompt = "Deep Research KYC for {company_name}."
    return list_comp, prompt


companies, prompt_template = load_assets()

# --- 4. CENTERED UI ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("🔍 Entity Selection")
    e_type = st.radio("Category", ["Listed Company", "Private Company"], horizontal=True)
    target = st.selectbox("Search", companies, index=None) if e_type == "Listed Company" else st.text_input(
        "Enter Private Company Name")

with col2:
    st.subheader("📂 Document Vault")
    # Multi-file support enabled
    uploaded_files = st.file_uploader("Upload supporting docs (No limit):", accept_multiple_files=True)

st.divider()

# --- 5. DEEP RESEARCH ENGINE ---
if target:
    if st.button(f"🚀 Launch Gemini 3 Deep Research for {target}"):
        # Create a placeholder for live updates
        status_area = st.empty()

        with st.status(f"Gemini 3 is researching {target}...", expanded=True) as status:
            final_prompt = prompt_template.replace("{company_name}", target)

            # 1. Start Interaction (Background task for agents)
            interaction = client.interactions.create(
                input=final_prompt,
                agent=RESEARCH_AGENT,
                background=True  # Required for multi-step research
            )

            # 2. Polling Loop for Long-Running Research
            while True:
                current = client.interactions.get(id=interaction.id)
                if current.state == "completed":
                    st.session_state["kyc_note"] = current.output
                    st.session_state["target_name"] = target
                    status.update(label="Deep Research Complete!", state="complete")
                    break
                elif current.state == "failed":
                    st.error("Research Agent encountered an error.")
                    break

                status.write("Planning research steps and searching web sources...")
                time.sleep(15)  # Wait between polls

# --- 6. DISPLAY & PDF EXPORT ---
if "kyc_note" in st.session_state:
    res_col1, res_col2 = st.columns([4, 1])
    with res_col2:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, f"Catamaran Deep Research: {st.session_state['target_name']}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 8, st.session_state["kyc_note"])

        st.download_button(
            "📥 Download PDF",
            data=pdf.output(),
            file_name=f"DeepKYC_{st.session_state['target_name']}.pdf",
            mime="application/pdf"
        )

    st.markdown(st.session_state["kyc_note"])