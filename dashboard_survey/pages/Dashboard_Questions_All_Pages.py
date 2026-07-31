import streamlit as st
import pandas as pd
from pathlib import Path
import uuid
from datetime import datetime
import os
import tempfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import math

# these are the keys for the Google Sheet columns, in order. 
# They are used to ensure the sheet has the correct headers and to map session state to sheet columns.
# Complete headers list (ordered) including all keys referenced across pages and widgets.
creds = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON") or st.secrets.get("gcp_service_account")



headers = [
    "user_id",
    "submission_timestamp_utc",

# --- pre-dashboard questions ---
    "pre_consent_select",
    "pre_age_band",
    "pre_education",
    "pre_borough",
    "pre_police_reliability",
    "pre_police_fairness",
    "pre_police_job",
    "pre_news_frequency",
    "pre_headline_accuracy",
    "pre_headline_inflation",
    "pre_headline_truth",
    "pre_crime_increase",
    "pre_crime_most",
    "pre_crime_least",
    "pre_media_least",
    "pre_media_most",
    "pre_lowest_boroughs",
    "pre_highest_boroughs",

    # --- dashboard 1 questions ---
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
    "d1_pills_operability", "d1_pills_usefulness",
    # --- open feedback text areas (required) ---
    "d1_open_chord_feedback", "d1_open_heatmap_feedback",
    "d1_open_hoverlist_feedback", "d1_open_linecharts_feedback",
    "d1_open_summary_pills_feedback",
    # --- dashboard-level questions ---
    "d1_overall_ui", "d1_overall_situational_awareness",
    "d1_overall_satisfaction", "d1_overall_task_suitability", "d1_overall_system_capabilities",

    #dashboard 2 questions (in order)
    # chord chart (in order)
    "d2_chord_content", "d2_chord_learnability", "d2_chord_operability", "d2_chord_easeofuse", "d2_chord_usefulness",
    # heatmap (in order)
    "d2_heatmap_content", "d2_heatmap_learnability", "d2_heatmap_operability", "d2_heatmap_easeofuse", "d2_heatmap_usefulness",
    # hoverlist (in order)
    "d2_hoverlist_content", "d2_hoverlist_learnability", "d2_hoverlist_operability", "d2_hoverlist_easeofuse", "d2_hoverlist_usefulness",
    # line charts (in order)
    "d2_lines_content", "d2_lines_easeofuse", "d2_lines_learnability", "d2_lines_operability", "d2_lines_usefulness",
    # residuals (in order)
    "d2_residuals_content", "d2_residuals_learnability", "d2_residuals_easeofuse",
    # summary pills (in order)
    "d2_pills_learnability", "d2_pills_content", "d2_pills_easeofuse", "d2_pills_operability", "d2_pills_usefulness",
    # open feedback text areas (required)
    "d2_open_chord_feedback", "d2_open_heatmap_feedback", "d2_open_hoverlist_feedback", "d2_open_linecharts_feedback", "d2_open_summary_pills_feedback",
    # dashboard-level questions (in order)
    "d2_overall_ui", "d2_overall_situational_awareness", "d2_overall_satisfaction", "d2_overall_task_suitability", "d2_overall_system_capabilities",

    # post-dashboard questions (in order)
    "post_police_reliability", "post_police_fairness", "post_police_job",
    "post_news_frequency", "post_headline_accuracy",
    "post_headline_inflation", "post_headline_truth", "post_crime_increase",
    "post_crime_most", "post_crime_least", "post_media_least", "post_media_most",
    "post_lowest_boroughs", "post_highest_boroughs",

    # Analytic fields
    "net_change_crime",
    "net_change_media",
    "net_change_boroughs"
]


# Remove duplicate header names while preserving order
_seen = set()
_deduped = []
for h in headers:
    if h not in _seen:
        _deduped.append(h)
        _seen.add(h)
headers = _deduped



LIKERT_7 = [
    "Select an option",
    "Very poor",
    "Poor",
    "Somewhat poor",
    "Neutral",
    "Somewhat good",
    "Good",
    "Very good"
]



