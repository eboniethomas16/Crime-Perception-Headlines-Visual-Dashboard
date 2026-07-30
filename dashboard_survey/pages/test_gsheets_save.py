
import streamlit as st
import json
import traceback
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="GSheets Test", layout="centered")
st.title("Google Sheets Connection Test")

# Show which secrets are present (no private key printed)
has_nested = "gcp_service_account" in st.secrets
has_json = "GCP_SERVICE_ACCOUNT_JSON" in st.secrets
st.write("DEBUG: found nested gcp_service_account:", has_nested)
st.write("DEBUG: found GCP_SERVICE_ACCOUNT_JSON:", has_json)
st.write("DEBUG: SPREADSHEET_ID present:", bool(st.secrets.get("SPREADSHEET_ID")))
st.write("DEBUG: SHEET_NAME present:", bool(st.secrets.get("SHEET_NAME")))

def build_gspread_client():
    """
    Build gspread client from Streamlit secrets.
    Accepts either st.secrets["gcp_service_account"] (nested table) or
    st.secrets["GCP_SERVICE_ACCOUNT_JSON"] (JSON string).
    """
    creds_info = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON") or st.secrets.get("gcp_service_account")
    if creds_info is None:
        raise RuntimeError("No GCP credentials found in st.secrets (GCP_SERVICE_ACCOUNT_JSON or gcp_service_account).")

    # Parse into dict
    if isinstance(creds_info, str):
        creds_dict = json.loads(creds_info)
    else:
        creds_dict = dict(creds_info)

    # Normalize private_key newlines if escaped
    if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip()

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
    client = gspread.authorize(creds)
    return client, creds_dict.get("client_email")

def ensure_worksheet(sh, sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows="1000", cols="50")
    return ws

st.markdown("---")
st.write("Click the button below to attempt opening the spreadsheet and appending a single test row.")
if st.button("Run GSheets test"):
    try:
        client, client_email = build_gspread_client()
        st.success("DEBUG: gspread client created")
        st.write("DEBUG: service account email:", client_email)

        spreadsheet_id = st.secrets.get("SPREADSHEET_ID")
        if not spreadsheet_id:
            st.error("SPREADSHEET_ID missing from st.secrets")
            st.stop()

        sh = client.open_by_key(spreadsheet_id)
        st.write("DEBUG: opened spreadsheet:", sh.title)

        sheet_name = st.secrets.get("SHEET_NAME", "responses")
        ws = ensure_worksheet(sh, sheet_name)
        st.write("DEBUG: using worksheet:", ws.title)

        # Ensure a simple header if sheet empty
        values = ws.get_all_values()
        if not values:
            headers = ["test_timestamp", "client_email", "note"]
            ws.append_row(headers, value_input_option="USER_ENTERED")
            st.write("DEBUG: wrote header row")

        # Append a test row
        test_row = [datetime.utcnow().isoformat() + "Z", client_email or "unknown", "streamlit test append"]
        ws.append_row(test_row, value_input_option="USER_ENTERED")
        st.success("Append succeeded — check the sheet now.")
        st.write("Appended row:", test_row)

    except Exception as e:
        st.error("DEBUG gspread error: " + str(e))
        st.text("Full traceback (for debugging):")
        st.text(traceback.format_exc())
        st.stop()
