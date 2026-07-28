# pages/00_Consent.py
import streamlit as st
import sys
from dashboard_survey.utils.navigation import safe_navigate


st.title("Consent")
if "pre_consent" not in st.session_state:
    st.session_state["pre_consent"] = None

choice = st.selectbox("I consent to my anonymised responses being used for this research.",
                      ["Select an option", "Yes, I consent", "No, I do not consent"],
                      key="pre_consent_select")

if st.button("Continue"):
    if choice == "Yes, I consent":
        st.session_state["pre_consent"] = True
        st.success("Consent recorded.")
        safe_navigate("0_Preliminary_Questions")
    elif choice == "No, I do not consent":
        st.session_state["pre_consent"] = False
        st.error("Survey closed for you.")
        safe_navigate("4_Thank_You")
    else:
        st.warning("Please select an option.")

# Always show manual link as guaranteed fallback
st.markdown("---")
st.markdown("[Go to Preliminary Questions](?page=0_Preliminary_Questions)")