def ensure_sheet_headers(worksheet, expected_headers):
    """
    Ensure the worksheet has the expected header row.
    - worksheet: gspread Worksheet object
    - expected_headers: list of header strings in the order you want columns
    Behavior:
      - If the sheet is empty, writes expected_headers as the first row.
      - If a header row exists but does not match expected_headers (case-insensitive),
        overwrites the first row with expected_headers.
    Returns True on success, False on failure.
    """
    try:
        # Get all values; if empty, get_all_values() returns []
        all_values = worksheet.get_all_values()
        if not all_values:
            # Sheet empty — write headers
            worksheet.append_row(expected_headers, value_input_option="USER_ENTERED")
            return True

        # There is at least one row; treat the first row as header row
        existing_header = all_values[0]
        # Normalize both lists for comparison
        norm_existing = [_normalize_header_cell(c) for c in existing_header]
        norm_expected = [_normalize_header_cell(c) for c in expected_headers]

        # If lengths differ or any cell differs, overwrite the first row
        if len(norm_existing) != len(norm_expected) or any(e != x for e, x in zip(norm_existing, norm_expected)):
            # Overwrite first row with expected headers
            # Use A1 update to replace the first row exactly
            worksheet.update("A1", [expected_headers], value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        # Surface helpful error in Streamlit UI or logs
        st.error(f"Failed to ensure headers on sheet '{worksheet.title}': {e}")
        return False

    
# centralised, secure way to build an authorised gspread client from st.secrets.
def _build_gspread_client_from_secrets():
    """
    Build and return an authorized gspread client.
    Accepts either:
      - st.secrets["gcp_service_account"] (nested TOML table -> dict)
      - st.secrets["GCP_SERVICE_ACCOUNT_JSON"] (JSON string)
    """
    creds_info = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON") or st.secrets.get("gcp_service_account")
    if creds_info is None:
        raise RuntimeError("Google service account JSON not found in Streamlit secrets (GCP_SERVICE_ACCOUNT_JSON or gcp_service_account).")

    # Parse secret into a dict
    if isinstance(creds_info, str):
        creds_dict = json.loads(creds_info)
    else:
        creds_dict = dict(creds_info)

    # Fix escaped newlines if present (safe guard)
    if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# TEMPORARY DEBUG: Attempt to create gspread client and open the spreadsheet
# try:
#     client = _build_gspread_client_from_secrets()
#     st.write("DEBUG: gspread client created")
#     sid = st.secrets.get("SPREADSHEET_ID")
#     st.write("DEBUG: SPREADSHEET_ID present:", bool(sid))
#     sh = client.open_by_key(sid)
#     st.write("DEBUG: opened spreadsheet:", sh.title)
#     ws_name = st.secrets.get("SHEET_NAME", "responses")
#     try:
#         ws = sh.worksheet(ws_name)
#         st.write("DEBUG: opened worksheet:", ws.title)
#     except gspread.WorksheetNotFound:
#         st.write("DEBUG: worksheet not found, will create:", ws_name)
#         ws = sh.add_worksheet(title=ws_name, rows="1000", cols="50")
#         st.write("DEBUG: created worksheet:", ws.title)
# except Exception as e:
#     st.error("DEBUG gspread error: " + str(e))
# if creds:
#     creds_dict = json.loads(creds) if isinstance(creds, str) else dict(creds)
#     st.write("DEBUG service account email:", creds_dict.get("client_email"))
# else:
#     st.write("DEBUG: no service account found in st.secrets")
# Save responses to Google Sheets
# def save_rows_to_sheet(rows, headers=headers, spreadsheet_id_secret="SPREADSHEET_ID", sheet_name_secret="SHEET_NAME", spreadsheet_title_secret="SPREADSHEET_TITLE"):
#     """
#     Append rows (list of lists) to Google Sheet.
#     - rows: list of lists (each inner list is a row)
#     - headers: optional list of header strings to write if sheet is empty
#     - secrets used: SPREADSHEET_ID (preferred) or SPREADSHEET_TITLE (fallback), and SHEET_NAME (worksheet title)
#     """
#     try:
#         client = _build_gspread_client_from_secrets()
#         spreadsheet_id = st.secrets.get("SPREADSHEET_ID")
#         if not spreadsheet_id:
#             st.error("SPREADSHEET_ID missing from st.secrets; responses will be saved locally.")
#             # fallback: write to CSV and return
#             for r in rows:
#                 append_row_to_csv(dict(zip(headers, r)))
#             return
        
#         sheet_name = st.secrets.get("SHEET_NAME", "Responses")
#         sh = client.open_by_key(spreadsheet_id)
#         try:
#             ws = sh.worksheet(sheet_name)
#         except gspread.WorksheetNotFound:
#             ws = sh.add_worksheet(title=sheet_name, rows="1000", cols="50")

#         # Ensure headers if provided
#         if headers:
#             ok = ensure_sheet_headers(ws, headers)
#             if not ok:
#                 st.error("Could not ensure headers in the Google Sheet. Aborting save.")
#                 return

#         # Append rows (cleaning values as needed)
#         for row in rows:
#             cleaned = []
#             for v in row:
#                 if v is None:
#                     cleaned.append("")   # or "none"
#                 elif isinstance(v, float) and math.isnan(v):
#                     cleaned.append("")
#                 elif isinstance(v, list):
#                     cleaned.append(";".join(map(str, v)))
#                 else:
#                     cleaned.append(v)
#             ws.append_row(cleaned, value_input_option="USER_ENTERED")

#     except Exception as e:
#         st.error(f"Failed to save responses to Google Sheets: {e}")
#         # fallback: persist locally to CSV to avoid data loss
#         for r in rows:
#             append_row_to_csv(dict(zip(headers, r)))
#         return


# --- normalizer used for Sheets ---
def _norm_value(v):
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    if isinstance(v, list):
        return ";".join(map(str, v))
    return str(v)

def _normalize_header_cell(s):
    if s is None:
        return ""
    return str(s).strip().lower()

# def ensure_sheet_headers(worksheet, expected_headers):
#     """
#     Ensure the worksheet has the expected header row.
#     - If the sheet is empty, writes expected_headers as the first row.
#     - If a header row exists but does not match expected_headers (case-insensitive),
#       overwrites the first row with expected_headers.
#     Returns True on success, False on failure.
#     """
#     try:
#         all_values = worksheet.get_all_values()
#         if not all_values:
#             worksheet.append_row(expected_headers, value_input_option="USER_ENTERED")
#             return True

#         existing_header = all_values[0]
#         norm_existing = [_normalize_header_cell(c) for c in existing_header]
#         norm_expected = [_normalize_header_cell(c) for c in expected_headers]

#         if len(norm_existing) != len(norm_expected) or any(e != x for e, x in zip(norm_existing, norm_expected)):
#             worksheet.update("A1", [expected_headers], value_input_option="USER_ENTERED")
#         return True
#     except Exception as e:
#         st.error(f"Failed to ensure headers on sheet '{getattr(worksheet, 'title', 'unknown')}': {e}")
#         return False

# Build a single row (list) in the exact order of headers list from session_state and grouped caches
def build_row_from_headers(headers_list):
    grouped = {}

    # Merge per-page caches (explicit order)
    for k in ("consent_answers", "pre_answers", "d1_answers", "d2_answers", "post_answers"):
        val = st.session_state.get(k)
        if isinstance(val, dict):
            grouped.update(val)

    # include top-level widget keys that aren't internal caches
    for k, v in st.session_state.items():
        if k.startswith("_") or k in ("consent_answers", "pre_answers", "d1_answers", "d2_answers", "post_answers"):
            continue
        if not callable(v):
            grouped.setdefault(k, v)

    row = []
    for h in headers_list:
        if h == "user_id":
            val = st.session_state.get("user_id") or ""
        elif h == "submission_timestamp_utc":
            val = datetime.utcnow().isoformat() + "Z"
        else:
            val = grouped.get(h, "")
        row.append(_norm_value(val))
    return row



# Save rows to Google Sheets (modified to accept rows as list-of-lists OR list-of-dicts)
def save_rows_to_sheet(rows, headers=headers, spreadsheet_id_secret="SPREADSHEET_ID", sheet_name_secret="SHEET_NAME"):
    """
    Append rows to Google Sheets.
    - rows: list of dicts (header->value) OR list-of-lists (ordered to headers)
    - headers: canonical header list used to ensure sheet columns and ordering
    This function is Google-Sheets-only: it will raise/emit errors if Sheets are not configured.
    """
    # Build client
    client = _build_gspread_client_from_secrets()

    spreadsheet_id = st.secrets.get(spreadsheet_id_secret)
    if not spreadsheet_id:
        raise RuntimeError("SPREADSHEET_ID missing from st.secrets; cannot save to Google Sheets.")

    sheet_name = st.secrets.get(sheet_name_secret, "Responses")
    sh = client.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows="1000", cols="50")

    # Ensure header row matches canonical headers
    if headers:
        ok = ensure_sheet_headers(ws, headers)
        if not ok:
            raise RuntimeError("Could not ensure headers in the Google Sheet.")

    # Normalize and append rows
    for r in rows:
        if isinstance(r, dict):
            ordered = [_norm_value(r.get(h, "")) for h in headers]
        else:
            # list-like: pad/truncate to headers length
            ordered = []
            for i, h in enumerate(headers):
                try:
                    v = r[i]
                except Exception:
                    v = ""
                ordered.append(_norm_value(v))
        ws.append_row(ordered, value_input_option="USER_ENTERED")

  

PLACEHOLDER = "Select an option"

# ---------------------------------------------------------
# INITIAL SETUP
# ---------------------------------------------------------



def init_state():
    """Initialize all session state variables once."""
    if "page" not in st.session_state:
        st.session_state.page = "consent"

    if "pre_consent" not in st.session_state:
        st.session_state.pre_consent = None

    # per-page caches (always dicts)
    if "consent_answers" not in st.session_state:
        st.session_state.consent_answers = {}
    if "pre_answers" not in st.session_state:
        st.session_state.pre_answers = {}

    if "d1_answers" not in st.session_state:
        st.session_state.d1_answers = {}

    if "d2_answers" not in st.session_state:
        st.session_state.d2_answers = {}

    # unique id per session (useful to join rows)
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"

    # optional guard for one-time rerun
    if "_nav_rerun_once" not in st.session_state:
        st.session_state["_nav_rerun_once"] = False



# ---------------------------------------------------------
# PAGE FUNCTIONS
# ---------------------------------------------------------
# SAVE CONSENT AGREEMENT TO CACHE
def page_consent():
    st.title("Consent for Research")

    st.selectbox(
        "I consent to my anonymised responses being used for this research.",
        [PLACEHOLDER, "Yes, I consent", "No, I do not consent"],
        key="pre_consent_select"
    )

    if st.button("Double Click To Continue"):
        choice = st.session_state.get("pre_consent_select")

        if choice == "Yes, I consent":
            # boolean used by app logic
            st.session_state["pre_consent"] = True

            # store the widget value in a dedicated consent cache
            consent_answers = st.session_state.get("consent_answers", {})
            consent_answers["pre_consent_select"] = choice
            st.session_state["consent_answers"] = consent_answers

            st.session_state.page = "preliminary"
            return

        if choice == "No, I do not consent":
            st.session_state["pre_consent"] = False
            consent_answers = st.session_state.get("consent_answers", {})
            consent_answers["pre_consent_select"] = choice
            st.session_state["consent_answers"] = consent_answers

            st.error("You cannot continue until you consent. Please select 'Yes, I consent' to proceed.")
            return

        st.warning("Please select an option before continuing.")
        return





        
# --------------------------------------
# --- GLOBAL VALIDATION HELPERS ---
# ------------------------------------------

# --- Prevent contradictory top-3 selections (place after the multiselect widgets) ---
def _overlap_warning(list_a, list_b):
    """Return list of overlapping items between two lists (or empty list)."""
    if not isinstance(list_a, list) or not isinstance(list_b, list):
        return []
    return list(set(list_a) & set(list_b)) 

# Validation helper
def is_exactly_three(selection):
    return isinstance(selection, list) and len(selection) == 3  
     
