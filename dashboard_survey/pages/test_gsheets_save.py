#!/usr/bin/env python3
"""
Simple test to verify Google Sheets append using a service account.

Usage:
  python test_gsheets_save.py --creds /path/to/service_account.json --sheet_id <SPREADSHEET_ID> --worksheet responses

Notes:
  - SPREADSHEET_ID must be the long id from the sheet URL (not the human title).
  - Share the spreadsheet with the service account's client_email (Editor).
"""
import argparse
import json
import os
import sys
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def build_client_from_file(creds_path):
    with open(creds_path, "r", encoding="utf-8") as f:
        creds_dict = json.load(f)
    # fix escaped newlines if present
    if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    return gspread.authorize(creds), creds_dict.get("client_email")

def build_client_from_env(env_var):
    raw = os.environ.get(env_var)
    if not raw:
        raise RuntimeError(f"Environment variable {env_var} not set")
    creds_dict = json.loads(raw)
    if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    return gspread.authorize(creds), creds_dict.get("client_email")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--creds", help="Path to service account JSON file (optional if using env)", default=None)
    p.add_argument("--env", help="Environment variable name containing JSON string (optional)", default="GCP_SERVICE_ACCOUNT_JSON")
    p.add_argument("--sheet_id", required=True, help="Spreadsheet ID (from URL)")
    p.add_argument("--worksheet", default="responses", help="Worksheet/tab name (will be created if missing)")
    args = p.parse_args()

    try:
        if args.creds:
            client, sa_email = build_client_from_file(args.creds)
            print("Loaded credentials from file:", args.creds)
        else:
            client, sa_email = build_client_from_env(args.env)
            print("Loaded credentials from environment variable:", args.env)
        print("Service account email:", sa_email)
    except Exception as e:
        print("Failed to build gspread client from credentials:", e, file=sys.stderr)
        sys.exit(2)

    try:
        print("Opening spreadsheet by key:", args.sheet_id)
        sh = client.open_by_key(args.sheet_id)
        print("Opened spreadsheet title:", sh.title)
    except Exception as e:
        print("Failed to open spreadsheet. Check SPREADSHEET_ID and that the service account has access.", file=sys.stderr)
        print("Error:", e, file=sys.stderr)
        sys.exit(3)

    try:
        try:
            ws = sh.worksheet(args.worksheet)
            print("Opened existing worksheet:", ws.title)
        except gspread.WorksheetNotFound:
            print("Worksheet not found; creating worksheet:", args.worksheet)
            ws = sh.add_worksheet(title=args.worksheet, rows="1000", cols="50")
            print("Created worksheet:", ws.title)

        # Ensure header row exists (simple check)
        values = ws.get_all_values()
        if not values:
            headers = ["test_timestamp", "test_user", "note"]
            print("Writing header row:", headers)
            ws.append_row(headers, value_input_option="USER_ENTERED")
            time.sleep(0.5)

        # Append a test row
        test_row = [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "test_user", "append test from script"]
        print("Appending test row:", test_row)
        ws.append_row(test_row, value_input_option="USER_ENTERED")
        print("Append succeeded. Check the sheet now.")
    except Exception as e:
        print("Failed while accessing or writing to worksheet:", e, file=sys.stderr)
        sys.exit(4)

if __name__ == "__main__":
    main()
