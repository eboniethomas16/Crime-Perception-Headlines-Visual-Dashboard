# pages/00_Consent.py
import streamlit as st
from utils.navigation import safe_navigate

st.set_page_config(page_title="Consent", layout="wide")
st.title("Consent for Research")

# Ensure navigation flag exists
if "_navigate_to" not in st.session_state:
    st.session_state["_navigate_to"] = None

# If a navigation request exists, show a button to complete it (top of page)
if st.session_state.get("_navigate_to"):
    target = st.session_state["_navigate_to"]
    st.info(f"Ready to navigate to: {target}")
    if st.button(f"Go to {target} now", key="go_now_button"):
        try:
            st.experimental_set_query_params(page=target)
            st.experimental_rerun()
        except Exception:
            st.warning("Automatic navigation unavailable — please use the Pages menu (top-left).")

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
    if st.button("Continue", key="consent_continue"):
        if consent_choice == "Select an option":
            st.warning("Please choose whether you consent before continuing.")
        elif consent_choice == "Yes, I consent":
            st.session_state["pre_consent"] = True
            st.success("Thank you — your consent has been recorded.")
            safe_navigate("0_Preliminary_Questions")
        else:  # No, I do not consent
            st.session_state["pre_consent"] = False
            st.error("You have chosen not to consent. The survey will now end.")
            safe_navigate("4_Thank_You")

with col2:
    if st.button("Exit survey", key="consent_exit"):
        st.info("You have exited the survey.")
        safe_navigate("4_Thank_You")

# Show status if consent already recorded
if st.session_state.get("pre_consent") is True:
    st.info("Consent already given. You can continue to the survey pages.")
elif st.session_state.get("pre_consent") is False:
    st.info("You previously declined consent. The survey is closed for you.")