def page_preliminary():
    st.set_page_config(page_title="Pre‑Dashboard 2 Survey", layout="wide")
    # At top of each page function (immediately after st.set_page_config / title)
    if st.session_state.get("_nav_rerun_once", False):
        # reset the one-time rerun guard when the target page loads
        st.session_state["_nav_rerun_once"] = False


    st.title("Section 2 – Baseline Understanding")
    st.markdown("Before navigating Dashboard 2, please answer the following questions about crime in London, policing, and media headlines.")

    # --- Require consent before showing anything ---
    if not st.session_state.get("pre_consent", False):
        st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
        st.stop()

     
    st.markdown("---")
    st.header("About You")

    # ---------------- ABOUT YOU ----------------
    st.selectbox(
        "What is your age band?",
        [PLACEHOLDER, "18–24", "25–34", "35–44", "45–54", "55–64", "65+", "Prefer not to say"],
        key="pre_age_band"
    )

    st.selectbox(
        "What is your highest level of education (current or completed)?",
        [
            PLACEHOLDER,
            "GCSE or equivalent",
            "A‑Levels or equivalent",
            "Undergraduate degree",
            "Postgraduate degree",
            "Doctorate",
            "Vocational / Professional qualification",
            "Prefer not to say"
        ],
        key="pre_education"
    )

    boroughs = [
        "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley",
        "Camden", "Croydon", "Ealing", "Enfield", "Greenwich", "Hackney",
        "Hammersmith and Fulham", "Haringey", "Harrow", "Havering", "Hillingdon",
        "Hounslow", "Islington", "Kensington and Chelsea", "Kingston upon Thames",
        "Lambeth", "Lewisham", "Merton", "Newham", "Redbridge", "Richmond upon Thames",
        "Southwark", "Sutton", "Tower Hamlets", "Waltham Forest", "Wandsworth",
        "Westminster", "I don’t live in London"
    ]

    st.selectbox(
        "In which London Borough do you live? If you don’t live in London, in what London Borough do you work or attend school?",
        [PLACEHOLDER] + boroughs,
        key="pre_borough"
    )

    # ---------------- POLICING QUESTIONS ----------------
    st.header("Your Views on Policing in Your Borough")

    policing_scale = [
        PLACEHOLDER,
        "Strongly Agree",
        "Agree",
        "Neutral",
        "Disagree",
        "Strongly Disagree"
    ]

    st.selectbox(
        "The police can be relied upon to be there when needed in your area.",
        policing_scale,
        key="pre_police_reliability"
    )

    st.selectbox(
        "The police treat everyone fairly regardless of who they are in your area.",
        policing_scale,
        key="pre_police_fairness"
    )

    st.selectbox(
        "The police do a good job in your area.",
        policing_scale,
        key="pre_police_job"
    )

    # ---------------- NEWS CONSUMPTION ----------------
    st.header("Your Exposure to Crime Headlines")

    st.selectbox(
        "How often do you read online news about crime in London?",
        [PLACEHOLDER, "Daily", "Several times a week", "Weekly", "Monthly", "Yearly", "Never"],
        key="pre_news_frequency"
    )

    st.selectbox(
        "How accurate do you think online headlines about crime in London are overall?",
        [PLACEHOLDER, "Very inaccurate", "Somewhat inaccurate", "Neither accurate nor inaccurate", "Somewhat accurate", "Very accurate", "Don’t know"],
        key="pre_headline_accuracy"
    )

    # ---------------- PERCEPTION OF HEADLINES ----------------
    st.header("Your Perception of Crime Headlines")

    likert = [
        PLACEHOLDER,
        "Strongly Agree",
        "Agree",
        "Neutral",
        "Disagree",
        "Strongly Disagree"
    ]

    st.selectbox(
        "Online news headlines make me believe crime in my borough is higher than actual crime counts.",
        likert,
        key="pre_headline_inflation"
    )

    st.selectbox(
        "Headlines about crime in London are generally accurate to actual crime counts in my Borough.",
        likert,
        key="pre_headline_truth"
    )

    st.selectbox(
        "In the past 12 months, crime in my Borough has increased.",
        likert,
        key="pre_crime_increase"
    )

    # ---------------- CRIME CATEGORY QUESTIONS ----------------
    st.header("Crime Categories – Your Perception")
    st.subheader("Definitions of Crime Categories")

    crime_definitions = {
        "Fraud and Forgery": "Offences involving deception, false representation, or falsifying documents for personal gain.",
        "Possession of Weapons": "Criminal possession of firearms, knives, or other prohibited weapons.",
        "Drug Offences": "Crimes involving possession, supply, trafficking, or production of illegal drugs.",
        "Gun Crime": "Offences involving the use, threat, or possession of a firearm.",
        "Knife Crime": "Offences involving the use, threat, or possession of a knife or sharp instrument.",
        "Lethal Barrel Discharge": "Incidents where a firearm is discharged, regardless of injury outcome.",
        "Sexual Offences": "Crimes of a sexual nature including rape, assault, exploitation, or indecent acts.",
        "Robbery": "Taking property using force or threat of force, including personal and business robberies.",
        "Violence Against the Person": "Offences involving physical harm, threats, harassment, or dangerous behaviour.",
        "Hate Crime": "Crimes motivated by hostility toward race, religion, disability, sexual orientation, or gender identity.",
        "Arson and Criminal Damage": "Deliberate fire‑setting or intentional destruction/damage of property.",
        "Burglary": "Entering a building illegally to steal property, including residential and commercial burglary.",
        "Public Order Offences": "Crimes involving disorderly behaviour, intimidation, harassment, or causing public alarm.",
        "Domestic Abuse": "Violence, coercion, or controlling behaviour within intimate or family relationships.",
        "Theft": "Taking property without consent, including shoplifting, bicycle theft, and theft from the person.",
        "Vehicle Offences": "Crimes involving theft of or from vehicles, interference with vehicles, or aggravated vehicle taking."
    }

    for cat, desc in crime_definitions.items():
        st.markdown(f"**{cat}** — {desc}")

    crime_categories = list(crime_definitions.keys())

    st.markdown("**Select exactly three options for each question.** If you select more or fewer than three, you will see a warning and cannot continue.")
    #st.markdown("**Select exactly three options for each question.** If you select more or fewer than three, you will see a warning and cannot continue.")

    # ---------------- CRIME CATEGORY QUESTIONS (pre) ----------------
    pre_crime_most = st.multiselect(
        "Select **three** crime categories you believe have the **MOST offences** in your Borough.",
        crime_categories,
        key="pre_crime_most"
    )

    pre_crime_least = st.multiselect(
        "Select **three** crime categories you believe have the **LEAST offences** in your Borough.",
        crime_categories,
        key="pre_crime_least"
    )

    # validate exact-3 selections and check overlaps for crime category selections
    valid_most = is_exactly_three(pre_crime_most)
    valid_least = is_exactly_three(pre_crime_least)

    if not valid_most:
        st.warning("Please select exactly 3 categories for 'MOST offences in your Borough'.")
    if not valid_least:
        st.warning("Please select exactly 3 categories for 'LEAST offences in your Borough'.")

    crime_overlap_most_least = _overlap_warning(pre_crime_most, pre_crime_least)
    if crime_overlap_most_least:
        st.warning(
            "You have selected the same crime categories in both the **MOST offences** and **LEAST offences** lists. "
            "Please choose different categories so the 'most' and 'least' answers are distinct. "
            f"Overlapping items: {', '.join(crime_overlap_most_least)}"
        )

    pre_media_least = st.multiselect(
        "Select **three** crime categories you believe the media covers **THE LEAST** in London headlines.",
        crime_categories,
        key="pre_media_least"
    )

    pre_media_most = st.multiselect(
        "Select **three** crime categories you believe the media covers **MOST PROMINENTLY** in London headlines.",
        crime_categories,
        key="pre_media_most"
    )

    # validate exact-3 selections and check overlaps for media coverage selections
    valid_media_least = is_exactly_three(pre_media_least)
    valid_media_most = is_exactly_three(pre_media_most)

    if not valid_media_least:
        st.warning("Please select exactly 3 categories for 'THE LEAST covered in headlines'.")
    if not valid_media_most:
        st.warning("Please select exactly 3 categories for 'MOST PROMINENTLY covered in headlines'.")

    crime_overlap_media = _overlap_warning(pre_media_most, pre_media_least)
    if crime_overlap_media:
        st.warning(
            "You have selected the same crime categories in both the **MOST PROMINENTLY covered** and **THE LEAST covered** media lists. "
            "Please choose different categories so media coverage answers are distinct. "
            f"Overlapping items: {', '.join(crime_overlap_media)}"
        )


    # ---------------- BOROUGH CRIME PERCEPTION (pre) ----------------
    st.header("Your Perception of Borough Crime Levels")

    pre_lowest_boroughs = st.multiselect(
        "Select **three** boroughs you believe have the **LOWEST** crime offences in London.",
        boroughs[:-1],
        key="pre_lowest_boroughs"
    )

    pre_highest_boroughs = st.multiselect(
        "Select **three** boroughs you believe have the **HIGHEST** crime offences in London.",
        boroughs[:-1],
        key="pre_highest_boroughs"
    )

    # validate borough selections and check overlap
    valid_lowest_boroughs = is_exactly_three(pre_lowest_boroughs)
    valid_highest_boroughs = is_exactly_three(pre_highest_boroughs)

    if not valid_lowest_boroughs:
        st.warning("Please select exactly 3 boroughs for the LOWEST crime question.")
    if not valid_highest_boroughs:
        st.warning("Please select exactly 3 boroughs for the HIGHEST crime question.")

    boroughs_overlap = _overlap_warning(pre_lowest_boroughs, pre_highest_boroughs)
    if boroughs_overlap:
        st.warning(
            "You have selected the same borough(s) for both the **LOWEST** and **HIGHEST** crime questions. "
            "Please select different boroughs for each question. "
            f"Overlapping items: {', '.join(boroughs_overlap)}"
        )

    # ---------------- CONTINUE BUTTON ----------------
    if st.button("Double Click To Continue to Dashboard 1"):
        # All required keys for the preliminary page (only enforced here)
        required_selects = [
            "pre_age_band", "pre_education", "pre_borough",
            "pre_police_reliability", "pre_police_fairness", "pre_police_job",
            "pre_news_frequency", "pre_headline_accuracy",
            "pre_headline_inflation", "pre_headline_truth", "pre_crime_increase",
            "pre_crime_most", "pre_crime_least", "pre_media_least", "pre_media_most",
            "pre_lowest_boroughs", "pre_highest_boroughs"
        ]

        # Treat placeholder, None, empty list, empty string, False as missing
        missing = [
            k for k in required_selects
            if st.session_state.get(k) in (None, PLACEHOLDER, [], "", False)
        ]

        
        overlap_errors = []
        if _overlap_warning(st.session_state.get("pre_crime_most", []), st.session_state.get("pre_crime_least", [])):
            overlap_errors.append("Same categories selected for MOST and LEAST offences.")
        if _overlap_warning(st.session_state.get("pre_media_most", []), st.session_state.get("pre_media_least", [])):
            overlap_errors.append("Same categories selected for MOST and LEAST media coverage.")
        if _overlap_warning(st.session_state.get("pre_lowest_boroughs", []), st.session_state.get("pre_highest_boroughs", [])):
            overlap_errors.append("Same boroughs selected for LOWEST and HIGHEST crime.")
        if overlap_errors:
            st.error("Please resolve the following contradictions before continuing:")
            for e in overlap_errors:
                st.write(f"- {e}")
            return

        if missing:
            st.error("Please answer all required questions before continuing. The following items are incomplete:")
            for k in missing:
                label = k.replace("pre_", "").replace("_", " ").capitalize()
                st.write(f"- {label}: {repr(st.session_state.get(k))}")
            st.info("Scroll up to complete the unanswered questions.")
            return

        # Validate exact-3 multiselects and borough selections
        if not (valid_most and valid_least and valid_media_least and valid_media_most):
            st.error("Please ensure all 'select three' questions have exactly three selections.")
            return

        if not (len(pre_lowest_boroughs) == 3 and len(pre_highest_boroughs) == 3):
            st.error("Please select exactly 3 boroughs for both the LOWEST and HIGHEST crime questions.")
            return

        # After all checks pass in page_preliminary()
        pre_keys = [
            "pre_age_band", "pre_education", "pre_borough",
            "pre_police_reliability", "pre_police_fairness", "pre_police_job",
            "pre_news_frequency", "pre_headline_accuracy",
            "pre_headline_inflation", "pre_headline_truth", "pre_crime_increase",
            "pre_crime_most", "pre_crime_least", "pre_media_least", "pre_media_most",
            "pre_lowest_boroughs", "pre_highest_boroughs"
        ]

        # Cache the pre answers as a single dict in session_state
        st.session_state["pre_answers"] = {k: st.session_state.get(k) for k in pre_keys}


        # Navigate to next page
        st.session_state.page = "d1_preview"
        if not st.session_state.get("_nav_rerun_once", False):
            st.session_state["_nav_rerun_once"] = True
            # st.experimental_rerun()
        return


