import streamlit as st
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
