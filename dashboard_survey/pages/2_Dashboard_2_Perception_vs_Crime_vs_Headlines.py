import streamlit as st

st.set_page_config(page_title="Dashboard 2 – Headlines vs Crime", layout="wide")

st.title("Dashboard 2 – Headlines vs Crime")

# ---------------- CHORD CHART ----------------

st.header("Chord Chart")

st.text_area("Open feedback — CHORD CHART", key="open_chord_feedback")


# ---------------- HEATMAP ----------------

st.header("Heatmap (Headlines vs Crime)")

st.radio(
    "How accurate and informative were the heatmap values and tooltips?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_heatmap_content"
)

st.radio(
    "How clear was the heatmap at showing where HEADLINE over/under-reports actual crime?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_heatmap_learnability"
)

st.radio(
    "How easy was it to interact with the heatmap (hover, select time, read tooltips)?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_heatmap_operability"
)

st.radio(
    "How easy was it to locate a specific crime category and month in the heatmap?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_heatmap_easeofuse"
)

st.radio(
    "How useful was the heatmap for spotting crime category/time combinations with large crime differences?",
    ["Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d2_heatmap_usefulness"
)

st.text_area("Open feedback — HEATMAP", key="open_heatmap_feedback")


# ---------------- HOVER LIST ----------------

st.header("Hoverlist (Headlines vs Crime)")

st.radio(
    "How accurate and complete were the hoverlist values and labels?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_hoverlist_content"
)

st.radio(
    "How clear were the hoverlist values (crime count; headlines; perception %; residual) when displayed?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_hoverlist_learnability"
)

st.radio(
    "How easy was it to control hover interactions and avoid accidental selections?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_hoverlist_operability"
)

st.radio(
    "How easy was it to move between categories in the hoverlist and read values?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_hoverlist_easeofuse"
)

st.radio(
    "How useful was the hoverlist for quickly identifying key values across charts?",
    ["Yes — very much", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d2_hoverlist_usefulness"
)

st.text_area("Open feedback — HOVER LIST", key="open_hoverlist_feedback")


# ---------------- LINE CHARTS ----------------

st.header("Line Charts")

st.radio(
    "How accurate and clear were the values and scales on the line charts?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_lines_content"
)

st.radio(
    "How easy was it to compare multiple series (crime, perception, headlines) on the line charts?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_lines_easeofuse"
)

st.radio(
    "How easy was it to read and compare the line charts (crime; perception; headlines; residuals) together?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_lines_learnability"
)

st.radio(
    "How easy was it to use the hoverline and zoom controls on the line charts?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_lines_operability"
)

st.radio(
    "How useful were the line charts for understanding trends and spikes over time?",
    ["Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d2_lines_usefulness"
)

st.text_area("Open feedback — LINE CHARTS", key="open_linecharts_feedback")


# ---------------- RESIDUALS CHART ----------------

st.header("Residuals Chart")

st.radio(
    "How accurate and interpretable were the residual values and labels?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d2_residuals_content"
)

st.radio(
    "How clear was the residuals chart at highlighting months where perception diverged from total headlines and crime counts for each crime category?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_residuals_learnability"
)

st.radio(
    "How easy was it to spot the largest residual spikes for a selected crime?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_residuals_easeofuse"
)


# ---------------- SUMMARY PILLS ----------------

st.header("Summary Pills")

st.radio(
    "How clear were the summary pills (total Counts; 12‑month % changes) at a glance?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_pills_learnability"
)

st.radio(
    "How consistent did the summary pill numbers appear compared with the detailed charts?",
    ["Very consistent", "Mostly consistent", "Neutral", "Somewhat inconsistent", "Very inconsistent"],
    key="d2_pills_content"
)

st.radio(
    "How easy was it to interpret the summary pills when scanning multiple crime categories?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_pills_easeofuse"
)

st.radio(
    "How easy was it to select crime categories in the dropdown list at the top of the page?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d2_pills_operability"
)

st.radio(
    "How useful were the summary pills for forming an initial judgement about the selected crime category?",
    ["Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d2_pills_usefulness"
)

st.text_area("Open feedback — SUMMARY PILLS", key="open_summary_pills_feedback")


# ---------------- DASHBOARD LEVEL ----------------

st.header("Dashboard-Level Questions")

st.radio(
    "How well did Dashboard 2 improve your situational awareness about headlines vs crime?",
    ["Greatly improved", "Somewhat improved", "Neutral", "Slightly improved", "Not improved"],
    key="d2_situational_awareness"
)

st.radio(
    "How satisfied are you overall with Dashboard 2 for understanding headlines vs crime?",
    ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
    key="d2_overall_satisfaction"
)

st.text_area("Open feedback — CRIME VS. HEADLINES DASHBOARD", key="d2_open_summary_dashboard_feedback")

st.radio(
    "Does the dashboard include the functions and features you expect for this analysis (filters; tooltips; zoom; borough selection; summary pills)?",
    ["All expected features present", "Most present", "Some present", "Few present", "None present"],
    key="d2_features_coverage"
)

st.radio(
    "How well integrated are the dashboard features into a single coherent tool?",
    ["Very well integrated", "Well integrated", "Neutral", "Poorly integrated", "Not integrated at all"],
    key="d2_integration"
)

st.radio(
    "How would you rate the dashboard's performance (speed when filtering; hovering; zooming)?",
    ["Very fast", "Fast", "Acceptable", "Slow", "Very slow"],
    key="d2_performance"
)

st.radio(
    "How well did Dashboard 2 support the task you came to do (compare headlines vs actual crime)?",
    ["Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d2_task_support"
)

st.radio(
    "How clear is the dashboard's user interface (labels; legends; control placement) overall?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d2_userinterface"
)

st.radio(
    "How would you rate the dashboard's overall visual design (colour choices; chart styles; layout)?",
    ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
    key="d2_visualdesign_satisfaction"
)

st.success("Dashboard 2 survey complete.")