def d1_page_preview():
    """
    Preview page for Dashboard 1.
    Shows an image/link and a checkbox that enables the Continue button.
    """
    # keep page config at app top-level; don't call set_page_config here
    if st.session_state.get("_nav_rerun_once", False):
        st.session_state["_nav_rerun_once"] = False

    st.title("Open Dashboard 1 (Preview)")
    st.markdown("Please open the Dashboard 1 interface in a new tab, inspect it, then return here and click Continue to answer questions about it.")

    # --- Dashboard image (optional) ---
    image_url = "https://github.com/eboniethomas16/Crime-Perception-Headlines-Visual-Dashboard/blob/main/dashboard_survey/photos/d1_dashboard.png"
    try:
        st.image(image_url, caption="Dashboard 1 preview", use_column_width=True)
    except Exception:
        pass

    st.markdown("---")

    # --- Link to open the live dashboard in a new tab ---
    dashboard_url = "https://your-dashboard-hosting.example.com/dashboard1"
    st.markdown(
        f'<a href="{dashboard_url}" target="_blank" rel="noopener noreferrer" style="font-size:16px;">'
        f'Open Dashboard 1 in a new tab</a>',
        unsafe_allow_html=True
    )

    st.markdown("**Important:** the link opens in a new tab. After the dashboard opens, return to this tab and confirm below.")

    # --- Confirmation checkbox to ensure user opened the dashboard ---
    opened = st.checkbox("I have opened Dashboard 1 in a new tab", key="d1_preview_opened")

    # --- Continue button enabled only after checkbox is checked ---
    if opened:
        if st.button("Continue to Dashboard 1 questions", key="d1_preview_continue"):
            st.session_state.page = "dashboard1"
            return
    else:
        st.info("Please open the dashboard in a new tab and check the box to continue.")



