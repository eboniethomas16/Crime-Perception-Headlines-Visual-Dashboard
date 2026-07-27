# pages/00_Consent.py
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

def safe_navigate(target_page: str):
    """
    Try to set query params to navigate. If the environment doesn't support
    experimental_set_query_params, show a friendly message instead.
    """
    try:
        st.experimental_set_query_params(page=target_page)
        st.experimental_rerun()
    except Exception:
        st.warning(
            "Automatic navigation is unavailable in this environment. "
            "Please use the Pages menu (top-left) to go to the next page."
        )

with col1:
    if st.button("Continue"):
        if consent_choice == "Select an option":
            st.warning("Please choose whether you consent before continuing.")
        elif consent_choice == "Yes, I consent":
            st.session_state["pre_consent"] = True
            st.success("Thank you — your consent has been recorded.")
            # Navigate to preliminary questions page
            safe_navigate("0_Preliminary_Questions")
        else:  # No, I do not consent
            st.session_state["pre_consent"] = False
            st.error("You have chosen not to consent. The survey will now end.")
            # Navigate to Thank You page
            safe_navigate("4_Thank_You")

with col2:
    if st.button("Exit survey"):
        st.info("You have exited the survey.")
        safe_navigate("4_Thank_You")

# Show status if consent already recorded
if st.session_state.get("pre_consent") is True:
    st.info("Consent already given. You can continue to the survey pages.")
elif st.session_state.get("pre_consent") is False:
    st.info("You previously declined consent. The survey is closed for you.")
