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
    # Use the new Google GenAI SDK Client
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ GEMINI_API_KEY missing. Please check your Streamlit Cloud Secrets.")

# Gemini 3 Deep Research Agent ID
RESEARCH_AGENT = 'deep-research-pro-preview-12-2025'


# --- 3. RESOURCE LOADING ---
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

# --- 4. DASHBOARD UI ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("🔍 Entity Search")
    e_type = st.radio("Entity Category", ["Listed Universe", "Private Entity"], horizontal=True)
    target = st.selectbox("Search", companies, index=None) if e_type == "Listed Universe" else st.text_input(
        "Enter Company Name")

with col2:
    st.subheader("📂 Document Vault")
    uploaded_files = st.file_uploader("Upload supporting docs (No Limit):", accept_multiple_files=True)

st.divider()

# --- 5. DEEP RESEARCH ENGINE ---
if target:
    if st.button(f"🚀 Launch Gemini 3 Deep Research for {target}"):
        with st.status(f"Gemini 3 is conducting deep research on {target}...", expanded=True) as status:
            final_prompt = prompt_template.replace("{company_name}", target)

            try:
                # 1. Start Interaction
                interaction = client.interactions.create(
                    input=final_prompt,
                    agent=RESEARCH_AGENT,
                    background=True
                )

                # 2. Polling Loop
                while True:
                    res = client.interactions.get(id=interaction.id)

                    # FIX: Access .status and .outputs correctly
                    if res.status == "completed":
                        # The final text is in the last item of the outputs list
                        st.session_state["kyc_note"] = res.outputs[-1].text
                        st.session_state["target_name"] = target
                        status.update(label="Intelligence Synthesis Complete!", state="complete")
                        break
                    elif res.status == "failed":
                        st.error("The Deep Research agent encountered an error.")
                        break

                    status.write("Agent is browsing web sources and synthesizing findings...")
                    # Delay to stay within Tier 1 polling limits
                    time.sleep(20)

            except Exception as e:
                if "429" in str(e):
                    st.error("🛑 **Quota Limit:** Your Tier 1 limits are being calibrated. Please wait a few minutes.")
                else:
                    st.error(f"⚠️ Interaction Error: {e}")

# --- 6. DISPLAY & DOWNLOAD ---
if "kyc_note" in st.session_state:
    res_col1, res_col2 = st.columns([4, 1])
    with res_col2:
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
            mime="application/pdf"
        )
    st.markdown("---")
    # Display results in a clean container
    st.markdown(f"### Report for {st.session_state['target_name']}")
    st.markdown(st.session_state["kyc_note"])