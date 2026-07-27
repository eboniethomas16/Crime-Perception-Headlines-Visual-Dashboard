# pages/2_Dashboard_2_Perception_vs_Crime.py
import streamlit as st

st.set_page_config(page_title="Dashboard 2 – Headlines vs Crime", layout="wide")
st.title("Dashboard 2 – Headlines vs Crime")
st.markdown("Please answer the questions below about Dashboard 2. All single-choice items start unselected.")

PLACEHOLDER = "Select an option"

# --- Require consent before showing anything ---
if not st.session_state.get("pre_consent", False):
    st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
    if st.button("Go to Consent page"):
        st.experimental_set_query_params(page="Consent")
        st.experimental_rerun()
    st.stop()

# ---------------- CHORD CHART ----------------
st.header("Chord Chart")
st.text_area("Open feedback — CHORD CHART", key="d2_open_chord_feedback")

# ---------------- HEATMAP ----------------
st.header("Heatmap (Headlines vs Crime)")

st.selectbox(
    "How accurate and informative were the heatmap values and tooltips?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_heatmap_content"
)

st.selectbox(
    "How clear was the heatmap at showing where HEADLINE over/under-reports actual crime?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_heatmap_learnability"
)

st.selectbox(
    "How easy was it to interact with the heatmap (hover, select time, read tooltips)?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_heatmap_operability"
)

st.selectbox(
    "How easy was it to locate a specific crime category and month in the heatmap?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_heatmap_easeofuse"
)

