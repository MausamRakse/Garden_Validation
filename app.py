import streamlit as st
from validator import ImageValidator

# Page Config
st.set_page_config(
    page_title="Home Garden Validator",
    page_icon="🏡",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .stAlert {
        border-radius: 10px;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        text-align: center;
        color: #2E7D32;
    }
    .upload-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🏡 Home Garden Image Validation</h1>", unsafe_allow_html=True)

# Sidebar for API Key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter Google Gemini API Key", type="password", help="Get your key from https://aistudio.google.com/app/apikey")
    if not api_key:
        st.warning("⚠️ You must enter an API Key to proceed.")

st.write("Please upload clear photos of your Front, Back, and Side yards. Ensure they are outdoors and well-lit.")

validator = ImageValidator()

with st.form("upload_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1️⃣ Front Yard")
        front_img = st.file_uploader("Upload Front Yard", type=['jpg', 'jpeg', 'png'], key="front")

    with col2:
        st.markdown("### 2️⃣ Back Yard")
        back_img = st.file_uploader("Upload Back Yard", type=['jpg', 'jpeg', 'png'], key="back")

    st.markdown("### 3️⃣ Side Yard")
    side_img = st.file_uploader("Upload Side Yard", type=['jpg', 'jpeg', 'png'], key="side")

    submitted = st.form_submit_button("Validate Images", use_container_width=True, type="primary")

if submitted:
    if not api_key:
        st.error("❌ API Key is missing. Please enter it in the sidebar.")
    elif not (front_img and back_img and side_img):
        st.error("⚠️ Please upload all 3 images to proceed.")
    else:
        import time
        with st.spinner("Validating Front Yard..."):
            # Validate Front
            front_res = validator.validate_image(front_img, "Front Yard", api_key)
        
        time.sleep(1.0) # Pause to respect Rate Limits
        
        with st.spinner("Validating Back Yard..."):
            # Validate Back
            back_res = validator.validate_image(back_img, "Back Yard", api_key)

        time.sleep(1.0) # Pause to respect Rate Limits

        with st.spinner("Validating Side Yard..."):
            # Validate Side
            side_res = validator.validate_image(side_img, "Side Yard", api_key)
            
            # Check Results
            all_valid = True
            
            # --- Results Display ---
            st.divider()
            
            # Front
            if front_res['valid']:
                st.success(f"✅ Front Yard: Valid (Score: {front_res.get('score', 'N/A')}, Model: {front_res.get('model_used', 'N/A')})")
            else:
                st.error(f"❌ Front Yard: {front_res['error']}\n\n💡 Suggestion: {front_res.get('suggestion', '')}\n\n(Model: {front_res.get('model_used', 'N/A')})")
                all_valid = False

            # Back
            if back_res['valid']:
                st.success(f"✅ Back Yard: Valid (Score: {back_res.get('score', 'N/A')}, Model: {back_res.get('model_used', 'N/A')})")
            else:
                st.error(f"❌ Back Yard: {back_res['error']}\n\n💡 Suggestion: {back_res.get('suggestion', '')}\n\n(Model: {back_res.get('model_used', 'N/A')})")
                all_valid = False

            # Side
            if side_res['valid']:
                st.success(f"✅ Side Yard: Valid (Score: {side_res.get('score', 'N/A')}, Model: {side_res.get('model_used', 'N/A')})")
            else:
                st.error(f"❌ Side Yard: {side_res['error']}\n\n💡 Suggestion: {side_res.get('suggestion', '')}\n\n(Model: {side_res.get('model_used', 'N/A')})")
                all_valid = False
            
            # Final Verdict
            if all_valid:
                st.balloons()
                st.success("🎉 All images are valid! You may proceed.")
            else:
                st.warning("Please correct the errors above and re-upload.")