def page_dashboard1():
    st.set_page_config(page_title="Dashboard 1 – Perception vs Crime", layout="wide")
    if st.session_state.get("_nav_rerun_once", False):
            # reset the one-time rerun guard when the target page loads
            st.session_state["_nav_rerun_once"] = False

    st.title("Dashboard 1 – Perception vs Crime")
    st.markdown("Please answer the questions below about Dashboard 1. All single-choice items start unselected.")

     

    # ---------------- BIVARIATE CHOROPLETH MAP ----------------
    st.header("Bivariate Choropleth Map")

    st.selectbox(
        "How accurate and trustworthy did the map's values and colour encoding appear?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d1_bivmap_content"
    )

    st.selectbox(
        "How clear was the **legend** and **map** at communicating the two variables (crime count and perception) at a glance?",
        [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
        key="d1_bivmap_learnability"
    )

    st.selectbox(
        "How easy was it to find and interpret a specific borough on the map?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_bivmap_easeofuse"
    )

    st.selectbox(
        "How easy was it to interact with the map without confusion(i.e. hover highlighting, click selection)?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_bivmap_operability"
    )

    st.selectbox(
        "How useful was the map for identifying boroughs where perception and crime diverge?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d1_bivmap_usefulness"
    )

    st.text_area("REQUIRED: If you have any additional comments about the bivariate choropleth map, please share them here:", key="d1_open_chord_feedback")


    # ---------------- HEATMAP ----------------
    st.header("Heatmap (Perception vs Crime)")

    st.selectbox(
        "How accurate and informative were the heatmap values and tooltips?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d1_heatmap_content"
    )

    st.selectbox(
        "How easy was it to comprehend the information shown on the heatmap?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_heatmap_learnability"
    )

    st.selectbox(
        "How easy was it to interact with the heatmap (hover time periods, select/unselect borough, scrollbar)?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_heatmap_operability"
    )

    st.selectbox(
        "How easy was it to locate a specific crime and month in the heatmap?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_heatmap_easeofuse"
    )

    st.selectbox(
        "How useful was the heatmap for identifying where the chosen perception metric over‑ or under‑estimated crime by category and time compared with actual crime?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d1_heatmap_usefulness"
    )

    st.text_area("REQUIRED: If you have any additional comments about the heatmap, please share them here:", key="d1_open_heatmap_feedback")


    # ---------------- HOVER LIST ----------------
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
        "How easy was it to control hover interactions on the line charts and heatmap to change hoverlist values and avoid accidental selections?",
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

    st.text_area("REQUIRED: If you have any additional comments about the hoverlist, please share them here:", key="d1_open_hoverlist_feedback")


    # ---------------- LINE CHARTS ----------------
    st.header("Line Charts")

    st.selectbox(
        "How accurate and clear were the values and scales on the crime, perception, and residuals line charts (e.g., axes, labels)?",
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
        "How easy was it to use the interactive features on the line charts(e.g., hoverline, zoom controls, Show/Hide residual button)?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_lines_operability"
    )

    st.selectbox(
        "How useful were the line charts for understanding trends and spikes over time?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d1_lines_usefulness"
    )

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
        "How easy was it to spot the largest residual spikes for a selected borough?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_residuals_easeofuse"
    )

    st.text_area("REQUIRED: If you have any additional comments about any of the line charts, please share them here:", 
                 key="d1_open_linecharts_feedback")



    # ---------------- SUMMARY PILLS ----------------
    st.header("Summary Pills and Selection Dropdown")

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
        "How easy was it to select the perception metrics and boroughs in the dropdown list at the top of the page?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_pills_operability"
    )

    st.selectbox(
        "How useful were the summary pills for forming an initial judgement about the selected boroughs?",
        [PLACEHOLDER, "Very Useful", "Mostly Useful", "Somewhat Useful", "Not really Useful", "Not Useful at all"],
        key="d1_pills_usefulness"
    )

    st.text_area("REQUIRED: If you have any additional comments about the summary pills, please share them here:", key="d1_open_summary_pills_feedback")

    # ---------------- DASHBOARD LEVEL ----------------
    st.header("Dashboard-Level Questions")

    st.selectbox(
    "How effective were the dashboard’s visualization tools (bivariate map, heatmap, line charts, hoverlist, summary pills) at helping you read and interpret the data?",
        LIKERT_7,
        key="d1_overall_ui"
        )

    st.selectbox(
        "How well did the dashboard support situational awareness by representing instability, conveying complexity and variability, drawing attention to important changes in the data reducing mental effort, and enabling monitoring of multiple boroughs at once?",
        LIKERT_7,
        key="d1_overall_situational_awareness"
    )

    st.selectbox(
        "Overall, how satisfied are you with this dashboard, including comfort using it, the user interface, and the available features and capabilities?",
        LIKERT_7,
        key="d1_overall_satisfaction"
    )

    st.selectbox(
        "How well does the dashboard support your regular tasks by organising information to match your work, fitting screen content to task needs, and allowing you to set or customise output/report displays for your tasks?",
        LIKERT_7,
        key="d1_overall_task_suitability"
    )

    st.selectbox(
        "How well does the system meet expectations (i.e. readable sizing of each chart component, responsiveness (speed), and integration of features so they work together smoothly?)",
        LIKERT_7,
        key="d1_overall_system_capabilities"
    )

    required_d1 = []
    # ---------------- CONTINUE BUTTON + VALIDATION ----------------
    st.markdown("---")
    st.write("When you're done, click Continue to proceed to Dashboard 2.")

    if st.button("Double Click To Continue to Dashboard 2"):
        # list all required d1_ keys (already defined above)
        required_d1 = [
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
            "d1_pills_operability", "d1_pills_usefulness",
            # --- open feedback text areas (required) ---
            "d1_open_chord_feedback", "d1_open_heatmap_feedback",
            "d1_open_hoverlist_feedback", "d1_open_linecharts_feedback",
            "d1_open_summary_pills_feedback",
            # --- dashboard-level questions ---
            "d1_overall_ui", "d1_overall_situational_awareness",
            "d1_overall_satisfaction", "d1_overall_task_suitability", "d1_overall_system_capabilities"
        ]

        def is_missing_value(val, placeholder=PLACEHOLDER):
            if val is None:
                return True
            if isinstance(val, str) and val.strip() == "":
                return True
            if isinstance(val, list) and len(val) == 0:
                return True
            if val == placeholder:
                return True
            return False

        missing = [k for k in required_d1 if is_missing_value(st.session_state.get(k, None))]
        if missing:
            st.error("Please answer all required questions before continuing. The following items are incomplete:")
            for k in missing:
                label = k.replace("d1_", "").replace("_", " ").capitalize()
                st.write(f"- {label}: {repr(st.session_state.get(k, ''))}")
            st.info("Scroll up to complete the unanswered questions.")
            return

        # Build and cache Dashboard 1 answers (per-page only)
        d1_answers = {k: st.session_state.get(k) for k in required_d1}
        st.session_state["d1_answers"] = d1_answers

        # Navigate to next page (no save)
        st.success("All Dashboard 1 questions complete. Redirecting to Dashboard 2...")
        st.session_state.page = "dashboard2"
        return