st.selectbox(
    "How useful was the heatmap for spotting crime category/time combinations with large crime differences?",
    [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d2_heatmap_usefulness"
)

st.text_area("Open feedback — HEATMAP", key="d2_open_heatmap_feedback")

# ---------------- HOVER LIST ----------------
st.header("Hoverlist (Headlines vs Crime)")

st.selectbox(
    "How accurate and complete were the hoverlist values and labels?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_hoverlist_content"
)

st.selectbox(
    "How clear were the hoverlist values (crime count; headlines; perception %; residual) when displayed?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_hoverlist_learnability"
)

st.selectbox(
    "How easy was it to control hover interactions and avoid accidental selections?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_hoverlist_operability"
)

st.selectbox(
    "How easy was it to move between categories in the hoverlist and read values?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_hoverlist_easeofuse"
)

st.selectbox(
    "How useful was the hoverlist for quickly identifying key values across charts?",
    [PLACEHOLDER, "Yes — very much", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d2_hoverlist_usefulness"
)

st.text_area("Open feedback — HOVER LIST", key="d2_open_hoverlist_feedback")

# ---------------- LINE CHARTS ----------------
st.header("Line Charts")

st.selectbox(
    "How accurate and clear were the values and scales on the line charts?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_lines_content"
)

st.selectbox(
    "How easy was it to compare multiple series (crime, perception, headlines) on the line charts?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_lines_easeofuse"
)

st.selectbox(
    "How easy was it to read and compare the line charts (crime; perception; headlines; residuals) together?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_lines_learnability"
)

st.selectbox(
    "How easy was it to use the hoverline and zoom controls on the line charts?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_lines_operability"
)

st.selectbox(
    "How useful were the line charts for understanding trends and spikes over time?",
    [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d2_lines_usefulness"
)

st.text_area("Open feedback — LINE CHARTS", key="d2_open_linecharts_feedback")

# ---------------- RESIDUALS CHART ----------------
st.header("Residuals Chart")

st.selectbox(
    "How accurate and interpretable were the residual values and labels?",
    [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_residuals_content"
)

st.selectbox(
    "How clear was the residuals chart at highlighting months where perception diverged from total headlines and crime counts for each crime category?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_residuals_learnability"
)

st.selectbox(
    "How easy was it to spot the largest residual spikes for a selected crime?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_residuals_easeofuse"
)

# ---------------- SUMMARY PILLS ----------------
st.header("Summary Pills")

st.selectbox(
    "How clear were the summary pills (total Counts; 12‑month % changes) at a glance?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_pills_learnability"
)

st.selectbox(
    "How consistent did the summary pill numbers appear compared with the detailed charts?",
    [PLACEHOLDER, "Very consistent", "Mostly consistent", "Neutral", "Somewhat inconsistent", "Very inconsistent"],
    key="d2_pills_content"
)

st.selectbox(
    "How easy was it to interpret the summary pills when scanning multiple crime categories?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_pills_easeofuse"
)

st.selectbox(
    "How easy was it to select crime categories in the dropdown list at the top of the page?",
    [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_pills_operability"
)

st.selectbox(
    "How useful were the summary pills for forming an initial judgement about the selected crime category?",
    [PLACEHOLDER, "Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d2_pills_usefulness"
)

st.text_area("Open feedback — SUMMARY PILLS", key="d2_open_summary_pills_feedback")

# ---------------- DASHBOARD LEVEL ----------------
st.header("Dashboard-Level Questions")

st.selectbox(
    "How well did Dashboard 2 improve your situational awareness about headlines vs crime?",
    [PLACEHOLDER, "Greatly improved", "Somewhat improved", "Neutral", "Slightly improved", "Not improved"],
    key="d2_situational_awareness"
)

st.selectbox(
    "How satisfied are you overall with Dashboard 2 for understanding headlines vs crime?",
    [PLACEHOLDER, "Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
    key="d2_overall_satisfaction"
)

st.text_area("Open feedback — CRIME VS. HEADLINES DASHBOARD", key="d2_open_summary_dashboard_feedback")

st.selectbox(
    "Does the dashboard include the functions and features you expect for this analysis (filters; tooltips; zoom; borough selection; summary pills)?",
    [PLACEHOLDER, "All expected features present", "Most present", "Some present", "Few present", "None present"],
    key="d2_features_coverage"
)

st.selectbox(
    "How well integrated are the dashboard features into a single coherent tool?",
    [PLACEHOLDER, "Very well integrated", "Well integrated", "Neutral", "Poorly integrated", "Not integrated at all"],
    key="d2_integration"
)

st.selectbox(
    "How would you rate the dashboard's performance (speed when filtering; hovering; zooming)?",
    [PLACEHOLDER, "Very fast", "Fast", "Acceptable", "Slow", "Very slow"],
    key="d2_performance"
)

st.selectbox(
    "How well did Dashboard 2 support the task you came to do (compare headlines vs actual crime)?",
    [PLACEHOLDER, "Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d2_task_support"
)

st.selectbox(
    "How clear is the dashboard's user interface (labels; legends; control placement) overall?",
    [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_userinterface"
)

st.selectbox(
    "How would you rate the dashboard's overall visual design (colour choices; chart styles; layout)?",
    [PLACEHOLDER, "Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
    key="d2_visualdesign_satisfaction"
)

st.markdown("---")
st.write("When you're done, click Finish to complete the survey and go to the Thank You page.")

# ---------------- CONTINUE / FINISH BUTTON + VALIDATION ----------------
if st.button("Finish and go to Thank You"):
    # Ensure pre-questions are completed (basic required pre_ keys)
    required_pre = [
        "pre_consent", "pre_age_band", "pre_education", "pre_borough",
        "pre_police_reliability", "pre_police_fairness", "pre_police_job",
        "pre_news_frequency", "pre_headline_accuracy",
        "pre_headline_inflation", "pre_headline_truth", "pre_crime_increase",
        "pre_crime_most", "pre_crime_least", "pre_media_least", "pre_media_most",
        "pre_lowest_boroughs", "pre_highest_boroughs"
    ]
    missing_pre = [k for k in required_pre if st.session_state.get(k) in (None, [], False)]
    if missing_pre:
        st.error("It looks like some preliminary questions are incomplete. Please complete the pre‑survey questions first.")
        if st.button("Go to Pre‑questions"):
            st.experimental_set_query_params(page="2_Pre_Dashboard_2_Questions")
            st.experimental_rerun()
    else:
        # Validate required d2_ keys
        required_d2 = [
            "d2_heatmap_content", "d2_heatmap_learnability", "d2_heatmap_operability",
            "d2_heatmap_easeofuse", "d2_heatmap_usefulness",
            "d2_hoverlist_content", "d2_hoverlist_learnability", "d2_hoverlist_operability",
            "d2_hoverlist_easeofuse", "d2_hoverlist_usefulness",
            "d2_lines_content", "d2_lines_easeofuse", "d2_lines_learnability",
            "d2_lines_operability", "d2_lines_usefulness",
            "d2_residuals_content", "d2_residuals_learnability", "d2_residuals_easeofuse",
            "d2_pills_learnability", "d2_pills_content", "d2_pills_easeofuse",
            "d2_pills_operability", "d2_pills_usefulness",
            "d2_situational_awareness", "d2_overall_satisfaction",
            "d2_features_coverage", "d2_integration", "d2_performance",
            "d2_task_support", "d2_userinterface", "d2_visualdesign_satisfaction"
        ]
        missing_d2 = [k for k in required_d2 if st.session_state.get(k) in (None, PLACEHOLDER)]
        if missing_d2:
            st.error("Please answer all required Dashboard 2 questions before finishing. The following items are unanswered:")
            for k in missing_d2:
                label = k.replace("d2_", "").replace("_", " ").capitalize()
                st.write(f"- {label}")
            st.info("Scroll up to complete the unanswered questions.")
        else:
            st.success("All Dashboard 2 questions complete. Redirecting to Post Survey Questions...")
            # Navigate to Thank You page
            st.experimental_set_query_params(page="3_Post_Questions")
            st.experimental_rerun()
