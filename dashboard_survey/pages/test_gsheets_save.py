import math
import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def _build_gspread_client_from_secrets():
    creds_info = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON") or st.secrets.get("gcp_service_account")
    if creds_info is None:
        raise RuntimeError("No GCP credentials found in st.secrets (GCP_SERVICE_ACCOUNT_JSON or gcp_service_account).")

    creds_dict = json.loads(creds_info) if isinstance(creds_info, str) else dict(creds_info)

    # Normalize private_key newlines if escaped
    if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip()

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
    client = gspread.authorize(creds)
    return client, creds_dict.get("client_email")

def save_to_google_sheets(results_data, sheet_title_or_id=None, worksheet_name="responses"):
    """
    Append rows (list of lists) to Google Sheets.
    - results_data: iterable of rows (each row is a list)
    - sheet_title_or_id: optional override (if None, uses st.secrets['SPREADSHEET_ID'])
    - worksheet_name: worksheet/tab name
    """
    try:
        client, client_email = _build_gspread_client_from_secrets()
    except Exception as e:
        st.error(f"GSpread auth error: {e}")
        return

    # Prefer explicit argument, otherwise top-level secret
    spreadsheet_id = sheet_title_or_id or st.secrets.get("SPREADSHEET_ID")
    if not spreadsheet_id:
        st.error("SPREADSHEET_ID missing from st.secrets; add it as a top-level key in secrets.toml")
        return

    try:
        # open by key (recommended) — if you want to open by title use client.open("Title")
        sh = client.open_by_key(spreadsheet_id)
    except Exception as e:
        st.error(f"Failed to open spreadsheet: {e}")
        return

    # get or create worksheet
    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_name, rows="1000", cols="50")

    # If sheet empty, optionally write a simple header (customise as needed)
    try:
        existing = ws.get_all_records()
    except Exception:
        existing = []

    if len(existing) == 0:
        headers = ["user_id", "submission_timestamp_utc", "note"]
        ws.append_row(headers, value_input_option="USER_ENTERED")

    # Append cleaned rows
    for row in results_data:
        cleaned = []
        for v in row:
            if v is None:
                cleaned.append("")
            elif isinstance(v, float) and math.isnan(v):
                cleaned.append("")
            elif isinstance(v, list):
                cleaned.append(";".join(map(str, v)))
            else:
                cleaned.append(v)
        ws.append_row(cleaned, value_input_option="USER_ENTERED")

    st.success("Rows appended to Google Sheet (check the sheet).")
