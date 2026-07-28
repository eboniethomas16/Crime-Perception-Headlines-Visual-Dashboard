# pages/00_Consent.py
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Consent", layout="wide")
st.title("Consent for Research")
if st.session_state.get("_navigate_to"):
    target = st.session_state["_navigate_to"]
    st.info(f"Ready to navigate to: {target}")
    if st.button(f"Go to {target} now", key="go_now_button"):
        try:
            st.experimental_set_query_params(page=target)
            st.experimental_rerun()
        except Exception:
            st.warning("Automatic navigation unavailable — please use the Pages menu (top-left).")


PLACEHOLDER = "Select an option"

import streamlit.components.v1 as components

def safe_navigate(target_page: str):
    try:
        js = f"""
        <script>
        try {{
            const url = new URL(window.location);
            url.searchParams.set('page', '{target_page}');
            window.location.href = url.toString();
        }} catch (e) {{ console.error(e); }}
        </script>
        """
        components.html(js, height=50)
        return
    except Exception:
        pass

    try:
        st.experimental_set_query_params(page=target_page)
        st.experimental_rerun()
        return
    except Exception:
        pass

    st.session_state["_navigate_to"] = target_page
    st.warning("Automatic navigation failed. Click the visible 'Go to next page' button.")


# --- Visible fallback button (top of page) ---
if st.session_state.get("_navigate_to"):
    target = st.session_state["_navigate_to"]
    st.info(f"Ready to navigate to: {target}")
    if st.button(f"Go to {target} now", key="go_now_button"):
        try:
            st.experimental_set_query_params(page=target)
            st.experimental_rerun()
        except Exception:
            st.warning("Automatic navigation unavailable — please use the Pages menu (top-left).")

# --- Consent UI ---
consent_choice = st.selectbox(
    "I consent to my anonymised responses being used for this research.",
    [PLACEHOLDER, "Yes, I consent", "No, I do not consent"],
    key="pre_consent_select"
)

col1, col2 = st.columns([1,1])
with col1:
    if st.button("Continue", key="consent_continue"):
        if consent_choice == PLACEHOLDER:
            st.warning("Please choose whether you consent before continuing.")
        elif consent_choice == "Yes, I consent":
            st.session_state["pre_consent"] = True
            st.success("Thank you — your consent has been recorded.")
            safe_navigate("0_Preliminary_Questions")
        else:
            st.session_state["pre_consent"] = False
            st.error("You have chosen not to consent. The survey will now end.")
            safe_navigate("4_Thank_You")

with col2:
    if st.button("Exit survey", key="consent_exit"):
        st.info("You have exited the survey.")
        safe_navigate("4_Thank_You")

# --- Debug output (remove when working) ---
st.markdown("---")
st.write("**Debug: session_state keys (remove in production)**")
st.write({k: st.session_state.get(k) for k in sorted(st.session_state.keys())})
