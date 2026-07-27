import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Submit & Export", layout="wide")

st.title("Submit & Export Responses")

st.markdown("Click **Save responses** to export all answers to a CSV file.")

if st.button("Save responses to CSV"):
    # Collect ALL keys that start with d1_ or d2_
    data = {
        key: st.session_state[key]
        for key in st.session_state
        if key.startswith(("d1_", "d2_"))
    }

    df = pd.DataFrame([data])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"survey_responses_{timestamp}.csv"

    df.to_csv(filename, index=False)

    st.success(f"Responses saved to {filename}")
    st.write(df)
