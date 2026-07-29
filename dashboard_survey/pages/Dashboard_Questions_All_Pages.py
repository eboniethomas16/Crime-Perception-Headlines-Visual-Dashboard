import streamlit as st
import pandas as pd
from pathlib import Path
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

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if "user_id" not in st.session_state:
        st.session_state.user_id = "user_" + str(st.session_state.get("seed", 1234))

    # Guard to avoid repeated experimental_rerun loops
    if "_nav_rerun_once" not in st.session_state:
        st.session_state["_nav_rerun_once"] = False



# ---------------------------------------------------------
# PAGE FUNCTIONS
# ---------------------------------------------------------

def page_consent():
    st.title("Consent for Research")

    PLACEHOLDER = "Select an option"

    # --- Consent question ---
    choice = st.selectbox(
        "I consent to my anonymised responses being used for this research.",
        [PLACEHOLDER, "Yes, I consent", "No, I do not consent"],
        key="pre_consent_select"
    )

    if st.button("Continue"):
        # --- YES: route to preliminary page ---
        # inside page_consent(), replace the rerun block with this
        if choice == "Yes, I consent":
            st.session_state["pre_consent"] = True
            st.success("Consent recorded.")
            st.session_state.page = "preliminary"
            return  

        elif choice == "No, I do not consent":
            st.session_state["pre_consent"] = False
            st.error("Survey closed for you.")
            st.session_state.page = "thank_you"
            return

        # --- Missing selection ---
        else:
            st.warning("Please select an option before continuing.")
            return
def page_preliminary():
    st.set_page_config(page_title="Pre‑Dashboard 2 Survey", layout="wide")

    st.title("Section 2 – Baseline Understanding")
    st.markdown("Before navigating Dashboard 2, please answer the following questions about crime in London, policing, and media headlines.")

    # --- Require consent before showing anything ---
    if not st.session_state.get("pre_consent", False):
        st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
        st.stop()

    PLACEHOLDER = "Select an option"

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

    # Validation helper
    def is_exactly_three(selection):
        return isinstance(selection, list) and len(selection) == 3

    valid_most = is_exactly_three(pre_crime_most)
    valid_least = is_exactly_three(pre_crime_least)
    valid_media_least = is_exactly_three(pre_media_least)
    valid_media_most = is_exactly_three(pre_media_most)

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

    # ---------------- CONTINUE BUTTON ----------------
    if st.button("Continue to Dashboard 1"):
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

        # All checks passed — navigate to Dashboard 1 (guarded rerun for single-click navigation)
        st.success("Pre‑survey complete. You will now be taken to view the Headlines vs. Crime Dashboard")
        st.session_state.page = "dashboard1"
        if not st.session_state.get("_nav_rerun_once", False):
            st.session_state["_nav_rerun_once"] = True
            st.experimental_rerun()
        return







