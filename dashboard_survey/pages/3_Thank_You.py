import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Submit & Export", layout="wide")

st.title("Submit & Export Responses")

st.markdown("Click **Save responses** to export your current answers to CSV.")

if st.button("Save responses to CSV"):
    data = {k: v for k, v in st.session_state.items() if k.startswith("d1_")}
    df = pd.DataFrame([data])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"d1_responses_{timestamp}.csv"
    df.to_csv(filename, index=False)
    st.success(f"Saved responses to {filename}")
