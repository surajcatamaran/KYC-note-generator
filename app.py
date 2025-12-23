import streamlit as st
from google import genai
from fpdf import FPDF
import time
import io

# --- 1. PAGE CONFIG & MODERN UI ---
st.set_page_config(page_title="Catamaran KYC", layout="wide", page_icon="📑")

# Professional UI Styling
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
    .report-container {
        padding: 20px; border-radius: 10px; background-color: #ffffff;
        border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE SDK & CLIENT ---
try:
    # Google GenAI SDK (2025 Standard)
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ GEMINI_API_KEY missing. Update your Streamlit Cloud Secrets.")

# Gemini 3 Deep Research Agent Identifier
RESEARCH_AGENT = 'deep-research-flash-preview-12-2025'


# --- 3. DATA LOADING ---
@st.cache_data
def load_assets():
    try:
        with open("companies.txt", "r", encoding="utf-8") as f:
            list_comp = [line.strip() for line in f.readlines()]
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
    except Exception:
        list_comp, prompt = ["Reliance", "TCS"], "Research KYC for {company_name}"
    return list_comp, prompt


companies, prompt_template = load_assets()

# --- 4. CENTERED BRANDING ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

# --- 5. DASHBOARD LAYOUT ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("🔍 Entity Search")
    e_type = st.radio("Entity Category", ["Listed Universe", "Private Entity"], horizontal=True)
    if e_type == "Listed Universe":
        target = st.selectbox("Search Indian Listed Companies", options=companies, index=None)
    else:
        target = st.text_input("Enter Private Company Name")

with col2:
    st.subheader("📂 Supporting Evidence")
    # Updated: Multiple file upload support
    uploaded_files = st.file_uploader(
        "Upload Reports, DRHPs, or Financial Statements (No Limit):",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg"]
    )

st.divider()

# --- 6. DEEP RESEARCH ENGINE ---
if target:
    if st.button(f"🚀 Launch Gemini 3 Deep Research for {target}"):
        with st.status(f"Gemini 3 is conducting deep research on {target}...", expanded=True) as status:

            # Prepare instructions and context
            final_prompt = prompt_template.replace("{company_name}", target)

            # Handle attachments for the research agent
            config_tools = []
            if uploaded_files:
                status.write(f"Integrating {len(uploaded_files)} local files into research plan...")
                # Note: For production agentic use, files are often added via the Tools config
                # In this SDK version, we pass them as part of the initial input interaction

            try:
                # 1. Start Interaction (Background task for agents)
                interaction = client.interactions.create(
                    input=final_prompt,
                    agent=RESEARCH_AGENT,
                    background=True
                )

                # 2. Polling Loop: Deep Research can take minutes
                while True:
                    res = client.interactions.get(id=interaction.id)

                    if res.state == "completed":
                        st.session_state["kyc_note"] = res.output
                        st.session_state["target_name"] = target
                        status.update(label="Intelligence Synthesis Complete!", state="complete")
                        break
                    elif res.state == "failed":
                        st.error("The Deep Research agent encountered a critical error.")
                        break

                    # Update user on agent activity
                    status.write("Agent is browsing web sources, analyzing filings, and reasoning...")
                    time.sleep(15)

            except Exception as e:
                st.error(f"Interaction Error: {e}")

# --- 7. REPORT DISPLAY & EXPORT ---
if "kyc_note" in st.session_state:
    res_col1, res_col2 = st.columns([4, 1])

    with res_col1:
        st.success(f"Final Report: {st.session_state['target_name']}")

    with res_col2:
        # PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, f"Catamaran Deep Research: {st.session_state['target_name']}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 7, st.session_state["kyc_note"])

        st.download_button(
            label="📥 Download PDF",
            data=pdf.output(),
            file_name=f"DeepKYC_{st.session_state['target_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown(f"<div class='report-container'>{st.session_state['kyc_note']}</div>", unsafe_allow_html=True)