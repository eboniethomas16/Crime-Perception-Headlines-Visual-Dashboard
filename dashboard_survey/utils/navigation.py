# utils/navigation.py
import streamlit as st
import streamlit.components.v1 as components

def safe_navigate(target_page: str):
    """
    Navigate to a Streamlit Pages filename using JS first (best for browsers),
    then fall back to st.experimental_set_query_params. If both fail, show a message.
    Usage: safe_navigate("2_Dashboard_2_Perception_vs_Crime_vs_Headlines")
    """
    # 1) Try JS navigation in the browser
    try:
        js = f"""
        <script>
        try {{
            const url = new URL(window.location);
            url.searchParams.set('page', '{target_page}');
            // Replace history entry and reload so Streamlit picks up the param
            window.history.replaceState(null, '', url);
            setTimeout(() => window.location.reload(), 60);
        }} catch (e) {{
            // If JS fails, do nothing here and let Python fallback run
        }}
        </script>
        """
        components.html(js, height=0)
        return
    except Exception:
        # If components.html is unavailable or blocked, continue to Python fallback
        pass

    # 2) Try Streamlit API navigation
    try:
        st.experimental_set_query_params(page=target_page)
        st.experimental_rerun()
        return
    except Exception:
        pass

    # 3) Final fallback: instruct the user
    st.warning(
        "Automatic navigation is unavailable in this environment. "
        "Please use the Pages menu (top-left) to go to the next page."
    )
