import streamlit as st
from google import genai
from fpdf import FPDF
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import time

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Catamaran KYC", layout="wide", page_icon="📑")

st.markdown("""
    <style>
    .centered-title { text-align: center; color: #004a99; font-size: 42px; font-weight: 800; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #004a99; color: white; font-weight: bold; }
    .report-container { padding: 20px; border-radius: 10px; background-color: #ffffff; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE CLIENT & RETRY LOGIC ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("⚠️ GEMINI_API_KEY missing in Streamlit Secrets.")

# CORRECT AGENT ID: There is no 'flash' version of Deep Research
RESEARCH_AGENT = 'gemini-3-flash'


# Retry logic to handle the 429 'Quota Exceeded' errors
@retry(
    wait=wait_exponential(multiplier=1, min=10, max=60),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)  # Retries on any API interruption
)
def start_research_task(prompt):
    return client.interactions.create(
        input=prompt,
        agent=RESEARCH_AGENT,
        background=True
    )


# --- 3. RESOURCE LOADING ---
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

# --- 4. UI LAYOUT ---
st.markdown("<h1 class='centered-title'>Catamaran's KYC note generator</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("🔍 Entity Search")
    e_type = st.radio("Category", ["Listed Universe", "Private Entity"], horizontal=True)
    target = st.selectbox("Search", companies, index=None) if e_type == "Listed Universe" else st.text_input(
        "Enter Company Name")

with col2:
    st.subheader("📂 Supporting Evidence")
    uploaded_files = st.file_uploader("Upload DRHPs or Reports:", accept_multiple_files=True)

st.divider()

# --- 5. EXECUTION ENGINE ---
if target:
    if st.button(f"🚀 Launch Gemini 3 Deep Research for {target}"):
        with st.status(f"Conducting deep research on {target}...", expanded=True) as status:
            final_prompt = prompt_template.replace("{company_name}", target)

            try:
                # Initiate task with retry logic
                interaction = start_research_task(final_prompt)

                # Polling for completion
                while True:
                    res = client.interactions.get(id=interaction.id)
                    if res.state == "completed":
                        st.session_state["kyc_note"] = res.output
                        st.session_state["target_name"] = target
                        status.update(label="Analysis Complete!", state="complete")
                        break
                    elif res.state == "failed":
                        st.error("Agent failed. This usually happens if the search query is too broad.")
                        break

                    status.write("Agent is browsing web sources and synthesizing findings...")
                    time.sleep(20)  # Poll every 20 seconds to stay under rate limits

            except Exception as e:
                st.error(f"Quota Error: Your free tier limit is likely exhausted for today. {e}")

# --- 6. DISPLAY & PDF ---
if "kyc_note" in st.session_state:
    res_col1, res_col2 = st.columns([4, 1])
    with res_col2:
        pdf = FPDF()
        pdf.add_page();
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, f"KYC Report: {st.session_state['target_name']}", ln=True, align='C')
        pdf.ln(10);
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 7, st.session_state["kyc_note"])
        st.download_button("📥 Download PDF", data=pdf.output(), file_name="KYC_Report.pdf")

    st.markdown(f"<div class='report-container'>{st.session_state['kyc_note']}</div>", unsafe_allow_html=True)