def page_dashboard2():
    st.set_page_config(page_title="Dashboard 2 – Headlines vs Crime", layout="wide")
    if st.session_state.get("_nav_rerun_once", False):
            # reset the one-time rerun guard when the target page loads
            st.session_state["_nav_rerun_once"] = False
    st.title("Dashboard 2 – Headlines vs Crime")
    st.markdown("Please answer the questions below about Dashboard 2. YOU MUST ANSWER ALL QUESTIONS BEFORE CONTINUING.")

     

    # --- Require consent before showing anything ---
    if not st.session_state.get("pre_consent", False):
        st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
        if st.button("Go to Consent page"):
            st.experimental_set_query_params(page="Consent")
            return
        st.stop()

    # ---------------- CHORD CHART ----------------
    st.header("Chord Chart")
    st.markdown("Please answer **ALL** questions below about the Chord Chart")

    st.selectbox(
        "How accurate and informative were the chord chart values and tooltips?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d2_chord_content"
    )

    st.selectbox(
        "How clear was the chord chart at showing where crime category co-occurrences in crime news happen in headlines?",
        [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
        key="d2_chord_learnability"
    )

    st.selectbox(
        "How easy was it to interact with the chord chart (hover over internal ribbons, hover over outer arcs, read tooltips)?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_chord_operability"
    )

    st.selectbox(
        "How easy was it to locate a specific crime category in the chord chart?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_chord_easeofuse"
    )

    st.selectbox(
        "How useful was the chord chart for spotting crime category co-occurrences in crime news headlines?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d2_chord_usefulness"
    )

    
    st.text_area("REQUIRED: If you have any additional comments about the chord chart, please share them here:", key="d2_open_chord_feedback")

    # ---------------- HEATMAP ----------------
    st.header("Heatmap (Headlines vs Crime)")
    st.markdown("Please answer **ALL** questions below about the Heatmap")

    st.selectbox(
        "How accurate and informative were the heatmap values and tooltips?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d2_heatmap_content"
    )

    st.selectbox(
        "How easy was it to interact with the heatmap (hover time periods, select/unselect crime categories, scrollbar)?",
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
        "How useful was the heatmap for identifying where headlines over‑ or under‑estimate crime by category and time compared with actual crime?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d2_heatmap_usefulness"
    )

    st.text_area("REQUIRED: If you have any additional comments about the heatmap, please share them here:", key="d2_open_heatmap_feedback")

    # ---------------- HOVER LIST ----------------
    st.header("Hoverlist (Headlines, Crime, Perception, Residuals)")

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
        "How easy was it to control hover interactions on the line charts and heatmap to change hoverlist values and avoid accidental selections?",
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

    st.text_area("REQUIRED: If you have any additional comments about the hoverlist, please share them here:", key="d2_open_hoverlist_feedback")

    # ---------------- LINE CHARTS ----------------
    st.header("Line Charts (headlines, crime, perception, residuals)")

    st.selectbox(
        "How accurate and clear were the values and scales on the crime, headlines, perception, and residuals line charts (e.g., axes, labels)?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d2_lines_content"
    )

    st.selectbox(
        "How easy was it to compare multiple series (crime, perception, headlines, & residuals) on the line charts?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_lines_easeofuse"
    )

    st.selectbox(
        "How easy was it to read and compare the line charts (crime; perception; headlines; residuals) together?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_lines_learnability"
    )

    st.selectbox(
        "How easy was it to use the interactive features on the line charts(e.g., hoverline, zoom controls, perception metric list, Show/Hide residual button)?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_lines_operability"
    )

    st.selectbox(
        "How useful were the line charts for understanding trends and spikes over time?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d2_lines_usefulness"
    )


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

    st.text_area("REQUIRED: If you have any additional comments about the any of the line charts, please share them here:", key="d2_open_linecharts_feedback")
    

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
        [PLACEHOLDER, "Very Useful", "Mostly Useful", "Somewhat Useful", "Not really Useful", "Not Useful at all"],
        key="d2_pills_usefulness"
    )

    st.text_area("Open feedback — SUMMARY PILLS", key="d2_open_summary_pills_feedback")

    # ---------------- DASHBOARD LEVEL ----------------
    st.header("Dashboard-Level Questions")

    # Dashboard 2 widgets (keys start with d2_) using the requested wording
    st.selectbox(
        "How effective were the dashboard’s visualization tools (chord chart, heatmap, line charts, hoverlist, summary pills) at helping you read and interpret the data?",
        LIKERT_7,
        key="d2_overall_ui"
    )

    st.selectbox(
        "How well did the dashboard support situational awareness by representing instability, conveying complexity and variability, drawing attention to important changes in the data, reducing mental effort, and enabling monitoring of multiple boroughs at once?",
        LIKERT_7,
        key="d2_overall_situational_awareness"
    )

    st.selectbox(
        "Overall, how satisfied are you with this dashboard, including comfort using it, the user interface, and the available features and capabilities?",
        LIKERT_7,
        key="d2_overall_satisfaction"
    )

    st.selectbox(
        "How well does the dashboard support your regular tasks by organising information to match your work, fitting screen content to task needs, and allowing you to set or customise output/report displays for your tasks?",
        LIKERT_7,
        key="d2_overall_task_suitability"
    )

    st.selectbox(
        "How well does the system meet expectations (i.e. readable sizing of each chart component, responsiveness (speed), and integration of features so they work together smoothly?)",
        LIKERT_7,
        key="d2_overall_system_capabilities"
    )


    st.markdown("---")
    st.write("When you're done, click Finish to complete the survey and go to the Thank You page.")

    # ---------------- CONTINUE / FINISH BUTTON + VALIDATION ----------------
    if st.button("Double Click To Go To Post Survey Questions"):
        # Validate required d2_ keys (including open feedback text areas)
        required_d2 = [
            # chord chart (in order)
            "d2_chord_content", "d2_chord_learnability", "d2_chord_operability", "d2_chord_easeofuse", "d2_chord_usefulness",
            # heatmap (in order)
            "d2_heatmap_content", "d2_heatmap_learnability", "d2_heatmap_operability", "d2_heatmap_easeofuse", "d2_heatmap_usefulness",
            # hoverlist (in order)
            "d2_hoverlist_content", "d2_hoverlist_learnability", "d2_hoverlist_operability", "d2_hoverlist_easeofuse", "d2_hoverlist_usefulness",
            # line charts (in order)
            "d2_lines_content", "d2_lines_easeofuse", "d2_lines_learnability", "d2_lines_operability", "d2_lines_usefulness",
            # residuals (in order)
            "d2_residuals_content", "d2_residuals_learnability", "d2_residuals_easeofuse",
            # summary pills (in order)
            "d2_pills_learnability", "d2_pills_content", "d2_pills_easeofuse", "d2_pills_operability", "d2_pills_usefulness",
            # open feedback text areas (required)
            "d2_open_chord_feedback", "d2_open_heatmap_feedback", "d2_open_hoverlist_feedback", "d2_open_linecharts_feedback", "d2_open_summary_pills_feedback",
            # dashboard-level questions (in order)
            "d2_overall_ui", "d2_overall_situational_awareness", "d2_overall_satisfaction", "d2_overall_task_suitability", "d2_overall_system_capabilities"
        ]

        # same missing-value check used in Dashboard 1
        def is_missing_value(val, placeholder=PLACEHOLDER):
            if val is None:
                return True
            if isinstance(val, str) and val.strip() == "":
                return True
            if isinstance(val, list) and len(val) == 0:
                return True
            if val == placeholder:
                return True
            return False

        missing_d2 = [k for k in required_d2 if is_missing_value(st.session_state.get(k, None))]
        if missing_d2:
            st.error("Please answer all required Dashboard 2 questions before finishing. The following items are incomplete:")
            for k in missing_d2:
                label = k.replace("d2_", "").replace("_", " ").capitalize()
                st.write(f"- {label}: {repr(st.session_state.get(k, ''))}")
            st.info("Scroll up to complete the unanswered questions.")
            return

        # Build and cache Dashboard 2 answers (per-page only)
        d2_answers = {k: st.session_state.get(k) for k in required_d2}
        st.session_state["d2_answers"] = d2_answers

        # Navigate to post survey (no save)
        st.success("All Dashboard 2 questions complete. Redirecting to Post Survey Questions...")
        st.session_state.page = "post_questions"
        return

    # # -------------------------
    # # Build and cache Dashboard 2 answers (per-page cache only)
    # # -------------------------
    # d2_keys = required_d2
    # d2_answers = {k: st.session_state.get(k) for k in d2_keys}
    # st.session_state["d2_answers"] = d2_answers


    # # Navigate to post survey
    # st.success("All Dashboard 2 questions complete. Redirecting to Post Survey Questions...")
    # st.session_state.page = "post_questions"
    # return
        

# USE TO COMPUTE NET CHANGE IN MOST/LEAST SELECTED CATEGORIES (POST vs PRE)
def _score_selection(categories, most, least):
    """Return dict mapping category -> score (+1 if in most, -1 if in least)."""
    s = {c: 0 for c in categories}
    for c in (most or []):
        if c in s:
            s[c] += 1
    for c in (least or []):
        if c in s:
            s[c] -= 1
    return s

def compute_net_change(categories, pre_most, pre_least, post_most, post_least):
    """Compute net change = sum(post_scores - pre_scores) across all categories (integer)."""
    pre_scores = _score_selection(categories, pre_most, pre_least)
    post_scores = _score_selection(categories, post_most, post_least)
    net = sum(post_scores[c] - pre_scores.get(c, 0) for c in categories)
    return int(net)
