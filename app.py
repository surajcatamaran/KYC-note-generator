import streamlit as st
from google import genai
import time

# --- 1. PAGE CONFIG & UI ---
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
        padding: 25px; border-radius: 10px; background-color: #ffffff;
        border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        line-height: 1.6; font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE CLIENT ---
try:
    # Google GenAI SDK Client
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

# --- 4. BRANDING & INPUTS ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("🔍 Entity Search")
    e_type = st.radio("Entity Category", ["Listed Universe", "Private Entity"], horizontal=True)
    if e_type == "Listed Universe":
        target = st.selectbox("Search Indian Listed Companies", options=companies, index=None)
    else:
        target = st.text_input("Enter Private Company Name")

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

                    if res.status == "completed":
                        # Fetch the final text output
                        st.session_state["kyc_note"] = res.outputs[-1].text
                        st.session_state["target_name"] = target
                        status.update(label="Intelligence Synthesis Complete!", state="complete")
                        break
                    elif res.status == "failed":
                        st.error("The Deep Research agent encountered an error.")
                        break

                    status.write("Agent is browsing web sources and synthesizing findings...")
                    # Delay to stay within polling limits
                    time.sleep(20)

            except Exception as e:
                if "429" in str(e):
                    st.error(
                        "🛑 **Quota Limit:** Your Tier 1 limits are being calibrated. Please wait a minute and try again.")
                else:
                    st.error(f"⚠️ Interaction Error: {e}")

# --- 6. DISPLAY RESULTS ---
if "kyc_note" in st.session_state:
    st.success(f"Final Intelligence Report: {st.session_state['target_name']}")
    st.markdown("---")
    # Wrap output in a styled container for better readability
    st.markdown(f"""
        <div class='report-container'>
            {st.session_state['kyc_note']}
        </div>
    """, unsafe_allow_html=True)