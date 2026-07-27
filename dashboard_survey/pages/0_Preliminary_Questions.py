# pages/2_Pre_Dashboard_2_Questions.py
import streamlit as st

st.set_page_config(page_title="Pre‑Dashboard 2 Survey", layout="wide")
st.title("Section 2 – Baseline Understanding")
st.markdown("Before navigating Dashboard 2, please answer the following questions about crime in London, policing, and media headlines.")

# --- Require consent before showing anything ---
if not st.session_state.get("pre_consent", False):
    st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
    st.stop()

# Helper: placeholder option for selectboxes
PLACEHOLDER = "Select an option"

# ---------------- ABOUT YOU ----------------

st.header("About You")

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
    "City of London", "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley",
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

policing_scale = [PLACEHOLDER, "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

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

likert = [PLACEHOLDER, "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

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

crime_categories = [
    "Fraud and Forgery", "Possession of Weapons", "Drug Offences", "Gun Crime",
    "Knife Crime", "Lethal Barrel Discharge", "Sexual Offences", "Robbery",
    "Violence Against the Person", "Hate Crime", "Arson and Criminal Damage",
    "Burglary", "Public Order Offences", "Domestic Abuse", "Theft",
    "Vehicle Offences"
]

st.markdown("**Select exactly three options for each question.** If you select more or fewer than three, you will see a warning and cannot continue.")

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

# Validate multiselect counts
def validate_three(name, selection):
    if selection is None:
        return False
    return len(selection) == 3

valid_most = validate_three("most", pre_crime_most)
valid_least = validate_three("least", pre_crime_least)
valid_media_least = validate_three("media_least", pre_media_least)
valid_media_most = validate_three("media_most", pre_media_most)

if not valid_most:
    st.warning("Please select exactly 3 categories for 'MOST offences in your Borough'.")
if not valid_least:
    st.warning("Please select exactly 3 categories for 'LEAST offences in your Borough'.")
if not valid_media_least:
    st.warning("Please select exactly 3 categories for 'THE LEAST covered in headlines'.")
if not valid_media_most:
    st.warning("Please select exactly 3 categories for 'MOST PROMINENTLY covered in headlines'.")

# ---------------- BOROUGH CRIME PERCEPTION ----------------

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

if len(pre_lowest_boroughs) != 3:
    st.warning("Please select exactly 3 boroughs for the LOWEST crime question.")
if len(pre_highest_boroughs) != 3:
    st.warning("Please select exactly 3 boroughs for the HIGHEST crime question.")

# Final continue button with validation
if st.button("Continue to Dashboard 2"):
    # Validate required selectboxes are not left on placeholder
    required_selects = [
        "pre_age_band", "pre_education", "pre_borough",
        "pre_police_reliability", "pre_police_fairness", "pre_police_job",
        "pre_news_frequency", "pre_headline_accuracy",
        "pre_headline_inflation", "pre_headline_truth", "pre_crime_increase"
    ]
    missing = [k for k in required_selects if st.session_state.get(k) in (None, PLACEHOLDER)]
    if missing:
        st.error("Please answer all required questions before continuing.")
    elif not (valid_most and valid_least and valid_media_least and valid_media_most and len(pre_lowest_boroughs) == 3 and len(pre_highest_boroughs) == 3):
        st.error("Please ensure all 'select three' questions have exactly three selections.")
    else:
        st.success("Pre‑survey complete. You may now proceed to Dashboard 2.")