def page_post_questions():
     
    st.set_page_config(page_title="Post‑Dashboard 2 Survey", layout="wide")
    if st.session_state.get("_nav_rerun_once", False):
            # reset the one-time rerun guard when the target page loads
            st.session_state["_nav_rerun_once"] = False
    st.title("Section 3 – Post Dashboard Survey - Change in Understanding")
    st.markdown("After viewing the dashboards, please answer the following questions about policing, headlines, and your perceptions. These mirror the baseline questions so we can measure any change in understanding.")

    # Require consent
    if not st.session_state.get("pre_consent", False):
        st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
        if st.button("Go to Consent page"):
            st.session_state.page = "consent"
            return
        st.stop()

    # ---------------- POLICING QUESTIONS (post) ----------------
    st.header("Your Views on Policing in Your Borough (after viewing dashboards)")

    policing_scale = [
        PLACEHOLDER,
        "Strongly Agree",
        "Agree",
        "Neutral",
        "Disagree",
        "Strongly Disagree"
    ]
    st.selectbox(
        "After viewing the dashboards, to what extent do you agree: The police can be relied upon to be there when needed in your area?",
        policing_scale,
        key="post_police_reliability"
    )

    st.selectbox(
        "After viewing the dashboards, to what extent do you agree: The police treat everyone fairly regardless of who they are in your area?",
        policing_scale,
        key="post_police_fairness"
    )

    st.selectbox(
        "After viewing the dashboards, to what extent do you agree: The police do a good job in your area?",
        policing_scale,
        key="post_police_job"
    )

    # ---------------- NEWS CONSUMPTION (post) ----------------
    st.header("Your Exposure to Crime Headlines (after viewing dashboards)")

    st.selectbox(
        "After viewing the dashboards, how often do you expect to read online news about crime in London?",
        [PLACEHOLDER, "Daily", "Several times a week", "Weekly", "Monthly", "Yearly", "Never"],
        key="post_news_frequency"
    )

    st.selectbox(
        "After viewing the dashboards, how accurate do you think online headlines about crime in London are overall?",
        [PLACEHOLDER, "Very inaccurate", "Somewhat inaccurate", "Neither accurate nor inaccurate", "Somewhat accurate", "Very accurate", "Don’t know"],
        key="post_headline_accuracy"
    )

    # ---------------- PERCEPTION OF HEADLINES (post) ----------------
    st.header("Your Perception of Crime Headlines (after viewing dashboards)")

    likert = [
        PLACEHOLDER,
        "Strongly Agree",
        "Agree",
        "Neutral",
        "Disagree",
        "Strongly Disagree"
    ]

    st.selectbox(
        "After viewing the dashboards, do online news headlines make you believe crime in your borough is higher than actual crime counts?",
        likert,
        key="post_headline_inflation"
    )

    st.selectbox(
        "After viewing the dashboards, do you think headlines about crime in London are generally accurate to actual crime counts in your Borough?",
        likert,
        key="post_headline_truth"
    )

    st.selectbox(
        "After viewing the dashboards, do you think crime in your Borough has increased in the past 12 months?",
        likert,
        key="post_crime_increase"
    )

    # ---------------- CRIME CATEGORY QUESTIONS (post) ----------------
    st.header("Crime Categories – Your Perception (after viewing dashboards)")

    st.subheader("Definitions of Crime Categories")

    crime_definitions = {
        "Fraud and Forgery": "Offences involving deception, false representation, or falsifying documents for personal gain.",
        "Possession of Weapons": "Criminal possession of firearms, knives, or other prohibited weapons.",
        "Drug Offences": "Crimes involving possession, supply, trafficking, or production of illegal drugs.",
        "Gun Crime": "Offences involving the use, threat, or possession of a firearm.",
        "Knife Crime": "Offences involving the use, threat, or possession of a knife or sharp instrument.",
        "Lethal Barrel Discharge": "Incidents where a firearm is discharged, regardless of injury outcome.",
        "Sexual Offences": "Crimes of a sexual nature including rape, assault, exploitation, or indecent acts.",
        "Robbery": "Taking property using force or threat of force, including personal and business robberies.",
        "Violence Against the Person": "Offences involving physical harm, threats, harassment, or dangerous behaviour.",
        "Hate Crime": "Crimes motivated by hostility toward race, religion, disability, sexual orientation, or gender identity.",
        "Arson and Criminal Damage": "Deliberate fire‑setting or intentional destruction/damage of property.",
        "Burglary": "Entering a building illegally to steal property, including residential and commercial burglary.",
        "Public Order Offences": "Crimes involving disorderly behaviour, intimidation, harassment, or causing public alarm.",
        "Domestic Abuse": "Violence, coercion, or controlling behaviour within intimate or family relationships.",
        "Theft": "Taking property without consent, including shoplifting, bicycle theft, and theft from the person.",
        "Vehicle Offences": "Crimes involving theft of or from vehicles, interference with vehicles, or aggravated vehicle taking."
    }

    for cat, desc in crime_definitions.items():
        st.markdown(f"**{cat}** — {desc}")


    crime_categories = [
        "Fraud and Forgery", "Possession of Weapons", "Drug Offences", "Gun Crime",
        "Knife Crime", "Lethal Barrel Discharge", "Sexual Offences", "Robbery",
        "Violence Against the Person", "Hate Crime", "Arson and Criminal Damage",
        "Burglary", "Public Order Offences", "Domestic Abuse", "Theft",
        "Vehicle Offences"
    ]
    # ---------------- CRIME CATEGORY QUESTIONS (post) ----------------
    st.markdown("**Select exactly three options for each question.** If you select more or fewer than three, you will see a warning and cannot continue.")
    
    post_crime_most = st.multiselect(
    "After viewing the dashboards, select **three** crime categories you believe have the **MOST offences** in your Borough.",
    crime_categories,
    key="post_crime_most"
    )

    post_crime_least = st.multiselect(
        "After viewing the dashboards, select **three** crime categories you believe have the **LEAST offences** in your Borough.",
        crime_categories,
        key="post_crime_least"
    )

    # Validate exact-3 selections immediately after widget creation
    post_valid_most = is_exactly_three(post_crime_most)
    post_valid_least = is_exactly_three(post_crime_least)

    if not post_valid_most:
        st.warning("Please select exactly 3 categories for 'MOST offences in your Borough' (post).")
    if not post_valid_least:
        st.warning("Please select exactly 3 categories for 'LEAST offences in your Borough' (post).")

    # Overlap check (most vs least)
    post_crime_overlap_most_least = _overlap_warning(post_crime_most, post_crime_least)
    if post_crime_overlap_most_least:
        st.warning(
            "You have selected the same crime categories in both the **MOST offences** and **LEAST offences** lists (post). "
            "Please choose different categories so the 'most' and 'least' answers are distinct. "
            f"Overlapping items: {', '.join(post_crime_overlap_most_least)}"
        )

    post_media_least = st.multiselect(
        "After viewing the dashboards, select **three** crime categories you believe the media covers **THE LEAST** in London headlines.",
        crime_categories,
        key="post_media_least"
    )

    post_media_most = st.multiselect(
        "After viewing the dashboards, select **three** crime categories you believe the media covers **MOST PROMINENTLY** in London headlines.",
        crime_categories,
        key="post_media_most"
    )

    # Validate media exact-3 selections
    post_valid_media_least = is_exactly_three(post_media_least)
    post_valid_media_most = is_exactly_three(post_media_most)

    if not post_valid_media_least:
        st.warning("Please select exactly 3 categories for 'THE LEAST covered in headlines' (post).")
    if not post_valid_media_most:
        st.warning("Please select exactly 3 categories for 'MOST PROMINENTLY covered in headlines' (post).")

    # Overlap check for media lists
    post_crime_overlap_media = _overlap_warning(post_media_most, post_media_least)
    if post_crime_overlap_media:
        st.warning(
            "You have selected the same crime categories in both the **MOST PROMINENTLY covered** and **THE LEAST covered** media lists (post). "
            "Please choose different categories so media coverage answers are distinct. "
            f"Overlapping items: {', '.join(post_crime_overlap_media)}"
        )

    
    # ---------------- BOROUGH CRIME PERCEPTION (post) ----------------
    st.header("Your Perception of Borough Crime Levels (after viewing dashboards)")

    boroughs = [
        "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley",
        "Camden", "Croydon", "Ealing", "Enfield", "Greenwich", "Hackney",
        "Hammersmith and Fulham", "Haringey", "Harrow", "Havering", "Hillingdon",
        "Hounslow", "Islington", "Kensington and Chelsea", "Kingston upon Thames",
        "Lambeth", "Lewisham", "Merton", "Newham", "Redbridge", "Richmond upon Thames",
        "Southwark", "Sutton", "Tower Hamlets", "Waltham Forest", "Wandsworth",
        "Westminster"
    ]

    post_lowest_boroughs = st.multiselect(
    "After viewing the dashboards, select **three** boroughs you believe have the **LOWEST** crime offences in London.",
    boroughs,
    key="post_lowest_boroughs"
    )

    post_highest_boroughs = st.multiselect(
        "After viewing the dashboards, select **three** boroughs you believe have the **HIGHEST** crime offences in London.",
        boroughs,
        key="post_highest_boroughs"
    )

    # Validate borough selections immediately
    post_valid_lowest_boroughs = is_exactly_three(post_lowest_boroughs)
    post_valid_highest_boroughs = is_exactly_three(post_highest_boroughs)

    if not post_valid_lowest_boroughs:
        st.warning("Please select exactly 3 boroughs for the LOWEST crime question (post).")
    if not post_valid_highest_boroughs:
        st.warning("Please select exactly 3 boroughs for the HIGHEST crime question (post).")

    # Overlap between post lowest and post highest (contradiction)
    post_boroughs_overlap = _overlap_warning(post_lowest_boroughs, post_highest_boroughs)
    if post_boroughs_overlap:
        st.warning(
            "You have selected the same borough(s) for both the **LOWEST** and **HIGHEST** crime questions (post). "
            "Please select different boroughs for each question. "
            f"Overlapping items: {', '.join(post_boroughs_overlap)}"
        )

    # --- read pre answers safely (may be None if missing) ---
    pre_answers = st.session_state.get("pre_answers", {}) or {}
    pre_crime_most = pre_answers.get("pre_crime_most", []) or []
    pre_crime_least = pre_answers.get("pre_crime_least", []) or []
    pre_media_most = pre_answers.get("pre_media_most", []) or []
    pre_media_least = pre_answers.get("pre_media_least", []) or []
    pre_lowest_boroughs = pre_answers.get("pre_lowest_boroughs", []) or []
    pre_highest_boroughs = pre_answers.get("pre_highest_boroughs", []) or []
                   

    # ---------------- VALIDATION HELPERS ----------------
    #Validate multiselect counts (post)
    # def is_exactly_three(selection):
    #     return isinstance(selection, list) and len(selection) == 3

    if not (is_exactly_three(post_crime_most) 
            and is_exactly_three(post_crime_least)
            and is_exactly_three(post_media_least) 
            and is_exactly_three(post_media_most)):
        st.warning("Please select exactly 3 categories for each of the 'select three' questions (post).")

    post_overlap_errors = []
    if _overlap_warning(st.session_state.get("post_crime_most", []), st.session_state.get("post_crime_least", [])):
        post_overlap_errors.append("Same categories selected for MOST and LEAST offences (post).")
    if _overlap_warning(st.session_state.get("post_media_most", []), st.session_state.get("post_media_least", [])):
        post_overlap_errors.append("Same categories selected for MOST and LEAST media coverage (post).")
    if _overlap_warning(st.session_state.get("post_lowest_boroughs", []), st.session_state.get("post_highest_boroughs", [])):
        post_overlap_errors.append("Same boroughs selected for LOWEST and HIGHEST crime (post).")
    if post_overlap_errors:
        st.error("Please resolve the following contradictions before continuing:")
        for e in post_overlap_errors:
            st.write(f"- {e}")
        return

    def is_missing(val, placeholder=PLACEHOLDER):
        if val is None:
            return True
        if isinstance(val, str) and val.strip() == "":
            return True
        if isinstance(val, list) and len(val) == 0:
            return True
        if val == placeholder:
            return True
        return False

    # ---------- Required keys (post) ----------
    required_post_selects = [
        "post_police_reliability", "post_police_fairness", "post_police_job",
        "post_news_frequency", "post_headline_accuracy",
        "post_headline_inflation", "post_headline_truth", "post_crime_increase",
        "post_crime_most", "post_crime_least", "post_media_least", "post_media_most",
        "post_lowest_boroughs", "post_highest_boroughs"
    ]

    # ---------- Finish handler ----------
    st.markdown("---")
    st.write("When you're done, click Finish to complete the survey and go to the Thank You page.")

    if st.button("Double Click to Finish Survey"):
    # 1) basic post required fields
        missing_post = [k for k in required_post_selects if is_missing(st.session_state.get(k))]
        if missing_post:
            st.error("Please answer all required post‑dashboard questions before finishing.")
            for k in missing_post:
                label = k.replace("post_", "").replace("_", " ").capitalize()
                st.write(f"- {label}: {repr(st.session_state.get(k))}")
            st.stop()

        # 2) exact-3 checks
        if not (is_exactly_three(st.session_state.get("post_crime_most")) and
                is_exactly_three(st.session_state.get("post_crime_least")) and
                is_exactly_three(st.session_state.get("post_media_least")) and
                is_exactly_three(st.session_state.get("post_media_most"))):
            st.error("Please ensure all 'select three' post questions have exactly three selections.")
            st.stop()

        # 3) borough checks
        if not (len(st.session_state.get("post_lowest_boroughs", [])) == 3 and
                len(st.session_state.get("post_highest_boroughs", [])) == 3):
            st.error("Please select exactly 3 boroughs for both the LOWEST and HIGHEST crime questions (post).")
            st.stop()

        # 4) ensure pre answers cached
        pre_answers = st.session_state.get("pre_answers", {})
        if not pre_answers:
            st.error("Preliminary responses are missing. Please complete the pre‑survey questions first.")
            if st.button("Go to Pre‑questions"):
                st.session_state.page = "preliminary"
                return
            st.stop()

        # --- compute net-change (ensure compute_net_change is defined at module scope) ---
        net_change_crime = compute_net_change(crime_categories, pre_crime_most, pre_crime_least, post_crime_most, post_crime_least)
        net_change_media = compute_net_change(crime_categories, pre_media_most, pre_media_least, post_media_most, post_media_least)
        net_change_boroughs = compute_net_change(boroughs, pre_lowest_boroughs, pre_highest_boroughs, post_lowest_boroughs, post_highest_boroughs)

        # Save numeric results into session_state so the row builder can pick them up
        st.session_state["net_change_crime"] = net_change_crime
        st.session_state["net_change_media"] = net_change_media
        st.session_state["net_change_boroughs"] = net_change_boroughs

        # --- Build final ordered row from session state (single canonical source) ---
        final_row_list = build_row_from_headers(headers)   # returns list ordered to match headers
        final_row = dict(zip(headers, final_row_list))     # header -> value mapping

        # --- Save the single main row to Google Sheets (one call only) ---
        try:
            save_rows_to_sheet([final_row], headers=headers)
            st.success("Responses saved to Google Sheets.")
        except Exception as e:
            st.error(f"Failed to save responses to Google Sheets: {e}")
            st.stop()

        # navigate to thank you
        st.session_state.page = "thank_you"
        return




