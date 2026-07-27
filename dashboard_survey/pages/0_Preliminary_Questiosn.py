import streamlit as st

st.set_page_config(page_title="Pre‑Dashboard 2 Survey", layout="wide")

st.title("Section 2 – Baseline Understanding")
st.markdown("Before navigating Dashboard 2, please answer the following questions about crime in London, policing, and media headlines.")


# ---------------- CONSENT ----------------

st.header("Consent")

st.radio(
    "I consent to my anonymised responses being used for this research.",
    ["Yes, I consent", "No, I do not consent"],
    key="pre_consent"
)


# ---------------- AGE ----------------

st.header("About You")

st.radio(
    "What is your age band?",
    ["18–24", "25–34", "35–44", "45–54", "55–64", "65+", "Prefer not to say"],
    key="pre_age_band"
)


# ---------------- EDUCATION ----------------

st.selectbox(
    "What is your highest level of education (current or completed)?",
    [
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


# ---------------- BOROUGH ----------------

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
    boroughs,
    key="pre_borough"
)


# ---------------- POLICING QUESTIONS ----------------

st.header("Your Views on Policing in Your Borough")

policing_scale = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

st.radio(
    "The police can be relied upon to be there when needed in your area.",
    policing_scale,
    key="pre_police_reliability"
)

st.radio(
    "The police treat everyone fairly regardless of who they are in your area.",
    policing_scale,
    key="pre_police_fairness"
)

st.radio(
    "The police do a good job in your area.",
    policing_scale,
    key="pre_police_job"
)


# ---------------- NEWS CONSUMPTION ----------------

st.header("Your Exposure to Crime Headlines")

st.radio(
    "How often do you read online news about crime in London?",
    ["Daily", "Several times a week", "Weekly", "Monthly", "Yearly", "Never"],
    key="pre_news_frequency"
)

st.radio(
    "How accurate do you think online headlines about crime in London are overall?",
    [
        "Very inaccurate",
        "Somewhat inaccurate",
        "Neither accurate nor inaccurate",
        "Somewhat accurate",
        "Very accurate",
        "Don’t know"
    ],
    key="pre_headline_accuracy"
)


# ---------------- PERCEPTION OF HEADLINES ----------------

st.header("Your Perception of Crime Headlines")

likert = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

st.radio(
    "Online news headlines make me believe crime in my borough is higher than actual crime counts.",
    likert,
    key="pre_headline_inflation"
)

st.radio(
    "Headlines about crime in London are generally accurate to actual crime counts in my Borough.",
    likert,
    key="pre_headline_truth"
)

st.radio(
    "In the past 12 months, crime in my Borough has increased.",
    likert,
    key="pre_crime_increase"
)


# ---------------- CRIME CATEGORY QUESTIONS ----------------

crime_categories = [
    "Fraud and Forgery", "Possession of Weapons", "Drug Offences", "Gun Crime",
    "Knife Crime", "Lethal Barrel Discharge", "Sexual Offences", "Robbery",
    "Violence Against the Person", "Hate Crime", "Arson and Criminal Damage",
    "Burglary", "Public Order Offences", "Domestic Abuse", "Theft",
    "Vehicle Offences"
]

st.header("Crime Categories – Your Perception")

# Q5 – MOST offences in your Borough
st.multiselect(
    "Select **three** crime categories you believe have the **MOST offences** in your Borough.",
    crime_categories,
    key="pre_crime_most"
)

# Q6 – LEAST offences in your Borough
st.multiselect(
    "Select **three** crime categories you believe have the **LEAST offences** in your Borough.",
    crime_categories,
    key="pre_crime_least"
)

# Q7 – LEAST covered in headlines
st.multiselect(
    "Select **three** crime categories you believe the media covers **THE LEAST** in London headlines.",
    crime_categories,
    key="pre_media_least"
)

# Q8 – MOST covered in headlines
st.multiselect(
    "Select **three** crime categories you believe the media covers **MOST PROMINENTLY** in London headlines.",
    crime_categories,
    key="pre_media_most"
)


# ---------------- BOROUGH CRIME PERCEPTION ----------------

st.header("Your Perception of Borough Crime Levels")

st.multiselect(
    "Select **three** boroughs you believe have the **LOWEST** crime offences in London.",
    boroughs[:-1],  # remove "I don't live in London"
    key="pre_lowest_boroughs"
)

st.multiselect(
    "Select **three** boroughs you believe have the **HIGHEST** crime offences in London.",
    boroughs[:-1],
    key="pre_highest_boroughs"
)


st.success("Pre‑Dashboard‑2 survey complete. Continue to Dashboard 2 when ready.")
