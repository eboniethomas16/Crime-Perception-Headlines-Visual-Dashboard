# pages/00_Consent.py
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Consent", layout="wide")
st.title("Consent for Research")

PLACEHOLDER = "Select an option"
TARGET_PAGE = "0_Preliminary_Questions"   # exact Pages menu label (no .py)
TARGET_QUERY = f"?page={TARGET_PAGE}"

def try_programmatic_nav(target_page: str):
    """Try JS then Streamlit API; return True if we attempted JS (not guaranteed success)."""
    # 1) JS attempt (force href)
    try:
        js = f"""
        <script>
        try {{
            const url = new URL(window.location);
            url.searchParams.set('page', '{target_page}');
            // Force navigation
            window.location.href = url.toString();
        }} catch (e) {{
            console.error('nav js error', e);
        }}
        </script>
        """
        # use a visible small height so Cloud renders it reliably
        components.html(js, height=50)
        return True
    except Exception:
        pass

    # 2) Streamlit API fallback
    try:
        st.experimental_set_query_params(page=target_page)
        st.experimental_rerun()
        return True
    except Exception:
        pass

    return False

# If a session flag was set by a previous failed attempt, show the visible fallback button
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

            # 1) Try programmatic navigation (JS or API)
            attempted = try_programmatic_nav(TARGET_PAGE)

            # 2) If programmatic navigation didn't run or failed, set a session flag
            if not attempted:
                st.session_state["_navigate_to"] = TARGET_PAGE
                st.warning("Automatic navigation failed. Use the link or button below to continue.")

            # 3) Always show a visible link/button below so user can continue manually
            st.markdown("---")
            st.markdown(
                f"**If the app did not navigate automatically, click this link to continue:**  \n"
                f"[Go to Preliminary Questions]({TARGET_QUERY})"
            )
            # Large HTML button (reliable clickable element)
            components.html(
                f"""
                <div style="margin-top:10px;">
                  <a href="{TARGET_QUERY}" style="
                      display:inline-block;
                      background-color:#0b66c3;
                      color:white;
                      padding:12px 20px;
                      text-decoration:none;
                      border-radius:6px;
                      font-weight:600;
                      ">
                    Continue to Preliminary Questions
                  </a>
                </div>
                """,
                height=70,
            )

        else:
            st.session_state["pre_consent"] = False
            st.error("You have chosen not to consent. The survey will now end.")
            # Provide visible link to Thank You page as well
            st.markdown(f"[Exit to Thank You page](?page=4_Thank_You)")
            components.html(
                f'<a href="?page=4_Thank_You" style="display:inline-block;background:#d9534f;color:white;padding:10px 16px;border-radius:6px;text-decoration:none;">Exit survey</a>',
                height=60,
            )

with col2:
    if st.button("Exit survey", key="consent_exit"):
        st.info("You have exited the survey.")
        # show visible link/button to Thank You page
        st.markdown(f"[Exit to Thank You page](?page=4_Thank_You)")
        components.html(
            f'<a href="?page=4_Thank_You" style="display:inline-block;background:#d9534f;color:white;padding:10px 16px;border-radius:6px;text-decoration:none;">Exit survey</a>',
            height=60,
        )

# --- Debug output (temporary) ---
st.markdown("---")
st.write("**Debug: session_state keys (remove in production)**")
st.write({k: st.session_state.get(k) for k in sorted(st.session_state.keys())})
st.write("Query params:", st.experimental_get_query_params())
st.write("Direct link to click:", TARGET_QUERY)