def page_thank_you():
    st.set_page_config(page_title="Thank You", layout="wide")
    if st.session_state.get("_nav_rerun_once", False):
            # reset the one-time rerun guard when the target page loads
            st.session_state["_nav_rerun_once"] = False
    st.title("Thank you")

    st.markdown(
        "Thank you for your time. Your choices have been recorded."
    )

    st.success("Survey complete. You may close this tab or return to the app menu.")


# ---------------------------------------------------------
# PAGE ROUTER
# ---------------------------------------------------------

def router():
    # Ensure page key exists and is valid
    page = st.session_state.get("page", "consent")

    # mapping of page name -> handler function
    routes = {
        "consent": page_consent,
        "preliminary": page_preliminary,
        "d1_preview": d1_page_preview,
        "dashboard1": page_dashboard1,
        # "d2_preview": d2_page_preview,
        "dashboard2": page_dashboard2,
        "post_questions": page_post_questions,
        "thank_you": page_thank_you,
    }

    handler = routes.get(page)

    if handler is None:
        # Unknown page value: show a helpful message and reset to a safe page
        st.error(f"Unknown page '{page}'. Redirecting to the consent page.")
        st.session_state["page"] = "consent"
        routes["consent"]()
        return

    # Call the page handler inside try/except so a page error doesn't break the whole app
    try:
        handler()
    except Exception as e:
        # Surface a friendly error and reset to a safe page
        st.error(f"An unexpected error occurred while rendering page '{page}': {e}")
        st.session_state["page"] = "consent"
        routes["consent"]()





# ---------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------
# initialize session state once
init_state()
# then route to the current page
router()

