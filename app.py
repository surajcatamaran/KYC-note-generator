import streamlit as st
import google.generativeai as genai

# 1. Setup Gemini Pro (API Key from Streamlit Secrets)
# For local testing, you can temporarily replace st.secrets with your actual key: "YOUR_KEY"
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = "PASTE_YOUR_API_KEY_HERE"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. Load the Public Companies List
try:
    with open("companies.txt", "r", encoding="utf-8") as f: # Added encoding here
        public_companies = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    public_companies = ["Reliance Industries", "TCS", "HDFC Bank"]

# 3. Load your 5-page prompt template
try:
    with open("prompt_template.txt", "r", encoding="utf-8") as f: # Added encoding here
        detailed_instructions = f.read()
except FileNotFoundError:
    detailed_instructions = "Analyze this company: {company_name}"

st.set_page_config(page_title="KYC Intelligence Tool", layout="wide")
st.title("🇮🇳 Indian Company KYC Intelligence")

# STEP 1: Choose Company Type
company_type = st.radio(
    "Select the type of company:",
    ["Indian Public Listed Company", "Indian Private Company"],
    index=0
)

# STEP 2: Conditional Input Interface
selected_company = ""
if company_type == "Indian Public Listed Company":
    selected_company = st.selectbox(
        "Search and select a listed company:",
        options=public_companies,
        index=None,
        placeholder="Type name (e.g., Reliance, TCS...)"
    )
else:
    selected_company = st.text_input(
        "Enter the name of the Private Company:",
        placeholder="Type the full company name here..."
    )

# STEP 3: Generate KYC Note
if selected_company:
    if st.button(f"Generate KYC Note for {selected_company}"):
        with st.spinner("Applying 5-page research framework..."):
            # Insert the company name into your prompt
            final_prompt = detailed_instructions.format(company_name=selected_company)

            # Call Gemini Pro
            response = model.generate_content(final_prompt)

            # Display result
            st.divider()
            st.subheader(f"Final Report: {selected_company}")
            st.markdown(response.text)