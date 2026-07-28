# # pages/5_Submit_and_Export.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Submit & Export", layout="wide")
st.title("Submit & Export Responses")
st.markdown(
    "Click **Submit** to send your responses to the configured Google Sheet. "
    "If Google Sheets is not configured, you can download a CSV copy instead."
)

# Collect all survey keys (pre_, d1_, d2_, post_)
def collect_responses():
    prefixes = ("pre_", "d1_", "d2_", "post_")
    data = {k: st.session_state.get(k, "") for k in st.session_state if k.startswith(prefixes)}
    # Add respondent metadata
    data["_submitted_at"] = datetime.utcnow().isoformat()
    # If you want a respondent id, generate one here
    if "_respondent_id" not in st.session_state:
        st.session_state["_respondent_id"] = f"resp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    data["_respondent_id"] = st.session_state["_respondent_id"]
    return data

def to_dataframe(data):
    # Ensure deterministic column order
    cols = sorted(data.keys())
    df = pd.DataFrame([data], columns=cols)
    return df

# Attempt to append to Google Sheets using service account credentials
def append_to_google_sheet(df):
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except Exception as e:
        return False, f"Missing libraries for Google Sheets: {e}"

    # Prefer secrets or environment variables
    sheet_id = st.secrets.get("GOOGLE_SHEET_ID") if "GOOGLE_SHEET_ID" in st.secrets else os.environ.get("GOOGLE_SHEET_ID")
    sa_info = None

    # Option 1: service account JSON stored in Streamlit secrets as a JSON string under key SERVICE_ACCOUNT
    if "SERVICE_ACCOUNT" in st.secrets:
        sa_info = st.secrets["SERVICE_ACCOUNT"]
    # Option 2: path to service account file in env var
    elif os.environ.get("SERVICE_ACCOUNT_FILE"):
        sa_path = os.environ.get("SERVICE_ACCOUNT_FILE")
        if os.path.exists(sa_path):
            creds = Credentials.from_service_account_file(sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
            gc = gspread.authorize(creds)
            try:
                sh = gc.open_by_key(sheet_id)
                worksheet = sh.sheet1
                worksheet.append_row(df.iloc[0].tolist(), value_input_option="USER_ENTERED")
                return True, "Appended to Google Sheet"
            except Exception as e:
                return False, f"Google Sheets append failed: {e}"
        else:
            return False, "Service account file path set but file not found."

    if not sa_info:
        return False, "No service account credentials found in Streamlit secrets or environment."

    try:
        # sa_info may be a dict-like object in st.secrets or a JSON string
        if isinstance(sa_info, str):
            import json
            sa_json = json.loads(sa_info)
        else:
            sa_json = sa_info

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(sa_json, scopes=scopes)
        gc = gspread.authorize(creds)
        if not sheet_id:
            return False, "GOOGLE_SHEET_ID not configured in secrets or environment."
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.sheet1
        worksheet.append_row(df.iloc[0].tolist(), value_input_option="USER_ENTERED")
        return True, "Appended to Google Sheet"
    except Exception as e:
        return False, f"Google Sheets append failed: {e}"

# Main submit flow
if st.button("Submit"):
    data = collect_responses()
    df = to_dataframe(data)

    st.info("Preparing submission...")

    success, message = append_to_google_sheet(df)
    if success:
        st.success("Responses submitted to Google Sheet.")
        st.write(df)
        # After successful submit, navigate to Thank You page
        st.experimental_set_query_params(page="3_Thank_You")
        st.experimental_rerun()
    else:
        st.warning(f"Google Sheets submission unavailable: {message}")
        st.markdown("You can still download a CSV copy of your responses below. When you're ready, re-run this page after configuring Google Sheets credentials to submit automatically.")

        # Provide download button for CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"survey_responses_{timestamp}.csv"

        st.download_button(
            label="Download responses as CSV",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv"
        )

        # Also offer to save to server if running locally
        try:
            local_path = os.path.join(os.getcwd(), filename)
            df.to_csv(local_path, index=False)
            st.info(f"A local copy was saved to: {local_path}")
        except Exception:
            # ignore write errors on hosted environments
            pass

# Show current respondent id and timestamp for debugging/traceability
if "_respondent_id" in st.session_state:
    st.write("Respondent ID:", st.session_state["_respondent_id"])
