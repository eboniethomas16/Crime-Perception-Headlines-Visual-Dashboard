
# streamlit_app_dashboard2.py
# Streamlit survey for Dashboard #2 — Headline Accuracy Tasks and Objective Checks
# Paste into a Streamlit app (streamlit run streamlit_app_dashboard2.py)

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import streamlit as st

import streamlit as st

st.set_page_config(page_title="Crime & Perception Survey", layout="wide")

st.title("Crime & Perception Dashboard Survey")

st.markdown("""
Welcome to the survey.

Use the sidebar or the page menu at the top to navigate:
- **Dashboard 1 – Perception vs Crime**
- **Dashboard 2 – Headlines vs Crime** (if enabled)
- **Thank you / Submit**
""")

st.set_page_config(page_title="Dashboard 1 – Perception vs Crime", layout="wide")

st.title("Dashboard 1 – Perception vs Crime")

st.header("Bivariate Choropleth Map")

st.radio(
    "How accurate and trustworthy did the map's values and colour encoding appear?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_bivmap_content"
)

st.radio(
    "How clear was the map at communicating the two variables (crime count and perception) at a glance?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_bivmap_learnability"
)

st.radio(
    "How easy was it to find and interpret a specific borough on the map?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_bivmap_easeofuse"
)

st.radio(
    "How easy was it to operate the map controls (zoom, pan, legend, hover) without confusion?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_bivmap_operability"
)

st.radio(
    "How useful was the map for identifying boroughs where perception and crime diverge?",
    ["Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d1_bivmap_usefulness"
)

st.text_area("Open feedback — BIVARIATE CHOROPLETH MAP", key="d1_open_chord_feedback")


# ---------------- HEATMAP ----------------

st.header("Heatmap (Perception vs Crime)")

st.radio(
    "How accurate and informative were the heatmap values and tooltips?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_heatmap_content"
)

st.radio(
    "How clear was the heatmap at showing where perception over/under estimates actual crime?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_heatmap_learnability"
)

st.radio(
    "How easy was it to interact with the heatmap (hover, select time, read tooltips)?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_heatmap_operability"
)

st.radio(
    "How easy was it to locate a specific borough and month in the heatmap?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_heatmap_easeofuse"
)

st.radio(
    "How useful was the heatmap for spotting borough/time combinations with large perception differences?",
    ["Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d1_heatmap_usefulness"
)

st.text_area("Open feedback — HEATMAP", key="d1_open_heatmap_feedback")


# ---------------- HOVERLIST ----------------

st.header("Hoverlist (Perception vs Crime)")

st.radio(
    "How accurate and complete were the hoverlist values and labels?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_hoverlist_content"
)

st.radio(
    "How clear were the hoverlist values (crime count; perception %; residual) when displayed?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_hoverlist_learnability"
)

st.radio(
    "How easy was it to control hover interactions and avoid accidental selections?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_hoverlist_operability"
)

st.radio(
    "How easy was it to move between categories in the hoverlist and read values?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_hoverlist_easeofuse"
)

st.radio(
    "How useful was the hoverlist for quickly identifying key values across charts?",
    ["Yes — very much", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d1_hoverlist_usefulness"
)

st.text_area("Open feedback — HOVER LIST", key="d1_open_hoverlist_feedback")


# ---------------- LINE CHARTS ----------------

st.header("Line Charts")

st.radio(
    "How accurate and clear were the values and scales on the line charts?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_lines_content"
)

st.radio(
    "How easy was it to compare multiple series (crime, perception, residuals) on the line charts?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_lines_easeofuse"
)

st.radio(
    "How easy was it to read and compare the line charts (crime; perception; residuals) together?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_lines_learnability"
)

st.radio(
    "How easy was it to use the hoverline and zoom controls on the line charts?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_lines_operability"
)

st.radio(
    "How useful were the line charts for understanding trends and spikes over time?",
    ["Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
    key="d1_lines_usefulness"
)

st.text_area("Open feedback — LINE CHARTS", key="d1_open_linecharts_feedback")


# ---------------- RESIDUALS CHART ----------------

st.header("Residuals Chart")

st.radio(
    "How accurate and interpretable were the residual values and labels?",
    ["Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
    key="d1_residuals_content"
)

st.radio(
    "How clear was the residuals chart at highlighting months where perception diverged from total crime counts for each borough?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_residuals_learnability"
)

st.radio(
    "How easy was it to spot the largest residual spikes for a selected crime?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_residuals_easeofuse"
)


# ---------------- SUMMARY PILLS ----------------

st.header("Summary Pills")

st.radio(
    "How clear were the summary pills (total count; avg perception; 12‑month change) at a glance?",
    ["Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
    key="d1_pills_learnability"
)

st.radio(
    "How consistent did the summary pill numbers appear compared with the detailed charts?",
    ["Very consistent", "Mostly consistent", "Neutral", "Somewhat inconsistent", "Very inconsistent"],
    key="d1_pills_content"
)

st.radio(
    "How easy was it to interpret the summary pills when scanning multiple Boroughs?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_pills_easeofuse"
)

st.radio(
    "How easy was it to select boroughs in the dropdown list at the top of the page?",
    ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
    key="d1_pills_operability"
)

st.radio(
    "How useful were the summary pills for forming an initial judgement about the selected crime category?",
    ["Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
    key="d1_pills_usefulness"
)

st.text_area("Open feedback — SUMMARY PILLS", key="d1_open_summary_pills_feedback")


# ----------------
