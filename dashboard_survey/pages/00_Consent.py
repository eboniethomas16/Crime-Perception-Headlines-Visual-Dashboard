# pages/Consent.py
import streamlit as st

st.set_page_config(page_title="Consent", layout="wide")
st.title("Consent for Research")

st.markdown(
    "Please read the consent statement below and select your choice. "
    "You must consent to continue with the survey."
)

consent_prompt = "I consent to my anonymised responses being used for this research."

# Use a selectbox with a placeholder so nothing is selected by default
consent_choice = st.selectbox(
    consent_prompt,
    ["Select an option", "Yes, I consent", "No, I do not consent"],
    key="pre_consent_select"
)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Continue"):
        if consent_choice == "Select an option":
            st.warning("Please choose whether you consent before continuing.")
        elif consent_choice == "Yes, I consent":
            st.session_state["pre_consent"] = True
            st.success("Thank you — your consent has been recorded. You may now proceed to the survey pages.")
        else:  # No, I do not consent
            st.session_state["pre_consent"] = False
            st.error("You have chosen not to consent. The survey will now end.")
            st.stop()

with col2:
    if st.button("Exit survey"):
        st.info("You have exited the survey.")
        st.stop()

# If user navigates back to this page after consenting, show status
if "pre_consent" in st.session_state and st.session_state.get("pre_consent") is True:
    st.info("Consent already given. You can continue to the survey pages.")
