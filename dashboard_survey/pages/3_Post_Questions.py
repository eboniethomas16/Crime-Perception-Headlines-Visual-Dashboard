# pages/4_Post_Dashboard_2_Questions.py
import streamlit as st

st.set_page_config(page_title="Post‑Dashboard 2 Survey", layout="wide")
st.title("Section 3 – Post Dashboard Survey - Change in Understanding")
st.markdown("After viewing the dashboards, please answer the following questions about policing, headlines, and your perceptions. These mirror the baseline questions so we can measure any change in understanding.")

# --- Require consent before showing anything ---
if not st.session_state.get("pre_consent", False):
    st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
    if st.button("Go to Consent page"):
        st.experimental_set_query_params(page="Consent")
        st.experimental_rerun()
    st.stop()

PLACEHOLDER = "Select an option"

# ---------------- POLICING QUESTIONS (post) ----------------
st.header("Your Views on Policing in Your Borough (after viewing dashboards)")

policing_scale = [PLACEHOLDER, "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

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

likert = [PLACEHOLDER, "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

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

crime_categories = [
    "Fraud and Forgery", "Possession of Weapons", "Drug Offences", "Gun Crime",
    "Knife Crime", "Lethal Barrel Discharge", "Sexual Offences", "Robbery",
    "Violence Against the Person", "Hate Crime", "Arson and Criminal Damage",
    "Burglary", "Public Order Offences", "Domestic Abuse", "Theft",
    "Vehicle Offences"
]

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

# Validate multiselect counts (post)
def is_exactly_three(selection):
    return isinstance(selection, list) and len(selection) == 3

valid_post_most = is_exactly_three(post_crime_most)
valid_post_least = is_exactly_three(post_crime_least)
valid_post_media_least = is_exactly_three(post_media_least)
valid_post_media_most = is_exactly_three(post_media_most)

if not valid_post_most:
    st.warning("Please select exactly 3 categories for 'MOST offences in your Borough' (post).")
if not valid_post_least:
    st.warning("Please select exactly 3 categories for 'LEAST offences in your Borough' (post).")
if not valid_post_media_least:
    st.warning("Please select exactly 3 categories for 'THE LEAST covered in headlines' (post).")
if not valid_post_media_most:
    st.warning("Please select exactly 3 categories for 'MOST PROMINENTLY covered in headlines' (post).")

# ---------------- BOROUGH CRIME PERCEPTION (post) ----------------
st.header("Your Perception of Borough Crime Levels (after viewing dashboards)")

boroughs = [
    "City of London", "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley",
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

if len(post_lowest_boroughs) != 3:
    st.warning("Please select exactly 3 boroughs for the LOWEST crime question (post).")
if len(post_highest_boroughs) != 3:
    st.warning("Please select exactly 3 boroughs for the HIGHEST crime question (post).")

# ---------------- FINISH BUTTON + VALIDATION + GAIN SUMMARY ----------------
st.markdown("---")
st.write("When you're done, click Finish to complete the survey and go to the Thank You page.")

if st.button("Finish and go to Thank You"):
    # Validate required post selectboxes are not left on placeholder
    required_post_selects = [
        "post_police_reliability", "post_police_fairness", "post_police_job",
        "post_news_frequency", "post_headline_accuracy",
        "post_headline_inflation", "post_headline_truth", "post_crime_increase"
    ]
    missing_post = [k for k in required_post_selects if st.session_state.get(k) in (None, PLACEHOLDER)]
    if missing_post:
        st.error("Please answer all required post‑survey questions before finishing.")
        st.info("Missing items:")
        for k in missing_post:
            label = k.replace("post_", "").replace("_", " ").capitalize()
            st.write(f"- {label}")
        st.stop()

    # Validate exact-3 multiselects
    post_multiselect_valid = all([
        valid_post_most, valid_post_least, valid_post_media_least, valid_post_media_most,
        len(post_lowest_boroughs) == 3, len(post_highest_boroughs) == 3
    ])
    if not post_multiselect_valid:
        st.error("Please ensure all 'select three' questions have exactly three selections (post).")
        st.stop()

    # Ensure pre-questions exist (so we can compute gain)
    pre_keys = [
        "pre_police_reliability", "pre_police_fairness", "pre_police_job",
        "pre_news_frequency", "pre_headline_accuracy",
        "pre_headline_inflation", "pre_headline_truth", "pre_crime_increase",
        "pre_crime_most", "pre_crime_least", "pre_media_least", "pre_media_most",
        "pre_lowest_boroughs", "pre_highest_boroughs"
    ]
    missing_pre = [k for k in pre_keys if k not in st.session_state or st.session_state.get(k) in (None, [], False)]
    if missing_pre:
        st.error("Preliminary responses are missing. Please complete the pre‑survey questions first.")
        if st.button("Go to Pre‑questions"):
            st.experimental_set_query_params(page="2_Pre_Dashboard_2_Questions")
            st.experimental_rerun()
        st.stop()

    # Compute a simple gain summary: count how many key perception items changed
    change_count = 0
    compare_keys = [
        ("pre_police_reliability", "post_police_reliability"),
        ("pre_police_fairness", "post_police_fairness"),
        ("pre_police_job", "post_police_job"),
        ("pre_headline_inflation", "post_headline_inflation"),
        ("pre_headline_truth", "post_headline_truth"),
        ("pre_crime_increase", "post_crime_increase"),
        ("pre_headline_accuracy", "post_headline_accuracy")
    ]
    changed_items = []
    for pre_k, post_k in compare_keys:
        pre_val = st.session_state.get(pre_k)
        post_val = st.session_state.get(post_k)
        if pre_val != post_val:
            change_count += 1
            changed_items.append((pre_k.replace("pre_", "").replace("_", " ").capitalize(), pre_val, post_val))

    st.success("Post‑survey complete. Calculating summary of changes...")
    st.markdown("### Quick change summary")
    st.write(f"**Number of key perception items changed:** {change_count} of {len(compare_keys)}")

    if changed_items:
        st.markdown("**Changed items (pre → post):**")
        for label, pre_val, post_val in changed_items:
            st.write(f"- **{label}**: {pre_val} → {post_val}")
    else:
        st.write("No changes detected in the key perception items.")

    # Show differences in top-3 selections (media and boroughs)
    def list_diff(pre_list, post_list):
        pre_set = set(pre_list)
        post_set = set(post_list)
        added = list(post_set - pre_set)
        removed = list(pre_set - post_set)
        return added, removed

    st.markdown("### Changes in top-3 selections")
    added, removed = list_diff(st.session_state["pre_media_most"], st.session_state["post_media_most"])
    st.write("Media most prominent (added):", added or "None")
    st.write("Media most prominent (removed):", removed or "None")

    added, removed = list_diff(st.session_state["pre_media_least"], st.session_state["post_media_least"])
    st.write("Media least prominent (added):", added or "None")
    st.write("Media least prominent (removed):", removed or "None")

    added, removed = list_diff(st.session_state["pre_lowest_boroughs"], st.session_state["post_lowest_boroughs"])
    st.write("Lowest boroughs (added):", added or "None")
    st.write("Lowest boroughs (removed):", removed or "None")

    added, removed = list_diff(st.session_state["pre_highest_boroughs"], st.session_state["post_highest_boroughs"])
    st.write("Highest boroughs (added):", added or "None")
    st.write("Highest boroughs (removed):", removed or "None")

    # Navigate to Thank You page
    st.info("You will now be taken to the Thank You page.")
    st.experimental_set_query_params(page="4_Thank_You")
    st.experimental_rerun()
