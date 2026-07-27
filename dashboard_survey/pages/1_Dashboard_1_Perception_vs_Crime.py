# pages/1_Dashboard_1_Perception_vs_Crime.py
import streamlit as st

st.set_page_config(page_title="Dashboard 1 – Perception vs Crime", layout="wide")

st.title("Dashboard 1 – Perception vs Crime")
st.markdown("Please answer the questions below about Dashboard 1. All single-choice items start unselected.")

PLACEHOLDER = "Select an option"

# ---------------- BIVARIATE CHOROPLETH MAP ----------------
st.header("Bivariate Choropleth Map")

st.selectbox(
    "How accurate and trustworthy did the map's values and colour encoding appear?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_bivmap_content"
)

st.selectbox(
    "How clear was the map at communicating the two variables (crime count and perception) at a glance?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_bivmap_learnability"
)

st.selectbox(
    "How easy was it to find and interpret a specific borough on the map?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_bivmap_easeofuse"
)

st.selectbox(
    "How easy was it to operate the map controls (zoom, pan, legend, hover) without confusion?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_bivmap_operability"
)

st.selectbox(
    "How useful was the map for identifying boroughs where perception and crime diverge?",
    [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d1_bivmap_usefulness"
)

st.text_area("Open feedback — BIVARIATE CHOROPLETH MAP", key="d1_open_chord_feedback")


# ---------------- HEATMAP ----------------
st.header("Heatmap (Perception vs Crime)")

st.selectbox(
    "How accurate and informative were the heatmap values and tooltips?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_heatmap_content"
)

st.selectbox(
    "How clear was the heatmap at showing where perception over/under estimates actual crime?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_heatmap_learnability"
)

st.selectbox(
    "How easy was it to interact with the heatmap (hover, select time, read tooltips)?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_heatmap_operability"
)

st.selectbox(
    "How easy was it to locate a specific borough and month in the heatmap?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_heatmap_easeofuse"
)

st.selectbox(
    "How useful was the heatmap for spotting borough/time combinations with large perception differences?",
    [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d1_heatmap_usefulness"
)

st.text_area("Open feedback — HEATMAP", key="d1_open_heatmap_feedback")


# ---------------- HOVERLIST ----------------
st.header("Hoverlist (Perception vs Crime)")

st.selectbox(
    "How accurate and complete were the hoverlist values and labels?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_hoverlist_content"
)

st.selectbox(
    "How clear were the hoverlist values (crime count; perception %; residual) when displayed?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_hoverlist_learnability"
)

st.selectbox(
    "How easy was it to control hover interactions and avoid accidental selections?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_hoverlist_operability"
)

st.selectbox(
    "How easy was it to move between categories in the hoverlist and read values?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_hoverlist_easeofuse"
)

st.selectbox(
    "How useful was the hoverlist for quickly identifying key values across charts?",
    [PLACEHOLDER, "Yes — very much", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d1_hoverlist_usefulness"
)

st.text_area("Open feedback — HOVER LIST", key="d1_open_hoverlist_feedback")


# ---------------- LINE CHARTS ----------------
st.header("Line Charts")

st.selectbox(
    "How accurate and clear were the values and scales on the line charts?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_lines_content"
)

st.selectbox(
    "How easy was it to compare multiple series (crime, perception, residuals) on the line charts?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_lines_easeofuse"
)

st.selectbox(
    "How easy was it to read and compare the line charts (crime; perception; residuals) together?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_lines_learnability"
)

st.selectbox(
    "How easy was it to use the hoverline and zoom controls on the line charts?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_lines_operability"
)

st.selectbox(
    "How useful were the line charts for understanding trends and spikes over time?",
    [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d1_lines_usefulness"
)

st.text_area("Open feedback — LINE CHARTS", key="d1_open_linecharts_feedback")


# ---------------- RESIDUALS CHART ----------------
st.header("Residuals Chart")

st.selectbox(
    "How accurate and interpretable were the residual values and labels?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_residuals_content"
)

st.selectbox(
    "How clear was the residuals chart at highlighting months where perception diverged from total crime counts for each borough?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_residuals_learnability"
)

st.selectbox(
    "How easy was it to spot the largest residual spikes for a selected crime?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_residuals_easeofuse"
)


# ---------------- SUMMARY PILLS ----------------
st.header("Summary Pills")

st.selectbox(
    "How clear were the summary pills (total count; avg perception; 12‑month change) at a glance?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_pills_learnability"
)

st.selectbox(
    "How consistent did the summary pill numbers appear compared with the detailed charts?",
    [PLACEHOLDER, "Very consistent", "Mostly consistent", "Neutral", "Somewhat inconsistent", "Very inconsistent"],
    key="d1_pills_content"
)

st.selectbox(
    "How easy was it to interpret the summary pills when scanning multiple Boroughs?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_pills_easeofuse"
)

st.selectbox(
    "How easy was it to select boroughs in the dropdown list at the top of the page?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_pills_operability"
)

st.selectbox(
    "How useful were the summary pills for forming an initial judgement about the selected crime category?",
    [PLACEHOLDER, "Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d1_pills_usefulness"
)

st.text_area("Open feedback — SUMMARY PILLS", key="d1_open_summary_pills_feedback")


# ---------------- CONTINUE BUTTON + VALIDATION ----------------
st.markdown("---")
st.write("When you're done, click Continue to proceed to Dashboard 2.")

if st.button("Continue to Dashboard 2"):
    # list all required d1_ keys (add or remove keys if you change questions)
    required_keys = [
        "d1_bivmap_content", "d1_bivmap_learnability", "d1_bivmap_easeofuse",
        "d1_bivmap_operability", "d1_bivmap_usefulness",
        "d1_heatmap_content", "d1_heatmap_learnability", "d1_heatmap_operability",
        "d1_heatmap_easeofuse", "d1_heatmap_usefulness",
        "d1_hoverlist_content", "d1_hoverlist_learnability", "d1_hoverlist_operability",
        "d1_hoverlist_easeofuse", "d1_hoverlist_usefulness",
        "d1_lines_content", "d1_lines_easeofuse", "d1_lines_learnability",
        "d1_lines_operability", "d1_lines_usefulness",
        "d1_residuals_content", "d1_residuals_learnability", "d1_residuals_easeofuse",
        "d1_pills_learnability", "d1_pills_content", "d1_pills_easeofuse",
        "d1_pills_operability", "d1_pills_usefulness"
    ]

    missing = [k for k in required_keys if st.session_state.get(k) in (None, PLACEHOLDER)]
    if missing:
        # Friendly, readable list of missing questions
        st.error("Please answer all required questions before continuing. The following items are unanswered:")
        for k in missing:
            # convert key to a nicer label for the user
            label = k.replace("d1_", "").replace("_", " ").capitalize()
            st.write(f"- {label}")
        st.info("Scroll up to complete the unanswered questions.")
    else:
        st.success("All Dashboard 1 questions complete. Redirecting to Dashboard 2...")
        # Navigate to Dashboard 2 page (adjust page name if your file is named differently)
        st.experimental_set_query_params(page="2_Dashboard_2_Perception_vs_Crime_vs_Headlines")
        st.experimental_rerun()