def page_dashboard1():
    st.set_page_config(page_title="Dashboard 1 – Perception vs Crime", layout="wide")

    st.title("Dashboard 1 – Perception vs Crime")
    st.markdown("Please answer the questions below about Dashboard 1. All single-choice items start unselected.")

    PLACEHOLDER = "Select an option"

    # ---------------- BIVARIATE CHOROPLETH MAP ----------------
    st.header("Bivariate Choropleth Map")

    st.selectbox(
        "How accurate and trustworthy did the map's values and colour encoding appear?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d1_bivmap_content"
    )

    st.selectbox(
        "How clear was the map at communicating the two variables (crime count and perception) at a glance?",
        [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
        key="d1_bivmap_learnability"
    )

    st.selectbox(
        "How easy was it to find and interpret a specific borough on the map?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_bivmap_easeofuse"
    )

    st.selectbox(
        "How easy was it to operate the map controls (zoom, pan, legend, hover) without confusion?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_bivmap_operability"
    )

    st.selectbox(
        "How useful was the map for identifying boroughs where perception and crime diverge?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d1_bivmap_usefulness"
    )

    st.text_area("Open feedback — BIVARIATE CHOROPLETH MAP", key="d1_open_chord_feedback")


    # ---------------- HEATMAP ----------------
    st.header("Heatmap (Perception vs Crime)")

    st.selectbox(
        "How accurate and informative were the heatmap values and tooltips?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d1_heatmap_content"
    )

    st.selectbox(
        "How clear was the heatmap at showing where perception over/under estimates actual crime?",
        [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
        key="d1_heatmap_learnability"
    )

    st.selectbox(
        "How easy was it to interact with the heatmap (hover, select time, read tooltips)?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_heatmap_operability"
    )

    st.selectbox(
        "How easy was it to locate a specific borough and month in the heatmap?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_heatmap_easeofuse"
    )

    st.selectbox(
        "How useful was the heatmap for spotting borough/time combinations with large perception differences?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d1_heatmap_usefulness"
    )

    st.text_area("Open feedback — HEATMAP", key="d1_open_heatmap_feedback")


    # ---------------- HOVERLIST ----------------
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
        "How easy was it to control hover interactions and avoid accidental selections?",
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

    st.text_area("Open feedback — HOVER LIST", key="d1_open_hoverlist_feedback")


    # ---------------- LINE CHARTS ----------------
    st.header("Line Charts")

    st.selectbox(
        "How accurate and clear were the values and scales on the line charts?",
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
        "How easy was it to use the hoverline and zoom controls on the line charts?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_lines_operability"
    )

    st.selectbox(
        "How useful were the line charts for understanding trends and spikes over time?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d1_lines_usefulness"
    )

    st.text_area("Open feedback — LINE CHARTS", key="d1_open_linecharts_feedback")


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
        "How easy was it to spot the largest residual spikes for a selected crime?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_residuals_easeofuse"
    )


    # ---------------- SUMMARY PILLS ----------------
    st.header("Summary Pills")

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
        "How easy was it to select boroughs in the dropdown list at the top of the page?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d1_pills_operability"
    )

    st.selectbox(
        "How useful were the summary pills for forming an initial judgement about the selected crime category?",
        [PLACEHOLDER, "Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
        key="d1_pills_usefulness"
    )

    st.text_area("Open feedback — SUMMARY PILLS", key="d1_open_summary_pills_feedback")


    # ---------------- CONTINUE BUTTON + VALIDATION ----------------
    st.markdown("---")
    st.write("When you're done, click Continue to proceed to Dashboard 2.")

    if st.button("Continue to Dashboard 2"):
        # list all required d1_ keys (add or remove keys if you change questions)
        required_keys = [
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
            "d1_pills_operability", "d1_pills_usefulness"
        ]

        missing = [k for k in required_keys if st.session_state.get(k) in (None, PLACEHOLDER)]
        if missing:
            # Friendly, readable list of missing questions
            st.error("Please answer all required questions before continuing. The following items are unanswered:")
            for k in missing:
                # convert key to a nicer label for the user
                label = k.replace("d1_", "").replace("_", " ").capitalize()
                st.write(f"- {label}")
            st.info("Scroll up to complete the unanswered questions.")
        else:
            st.success("All Dashboard 1 questions complete. Redirecting to Dashboard 2...")
            # Navigate to Dashboard 2 page (adjust page name if your file is named differently)
            st.session_state.page = "dashboard2"
            return



def page_dashboard2():
    st.set_page_config(page_title="Dashboard 2 – Headlines vs Crime", layout="wide")
    st.title("Dashboard 2 – Headlines vs Crime")
    st.markdown("Please answer the questions below about Dashboard 2. All single-choice items start unselected.")

    PLACEHOLDER = "Select an option"

    # --- Require consent before showing anything ---
    if not st.session_state.get("pre_consent", False):
        st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
        if st.button("Go to Consent page"):
            st.experimental_set_query_params(page="Consent")
            return
        st.stop()

    # ---------------- CHORD CHART ----------------
    st.header("Chord Chart")
    st.text_area("Open feedback — CHORD CHART", key="d2_open_chord_feedback")

    # ---------------- HEATMAP ----------------
    st.header("Heatmap (Headlines vs Crime)")

    st.selectbox(
        "How accurate and informative were the heatmap values and tooltips?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d2_heatmap_content"
    )

    st.selectbox(
        "How clear was the heatmap at showing where HEADLINE over/under-reports actual crime?",
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
        "How useful was the heatmap for spotting crime category/time combinations with large crime differences?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d2_heatmap_usefulness"
    )

    st.text_area("Open feedback — HEATMAP", key="d2_open_heatmap_feedback")

    # ---------------- HOVER LIST ----------------
    st.header("Hoverlist (Headlines vs Crime)")

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
        "How easy was it to control hover interactions and avoid accidental selections?",
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

    st.text_area("Open feedback — HOVER LIST", key="d2_open_hoverlist_feedback")

    # ---------------- LINE CHARTS ----------------
    st.header("Line Charts")

    st.selectbox(
        "How accurate and clear were the values and scales on the line charts?",
        [PLACEHOLDER, "Very accurate", "Mostly accurate", "Neutral", "Somewhat inaccurate", "Very inaccurate"],
        key="d2_lines_content"
    )

    st.selectbox(
        "How easy was it to compare multiple series (crime, perception, headlines) on the line charts?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_lines_easeofuse"
    )

    st.selectbox(
        "How easy was it to read and compare the line charts (crime; perception; headlines; residuals) together?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_lines_learnability"
    )

    st.selectbox(
        "How easy was it to use the hoverline and zoom controls on the line charts?",
        [PLACEHOLDER, "Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
        key="d2_lines_operability"
    )

    st.selectbox(
        "How useful were the line charts for understanding trends and spikes over time?",
        [PLACEHOLDER, "Very useful", "Useful", "Neutral", "Not very useful", "Not useful at all"],
        key="d2_lines_usefulness"
    )

    st.text_area("Open feedback — LINE CHARTS", key="d2_open_linecharts_feedback")

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
        [PLACEHOLDER, "Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
        key="d2_pills_usefulness"
    )

    st.text_area("Open feedback — SUMMARY PILLS", key="d2_open_summary_pills_feedback")

    # ---------------- DASHBOARD LEVEL ----------------
    st.header("Dashboard-Level Questions")

    st.selectbox(
        "How well did Dashboard 2 improve your situational awareness about headlines vs crime?",
        [PLACEHOLDER, "Greatly improved", "Somewhat improved", "Neutral", "Slightly improved", "Not improved"],
        key="d2_situational_awareness"
    )

    st.selectbox(
        "How satisfied are you overall with Dashboard 2 for understanding headlines vs crime?",
        [PLACEHOLDER, "Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
        key="d2_overall_satisfaction"
    )

    st.text_area("Open feedback — CRIME VS. HEADLINES DASHBOARD", key="d2_open_summary_dashboard_feedback")

    st.selectbox(
        "Does the dashboard include the functions and features you expect for this analysis (filters; tooltips; zoom; borough selection; summary pills)?",
        [PLACEHOLDER, "All expected features present", "Most present", "Some present", "Few present", "None present"],
        key="d2_features_coverage"
    )

    st.selectbox(
        "How well integrated are the dashboard features into a single coherent tool?",
        [PLACEHOLDER, "Very well integrated", "Well integrated", "Neutral", "Poorly integrated", "Not integrated at all"],
        key="d2_integration"
    )

    st.selectbox(
        "How would you rate the dashboard's performance (speed when filtering; hovering; zooming)?",
        [PLACEHOLDER, "Very fast", "Fast", "Acceptable", "Slow", "Very slow"],
        key="d2_performance"
    )

    st.selectbox(
        "How well did Dashboard 2 support the task you came to do (compare headlines vs actual crime)?",
        [PLACEHOLDER, "Yes — completely", "Mostly", "Somewhat", "Not really", "Not at all"],
        key="d2_task_support"
    )

    st.selectbox(
        "How clear is the dashboard's user interface (labels; legends; control placement) overall?",
        [PLACEHOLDER, "Very clear", "Clear", "Neutral", "Unclear", "Very unclear"],
        key="d2_userinterface"
    )

    st.selectbox(
        "How would you rate the dashboard's overall visual design (colour choices; chart styles; layout)?",
        [PLACEHOLDER, "Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
        key="d2_visualdesign_satisfaction"
    )

    st.markdown("---")
    st.write("When you're done, click Finish to complete the survey and go to the Thank You page.")

    # ---------------- CONTINUE / FINISH BUTTON + VALIDATION ----------------
    if st.button("Finish and go to Thank You"):
        # Validate required d2_ keys
        required_d2 = [
            "d2_heatmap_content", "d2_heatmap_learnability", "d2_heatmap_operability",
            "d2_heatmap_easeofuse", "d2_heatmap_usefulness",
            "d2_hoverlist_content", "d2_hoverlist_learnability", "d2_hoverlist_operability",
            "d2_hoverlist_easeofuse", "d2_hoverlist_usefulness",
            "d2_lines_content", "d2_lines_easeofuse", "d2_lines_learnability",
            "d2_lines_operability", "d2_lines_usefulness",
            "d2_residuals_content", "d2_residuals_learnability", "d2_residuals_easeofuse",
            "d2_pills_learnability", "d2_pills_content", "d2_pills_easeofuse",
            "d2_pills_operability", "d2_pills_usefulness",
            "d2_situational_awareness", "d2_overall_satisfaction",
            "d2_features_coverage", "d2_integration", "d2_performance",
            "d2_task_support", "d2_userinterface", "d2_visualdesign_satisfaction"
        ]
        missing_d2 = [k for k in required_d2 if st.session_state.get(k) in (None, PLACEHOLDER)]
        if missing_d2:
            st.error("Please answer all required Dashboard 2 questions before finishing. The following items are unanswered:")
            for k in missing_d2:
                label = k.replace("d2_", "").replace("_", " ").capitalize()
                st.write(f"- {label}")
            st.info("Scroll up to complete the unanswered questions.")
        else:
            st.success("All Dashboard 2 questions complete. Redirecting to Post Survey Questions...")
            st.session_state.page = "post_questions"
            return


def page_post_questions():
    st.set_page_config(page_title="Post‑Dashboard 2 Survey", layout="wide")
    st.title("Section 3 – Post Dashboard Survey - Change in Understanding")
    st.markdown("After viewing the dashboards, please answer the following questions about policing, headlines, and your perceptions. These mirror the baseline questions so we can measure any change in understanding.")

    # --- Require consent before showing anything ---
    if not st.session_state.get("pre_consent", False):
        st.warning("You must give consent before continuing. Please go to the Consent page and select 'Yes, I consent'.")
        if st.button("Go to Consent page"):
            st.experimental_set_query_params(page="Consent")
            return
        st.stop()

    PLACEHOLDER = "Select an option"

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
    # ---------------- FINISH BUTTON + VALIDATION ----------------
    st.markdown("---")
    st.write("When you're done, click Finish to complete the survey.")


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

    if len(post_lowest_boroughs) != 3:
        st.warning("Please select exactly 3 boroughs for the LOWEST crime question (post).")
    if len(post_highest_boroughs) != 3:
        st.warning("Please select exactly 3 boroughs for the HIGHEST crime question (post).")

    # ---------------- FINISH / SUBMIT VALIDATION (unified) ----------------
    st.markdown("---")
    st.write("When you're done, click Finish to complete the survey and go to the Thank You page.")

    # Helper validators
    def is_missing(val, placeholder=PLACEHOLDER):
        return val in (None, placeholder, [], "")

    def is_exactly_three(selection):
        return isinstance(selection, list) and len(selection) == 3

    # Keys required for post questions (all keys used above)
    required_post_selects = [
        "post_police_reliability", "post_police_fairness", "post_police_job",
        "post_news_frequency", "post_headline_accuracy",
        "post_headline_inflation", "post_headline_truth", "post_crime_increase",
        "post_crime_most", "post_crime_least", "post_media_least", "post_media_most",
        "post_lowest_boroughs", "post_highest_boroughs"
    ]

    # Keys required from the pre (only enforced here, same names used in page_preliminary)
    required_pre_keys = [
        "pre_police_reliability", "pre_police_fairness", "pre_police_job",
        "pre_news_frequency", "pre_headline_accuracy",
        "pre_headline_inflation", "pre_headline_truth", "pre_crime_increase",
        "pre_crime_most", "pre_crime_least", "pre_media_least", "pre_media_most",
        "pre_lowest_boroughs", "pre_highest_boroughs"
    ]

    if st.button("Finish and go to Thank You"):
        # Check post required fields
        missing_post = [k for k in required_post_selects if is_missing(st.session_state.get(k))]
        if missing_post:
            st.error("Please answer all required post‑dashboard questions before finishing.")
            st.info("Missing items:")
            for k in missing_post:
                label = k.replace("post_", "").replace("_", " ").capitalize()
                st.write(f"- {label}: {repr(st.session_state.get(k))}")
            st.stop()

        # Validate exact-3 multiselects (post)
        if not (is_exactly_three(st.session_state.get("post_crime_most")) and
                is_exactly_three(st.session_state.get("post_crime_least")) and
                is_exactly_three(st.session_state.get("post_media_least")) and
                is_exactly_three(st.session_state.get("post_media_most"))):
            st.error("Please ensure all 'select three' post questions have exactly three selections.")
            st.stop()

        # Validate borough multiselects (post)
        if not (len(st.session_state.get("post_lowest_boroughs", [])) == 3 and
                len(st.session_state.get("post_highest_boroughs", [])) == 3):
            st.error("Please select exactly 3 boroughs for both the LOWEST and HIGHEST crime questions (post).")
            st.stop()

        # Ensure pre-questions exist (so we can compute gain)
        missing_pre = [k for k in required_pre_keys if k not in st.session_state or is_missing(st.session_state.get(k))]
        if missing_pre:
            st.error("Preliminary responses are missing. Please complete the pre‑survey questions first.")
            st.info("Missing preliminary items:")
            for k in missing_pre:
                label = k.replace("pre_", "").replace("_", " ").capitalize()
                st.write(f"- {label}: {repr(st.session_state.get(k))}")
            if st.button("Go to Pre‑questions"):
                st.session_state.page = "preliminary"
                st.experimental_rerun()
            st.stop()

        # All checks passed — compute summary and navigate
        st.success("Post‑survey complete. Calculating summary of changes...")
        # (existing gain summary code can remain here; you already have it below)
        # After computing and showing the summary, navigate to Thank You
        st.info("You will now be taken to the Thank You page.")
        st.session_state.page = "thank_you"
        st.experimental_rerun()






def page_thank_you():
    st.set_page_config(page_title="Thank You", layout="wide")
    st.title("Thank you")

    st.markdown(
        "Thank you for your time. Your choices have been recorded."
    )

    st.success("Survey complete. You may close this tab or return to the app menu.")


# ---------------------------------------------------------
# PAGE ROUTER
# ---------------------------------------------------------

def router():
    if st.session_state.page == "consent":
        page_consent()
    elif st.session_state.page == "preliminary":
        page_preliminary()
    elif st.session_state.page == "dashboard1":
        page_dashboard1()
    elif st.session_state.page == "dashboard2":
        page_dashboard2()
    elif st.session_state.page == "post_questions":
        page_post_questions()
    elif st.session_state.page == "thank_you":
        page_thank_you()
# def router():
#     """Route to the correct page based on session_state.page."""
#     page = st.session_state.page

#     if page == "consent":
#         page_consent()
#     elif page == "preliminary":
#         page_preliminary()
#     elif page == "dashboard1":
#         page_dashboard1()
#     elif page == "dashboard2":
#         page_dashboard2()
#     elif page == "post_questions":
#         page_post_questions()
#     elif page == "thank_you":
#         page_thank_you()
#     else:
#         st.error(f"Unknown page: {page}")


# ---------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------

init_state()
router()
