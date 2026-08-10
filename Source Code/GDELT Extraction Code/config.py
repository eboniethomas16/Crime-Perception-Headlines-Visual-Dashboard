import pandas as pd
# GDELT 2.0 base URL
GDELT_BASE = "http://data.gdeltproject.org/gdeltv2/"


# Where to store downloaded files
OUTPUT_DIR = "data/combined_datasets/" #stores the final combined .csv dataset
CACHE_FILTERED = "data/cache/filtered" #stores the filtered parquet datasets
CACHE_PARSED_DIR = "data/cache/parsed" #stores the parsed datasets


# Themes relevant to crime/policing
CRIME_THEMES = ["CRIME", "VIOLENCE", "POLICE", "LAW_ENFORCEMENT", "SECURITY",
    "ASSAULT", "MURDER", "HOMICIDE", "SHOOTING", "STABBING",
    "KIDNAPPING", "ROBBERY", "BURGLARY", "ARSON",
    "ARREST", "RAID", "INVESTIGATION", "SECURITY_FORCES",
    "TERROR", "EXTREMISM", "BOMBING", "EXPLOSION",
    "COURT", "TRIAL", "SENTENCING", "PROSECUTION", "JUDICIARY",
    "PUBLIC_SAFETY", "EMERGENCY_SERVICES", "FIRE_DEPARTMENT",
    # Strong additions
    "VIOLENT_CRIME", "GANG_VIOLENCE", "ORGANIZED_CRIME", "CARTELS",
    "DRUG_VIOLENCE", "SEXUAL_VIOLENCE", "DOMESTIC_VIOLENCE",
    "HATE_CRIME", "RACIAL_VIOLENCE", "ETHNIC_VIOLENCE",
    "WEAPONS", "GUN_VIOLENCE", "ILLEGAL_WEAPONS", "ARMS_TRAFFICKING",
    "DRUG_TRAFFICKING", "NARCOTICS", "HUMAN_TRAFFICKING",
    "SMUGGLING", "SEX_TRAFFICKING",
    "CYBERCRIME", "CYBER_ATTACK", "HACKING", "DATA_BREACH", "RANSOMWARE",
    "LAW_CRIME", "CRIMINAL_JUSTICE", "PRISON", "INCARCERATION",
    "DETENTION", "FORENSICS", "LEGAL_ACTION", "JUDICIAL_PROCESS",

    # Secondary additions
    "RIOT", "UNREST", "CIVIL_DISORDER", "PROTEST_VIOLENCE",
    "NATIONAL_SECURITY", "PUBLIC_ORDER", "THREAT", "RISK",
    "INSURGENCY", "MILITANCY",
    "FIRST_RESPONDERS", "MEDICAL_EMERGENCY", "DISASTER_RESPONSE",
    "FRAUD", "CORRUPTION", "MONEY_LAUNDERING", "BRIBERY", "FINANCIAL_CRIME",

    # Optional harm-related themes
    "ABUSE", "HARASSMENT", "SEX_OFFENSES", "CHILD_ABUSE",
    "ELDER_ABUSE", "EXPLOITATION", "MISCONDUCT",
    
    "SECURITY_SERVICES",
    "TAX_FNCACT_POLICE",
    "TAX_FNCACT_OFFICERS",
    "TAX_FNCACT_DETECTIVES",
    "TAX_FNCACT_INSPECTOR",
    "TAX_FNCACT_MAGISTRATES",
    "TAX_FNCACT_VICTIM",
    "TAX_FNCACT_KILLER",

    "WB_840_JUSTICE",
    "WB_1014_CRIMINAL_JUSTICE",
    "SOC_GENERALCRIME",

    "CRISISLEX_T02_INJURED",
    "CRISISLEX_T03_DEAD",
    "WOUND",
    "KILL",
    "WB_1428_INJURY",

    "WB_2433_CONFLICT_AND_VIOLENCE",
    "WB_2432_FRAGILITY_CONFLICT_AND_VIOLENCE",
    "UNGP_CRIME_VIOLENCE",

    "MANMADE_DISASTER_IMPLIED",
    "SEIZE",
    "BAN",
    "CRISISLEX_C07_SAFETY",
]

CRIME_HEADLINES = {
    "ARSON AND CRIMINAL DAMAGE": [
        r"\barson\b", r"\bset fire\b", r"\bset alight\b",
        r"\bfirebomb\b", r"\bpetrol bomb\b",
        r"\btorched\b", r"\bblaze\b",
        r"\bpolice vehicles on fire\b"
],
    "BURGLARY": [
        r"\bburglary\b", r"\bburglar\b", r"\bburgled\b",
        r"\bbreak-in\b", r"\bbreak in\b",
        r"\bhousebreaking\b", r"\bforced entry\b",
        r"\bnight-time burglary\b",
        r"\bshoplifter\b", r"\bshoplifting\b"
],
    "DRUG OFFENCES": [
        r"\bdrug\b", r"\bdrugs\b", r"\bdrug dealer\b", r"\bdrug kingpin\b",
        r"\bdrug factory\b", r"\bdrug bust\b", r"\bdrug haul\b",
        r"\bclass a drugs\b", r"\bclass b drugs\b",
        r"\bcrack cocaine\b", r"\bheroin\b", r"\bmdma\b",
        r"\bcocaine\b", r"\bnarcotics\b",
        r"\btrafficking\b", r"\bsmuggling\b",
        r"\bcounty lines\b", r"\bcannabis farm\b", r"\bgrow house\b",
        r"\bdealing drugs\b"
],
    "POSSESSION OF WEAPONS": [
        r"\bweapon\b", r"\bweapons\b",
        r"\bfirearms\b", r"\bgun\b", r"\bgunman\b",
        r"\bknife\b", r"\bknife-wielding\b",
        r"\bbrandished a knife\b",
        r"\barmed with\b"
],
    "PUBLIC ORDER OFFENCES": [
        r"\bviolent disorder\b",
        r"\bpublic order\b",
        r"\briot\b",
        r"\baffray\b",
        r"\bthreatening behaviour\b",
        r"\bdisorderly\b"
],
    "ROBBERY": [
        r"\brobbery\b", r"\brobbed\b", r"\barmed robbery\b",
        r"\bmugging\b", r"\bheist\b",
        r"\bhoneytrap\b", r"\bhoneytrap plot\b",
        r"\bintruder\b",
        r"\braid\b", r"\bsmash-and-grab\b",
        r"\bheld at knifepoint\b", r"\bheld at gunpoint\b",
        r"\bcashpoint robbery\b", r"\brobbery spree\b"
],
    "SEXUAL OFFENCES": [
        r"\brape\b", r"\braped\b", r"\brapist\b",
        r"\bsexual assault\b", r"\bsexual harassment\b",
        r"\bsex attack\b",
        r"\bsexually assaulted\b", r"\bsexually abused\b",
        r"\bchild sex abuse\b", r"\bchild sexual exploitation\b",
        r"\bsex abuse\b", r"\bsex offender\b",
        r"\bgrooming\b", r"\bgroomed\b",
        r"\bindecent assault\b", r"\bindecent images\b",
        r"\bpaedo\b", r"\bpaedophile\b", r"\bpaedo ring\b"
],
    "THEFT": [
        #BICYCLE THEFT
        r"\bbike theft\b",
        r"\bbicycle theft\b",
        r"\bstolen bike\b",
        r"\bstole a bike\b",
        r"\bbike stolen\b",
        r"\bbike thief\b",
        r"\bbicycle thief\b",
        r"\btaken bike\b",
        r"\bpedal cycle theft\b",
        r"\bcycle theft\b",

    #SHOPLIFTING
        r"\bshoplifting\b",
        r"\bshoplifter\b",
        r"\bstole from shop\b",
        r"\bretail theft\b",
        r"\bstore theft\b",
        r"\bconcealed items\b",
        r"\bwalked out without paying\b",
        r"\btheft from store\b",

    #THEFT FROM THE PERSON
        r"\btheft from the person\b",
        r"\bpickpocket\b",
        r"\bpickpocketing\b",
        r"\bphone snatch\b",
        r"\bphone stolen from hand\b",
        r"\bgrabbed.*phone\b",
        r"\bhandbag snatch\b",
        r"\bbag snatch\b",
        r"\bdistraction theft\b",
        r"\bstolen from pocket\b",
        r"\bstolen from bag\b",
        r"\bstolen from hand\b",

    #OTHER THEFT
        r"\btheft\b",
        r"\bstole\b",
        r"\bstolen\b",
        r"\bstealing\b",
        r"\bproperty stolen\b",
        r"\bitems stolen\b",
        r"\bpersonal items stolen\b",
        r"\bwallet stolen\b",
        r"\bpurse stolen\b",
        r"\btools stolen\b",
        r"\bconstruction equipment stolen\b",
        r"\bmetal theft\b",
        r"\bcopper theft\b",
        r"\btheft of mail\b",
        r"\bparcel theft\b",
        r"\bpackage stolen\b"


],
    "VEHICLE OFFENCES": [
        r"\bcar theft\b", r"\bvehicle theft\b",
        r"\bstolen car\b", r"\bstole a car\b",
        r"\bcarjacking\b",
        r"\bhit and run\b",
        r"\bdrink driving\b", r"\bdrunk driving\b",
        r"\bdangerous driving\b",
        r"\bvehicle crime\b",
        r"\bcar crash\b",
        r"\bcar crashes\b"
    ],
    "VIOLENCE AGAINST THE PERSON": [

        # STALKING & HARASSMENT
        r"\bstalking\b",
        r"\bstalker\b",
        r"\bharassment\b",
        r"\bharassed\b",
        r"\bcoercive control\b",
        r"\bcontrolling behaviour\b",
        r"\bthreatening behaviour\b",
        r"\bintimidation\b",
        r"\bobsessed with\b",
        r"\bunwanted contact\b",
        r"\bcontacted repeatedly\b",
        r"\bissued threats\b",

        # VIOLENCE WITH INJURY (non‑weapon)
        r"\bassault\b",
        r"\bserious assault\b",
        r"\battacked\b",
        r"\battack\b",
        r"\bbeaten\b",
        r"\bpunched\b",
        r"\bkicked\b",
        r"\bglass attack\b",
        r"\bglassed\b",
        r"\battacked with\b",   # e.g., attacked with hammer, bottle, brick
        r"\blife-changing injuries\b",
        r"\bviolent disorder\b",
        r"\bkilled\b",

        # VIOLENCE WITHOUT INJURY
        r"\bcommon assault\b",
        r"\bthreatened\b",
        r"\bverbal abuse\b",
        r"\bconfrontation\b",
        r"\bphysical altercation\b",
        r"\bscuffle\b",
        r"\bminor assault\b",
    ],

        "FRAUD AND FORGERY": [
            r"\bfraud\b", r"\bforgery\b",
            r"\bscam\b", r"\bscammer\b",
            r"\bidentity theft\b",
            r"\bforged documents\b"
    ],
        "NFIB FRAUD": [
            r"\bcyber fraud\b",
            r"\bonline scam\b",
            r"\bphishing\b",
            r"\bromance scam\b",
            r"\binvestment fraud\b",
            r"\bcrypto scam\b"
    ],
        "DOMESTIC ABUSE": [
            r"\bdomestic abuse\b", r"\bdomestic violence\b",
            r"\bcoercive control\b",
            r"\bpartner assaulted\b",
            r"\bex-partner\b",
            r"\bcontrolling behaviour\b"
    ],
        "KNIFE CRIME": [

            # Direct references
            r"\bknife\b",
            r"\bknifed\b",
            r"\bknife attack\b",
            r"\bknife crime\b",
            r"\bknife gang\b",
            r"\bknife-point\b",
            r"\bbrandished a knife\b",

            # Stabbing language
            r"\bstab\b",
            r"\bstabbed\b",
            r"\bstabbing\b",
            r"\bstabbings\b",
            r"\bmultiple stab wounds\b",
            r"\bstab wound\b",
            r"\bstab spree\b",
            r"\bstab rampage\b",
            r"\bknife wounds\b",

            # Weapon descriptions commonly used in UK headlines
            r"\bblade\b",
            r"\bbladed article\b",
            r"\bbladed weapon\b",
            r"\bsharp weapon\b",
            r"\bsharp object\b",

            # Threats involving knives
            r"\bthreatened with a knife\b",
            r"\bheld at knifepoint\b",
            r"\bat knifepoint\b",
            r"\bknife-point robbery\b",

            # Possession offences
            r"\bpossession of a knife\b",
            r"\bcarrying a knife\b",
            r"\bcarried a knife\b",
            r"\barmed with a knife\b",

            # Common UK press phrasing
            r"\bman with a knife\b",
            r"\bwoman with a knife\b",
            r"\byouth with a knife\b",
            r"\bteen with a knife\b",
        ],
        "GUN CRIME": [
            r"\bgun\b",
            r"\bgunman\b",
            r"\bgunmen\b",
            r"\barmed with a gun\b",
            r"\barmed with (a )?firearm\b",
            r"\bfirearm\b",
            r"\bfirearms\b",
            r"\bhandgun\b",
            r"\brevolver\b",
            r"\bloaded gun\b",
            r"\bseized gun\b",
            r"\bgun possession\b",
            r"\billegal gun\b",
            r"\bgun threat\b",
            r"\bbrandished a gun\b",
            r"\bheld at gunpoint\b",
            r"\bgunpoint robbery\b",
            r"\bgun robbery\b"
    ],
        "LETHAL BARREL DISCHARGE": [
        r"\bshot\b",
        r"\bshots fired\b",
        r"\bshot dead\b",
        r"\bshot in the\b",
        r"\bshot and killed\b",
        r"\bshot multiple times\b",
        r"\bgunfire\b",
        r"\bgunshots\b",
        r"\bopened fire\b",
        r"\bdrive[- ]?by shooting\b",
        r"\bshooting\b",
        r"\bshootout\b",
        r"\bman was gunned down\b",
        r"\bgunned down\b",
    ],

    "HATE CRIME": [
        # RACIST & RELIGIOUS HATE
        r"\bracist\b",
        r"\bracism\b",
        r"\bracially\b",
        r"\bracial abuse\b",
        r"\bracist attack\b",
        r"\bracist incident\b",
        r"\bracist and religious\b",
        r"\breligious hate\b",
        r"\breligiously aggravated\b",

        # ANTISEMITIC
        r"\bantisemitic\b",
        r"\banti-semitic\b",
        r"\bantisemitism\b",
        r"\banti-semitism\b",
        r"\bjewish community\b",   # often used in hate‑crime reporting
        r"\bjewish man\b",
        r"\bjewish woman\b",

        # ISLAMOPHOBIC
        r"\bislamophobic\b",
        r"\banti-muslim\b",
        r"\banti islam\b",
        r"\banti-islam\b",
        r"\bmuslim community\b",

        # HOMOPHOBIC
        r"\bhomophobic\b",
        r"\bhomophobia\b",
        r"\bhomophobic attack\b",

        # TRANSPHOBIC
        r"\btransphobic\b",
        r"\btransphobia\b",
        r"\btransgender hate\b",

        # DISABILITY HATE CRIME
        r"\bdisability hate\b",
        r"\bdisability-related hate\b",
        r"\bdisabled man attacked\b",
        r"\bdisabled woman attacked\b",

        # FAITH-BASED HATE
        r"\bfaith hate\b",
        r"\bfaith-based hate\b",
        r"\bfaith crime\b",

        # GENERIC HATE CRIME TERMS
        r"\bhate crime\b",
        r"\bhate incident\b",
        r"\bhate-motivated\b"
],

"MISCELLANEOUS CRIMES AGAINST SOCIETY": [

    # HANDLING STOLEN GOODS / EQUIPMENT
    r"\bhandling stolen goods\b",
    r"\bgoing equipped for stealing\b",

    # THREAT TO COMMIT CRIMINAL DAMAGE
    r"\bthreat to commit criminal damage\b",
    r"\bthreat to damage\b",

    # DANGEROUS DRIVING (non‑fatal, non‑injury)
    r"\bdangerous driving\b",
    r"\breckless driving\b",

    # JUSTICE SYSTEM OFFENCES
    r"\bperverting the course of justice\b",
    r"\bpervert the course of justice\b",
    r"\bperjury\b",
    r"\bfalse statement\b",
    r"\bfalse or misleading\b",
    r"\bobstruction\b",
    r"\bobstructing police\b",

    # BAIL & CUSTODY OFFENCES
    r"\bbail offences?\b",
    r"\bbreach of bail\b",
    r"\babsconding from lawful custody\b",
    r"\babsconded from custody\b",

    # FALSE DOCUMENTS / FORGERY (non‑fraud)
    r"\bpossession of false documents?\b",
    r"\bfalse passport\b",
    r"\bfalse ID\b",
    r"\bforgery\b",
    r"\bother forgery\b",

    # OBSCENE PUBLICATIONS
    r"\bobscene publications?\b",

    # PROCEEDS OF CRIME (non‑fraud)
    r"\bconcealing proceeds of crime\b",
    r"\bproceeds of crime\b",

    # PROSTITUTION‑RELATED (non‑sexual‑offence)
    r"\bexploitation of prostitution\b",

    # WILDLIFE / ENVIRONMENTAL OFFENCES
    r"\bwildlife crime\b",
    r"\billegal hunting\b",
    r"\bpoaching\b",

    # OTHER NOTIFIABLE OFFENCES (catch‑all)
    r"\bother notifiable offences?\b",
    r"\bmisc crimes against society\b",
    # MOBILE PHONE SUBTYPES
    r"\brobbery mobile phone\b",
    r"\bmobile phone robbery\b",
    r"\bphone robbery\b",
    r"\bphone theft\b",
    r"\btheft person - mobile phone\b",
    r"\bmobile phone theft\b",

    # TNO ADMIN LABELS
    r"\btno non victim based\b",
    r"\btno victim based\b",
    
],



"UNKNOWN": []}






#-----USED FOR EXTRACT_HEADLINE FUNCTIONS-----------------
ACRONYMS = {
    # Existing
    "uk", "us", "eu", "un", "uae", "nato", "covid", "covid-19",
    "nhs", "bbc", "nyc", "lgbt", "lgbtq", "met", "g7", "g20",

    # UK Government & Politics
    "pm", "mp", "mps", "tory", "lab", "labour", "snp", "dup", "uup",
    "pla", "gov", "dwp", "hmrc", "moj", "mod", "hoc", "hol",

    # Police & Justice
    "nca", "sfo", "cps", "npcc", "psni", "btp",

    # London Transport & Geography
    "tfl", "dlr", "m25", "a40", "a406", "a1m", "m1", "m4", "m11",
    "lhr", "lgw", "ltn", "stn", "city", "heathrow", "gatwick",

    # Media & Tech
    "sky", "itv", "cnn", "ft", "nyt", "ai", "vr", "5g",

    # Crime & Emergency
    "cctv", "asbo", "foi", "sos", "999",

    # International
    "who", "wto", "imf", "opec", "gaza", "isis", "idf",

    # Misc common headline acronyms
    "ukip", "brexit", "covid19", "covid-19", "fifa", "uefa",
    "pr", "hr", "ceo", "cfo", "ngo"
}


STOPWORDS = {
    # Existing
    "and", "or", "the", "a", "an", "of", "in", "on", "for", "to",
    "with", "at", "by", "from", "as", "after", "over", "under",

    # Common headline fillers
    "into", "onto", "off", "up", "down", "out", "about",
    "across", "through", "via", "towards", "against",

    # British phrasing
    "amid", "amidst", "despite", "whilst", "among", "amongst",

    # Time words often dropped in normalization
    "during", "before", "until", "since",

    # Glue words
    "that", "this", "those", "these", "their", "its", "his", "her",

    # Modal / helper verbs
    "is", "was", "were", "be", "been", "being",
    "do", "does", "did",
    "has", "have", "had",

    # Articles / determiners
    "my", "your", "our", "their",

    # Misc headline filler
    "just", "only", "still", "even"
}


# INTENSITY_KEYWORDS = {
#     # High intensity (+2 or +3)
#     "fatal": 3,
#     "catastrophic": 3,
#     "devastating": 3,
#     "life-threatening": 2,
#     "critical": 2,
#     "severe": 2,
#     "grave": 2,
#     "dire": 2,
#     "extreme": 2,
#     "violent": 2,
#     "brutal": 2,

#     # Moderate intensity (+1)
#     "serious": 1,
#     "significant": 1,
#     "concerning": 1,
#     "heightened": 1,
#     "elevated": 1,
#     "urgent": 1,
#     "harmful": 1,

#     # Low intensity (0 or -1)
#     "minor": -1,
#     "slight": -1,
#     "limited": -1,
#     "manageable": -1,

#     # De-escalating (-1 or -2)
#     "attempted": -1,
#     "unsuccessful": -1,
#     "non-serious": -1,
#     "low-risk": -1,
#     "improving": -1,
#     "resolved": -2,
# }


GKG_COLS = [
    "GKGRECORDID","V2.1DATE","V2SOURCECOLLECTIONIDENTIFIER","V2SOURCECOMMONNAME",
    "V2DOCUMENTIDENTIFIER","V1COUNTS","V2.1COUNTS","V1THEMES","V2ENHANCEDTHEMES",
    "V1LOCATIONS","V2ENHANCEDLOCATIONS","V1PERSONS","V2ENHANCEDPERSONS",
    "V1ORGANIZATIONS","V2ENHANCEDORGANIZATIONS","V1.5TONE","V2.1ENHANCEDDATES",
    "V2GCAM","V2.1SHARINGIMAGE","V2.1RELATEDIMAGES","V2.1SOCIALIMAGEEMBEDS",
    "V2.1SOCIALVIDEOEMBEDS","V2.1QUOTATIONS","V2.1ALLNAMES","V2.1AMOUNTS",
    "V2.1TRANSLATIONINFO","V2EXTRASXML"
]

# Most Frequently Used National News Outlets in the UK
UK_SITES = [
    "ALJAZEERA.COM",
    "BANBURYGUARDIAN.CO.UK",
    "BARKINGANDDAGENHAMPOST.CO.UK",
    "BBC.CO.UK",
    "BECKHILLADVERTISER.NET",
    "BEXLEYTIMES.CO.UK",
    "BIGGIN-HILL-TODAY.CO.UK",
    "BOREHAMWOODTIMES.CO.UK",
    "BROMLEYTIMES.CO.UK",
    "BUZZFEEDNEWS.COM",
    "CAMDENNEWJOURNAL.COM",
    "CNN.COM",
    "CROYDONGUARDIAN.CO.UK",
    "EALINGGAZETTE.CO.UK",
    "EALINGTIMES.CO.UK",
    "EASTLONDONADVERTISER.CO.UK",
    "ENFIELDINDEPENDENT.CO.UK",
    "EPSOMGUARDIAN.CO.UK",
    "FT.COM",
    "FULHAMCHRONICLE.CO.UK",
    "GBNEWS.COM",

    # London-Based Regional News Outlets:
    "GETSURREY.CO.UK",
    "GOOGLE.NEWS.COM",
    "GUARDIAN-SERIES.CO.UK",
    "HAMHIGH.CO.UK",
    "HARLOWTIMES.CO.UK",
    "HARINGEYINDEPENDENT.CO.UK",
    "HILLINGDONTIMES.CO.UK",
    "HUFFPOST.COM",
    "ILFORDRECORDER.CO.UK",
    "INDEPENDENT.CO.UK",
    "ISLINGTONGAZETTE.CO.UK",
    "ITV.COM/NEWS",
    "KILBURNTIMES.CO.UK",
    "KINGSTONGUARDIAN.CO.UK",
    "LADBIBLE.COM",
    "METRO.CO.UK",
    "MIRROR.CO.UK",
    "MSN.COM",
    "NEWHAMRECORDER.CO.UK",
    "NEWS.GOOGLE.COM",
    "NEWS.SKY.COM",
    "NEWS.YAHOO.COM",
    "NEWSSHOPPER.CO.UK",
    "RICHMONDANDTWICKENHAMTIMES.CO.UK",
    "ROMFORDRECORDER.CO.UK",
    "SURREYCOMET.CO.UK",
    "SUTTONGUARDIAN.CO.UK",
    "TELEGRAPH.CO.UK",
    "THEGUARDIAN.COM",
    "THESUN.CO.UK",
    "THETIMES.CO.UK",
    "THISISCROYDONTODAY.CO.UK",
    "TIMES-SERIES.CO.UK",
    "TOTTENHAMJOURNAL.CO.UK",
    "UXBRIDGEGAZETTE.CO.UK",
    "WANDSWORTHGUARDIAN.CO.UK",
    "WESTENDEXTRA.COM",
    "WIMBLEDONGUARDIAN.CO.UK",
    "YELLOWADVERTISER-TODAY.CO.UK",
    "YOURLOCALGUARDIAN.CO.UK"
]


GREATER_LONDON_LOC = [
    "LONDON",
    "CITY OF LONDON",
    "WESTMINSTER",
    "CAMDEN",
    "ISLINGTON",
    "HACKNEY",
    "TOWER HAMLETS",
    "GREENWICH",
    "LEWISHAM",
    "SOUTHWARK",
    "LAMBETH",
    "WANDSWORTH",
    "HAMMERSMITH",
    "FULHAM",
    "KENSINGTON",
    "CHELSEA",
    "BRENT",
    "EALING",
    "HOUNSLOW",
    "RICHMOND",
    "KINGSTON",
    "MERTON",
    "SUTTON",
    "CROYDON",
    "BROMLEY",
    "BARNET",
    "HARROW",
    "HILLINGDON",
    "ENFIELD",
    "WALTHAM FOREST",
    "REDBRIDGE",
    "NEWHAM",
    "BARKING",
    "DAGENHAM",
    "HAVERING",

    # AREAS OF LONDON
    "ABBEY WOOD",
    "ACTON",
    "ACTON GREEN",
    "ADDINGTON",
    "ADDISCOMBE",
    "ALBANY PARK",
    "ALDBOROUGH HATCH",
    "ALDGATE",
    "ALDWYCH",
    "ALPERTON",
    "ANERLEY",
    "ANGEL",
    "APERFIELD",
    "ARCHWAY",
    "ARDLEIGH GREEN",
    "ARKLEY",
    "ARNOS GROVE",

    "BALHAM",
    "BANKSIDE",
    "BARBICAN",
    "BARKING",
    "BARKING RIVERSIDE",
    "BARKINGSIDE",
    "BARNEHURST",
    "BARNES",
    "BARNES CRAY",
    "BARNSBURY",
    "BAYSWATER",
    "BECKTON",
    "BELGRAVIA",
    "BELSZIE PARK",
    "BERMONDSEY",
    "BETHNAL GREEN",
    "BEXLEYHEATH",
    "BLACKFRIARS",
    "BLACKWALL",
    "BOUNDS GREEN",
    "BOW",
    "BOW COMMON",
    "BRENT CROSS",
    "BRIXTON",
    "BROMLEY BY BOW",
    "BROMPTON",

    "CAMBRIDGE HEATH",
    "CAMDEN TOWN",
    "CANNING TOWN",
    "CARSHALTON",
    "CHADWELL HEATH",
    "CHELSEA",
    "CHINATOWN",
    "CHINGFORD",
    "CHIPPING BARNET",
    "CHISLEHURST",
    "CHISWICK",
    "CLAPHAM",
    "CLAPTON",
    "COVENT GARDEN",
    "COWLEY",
    "CRAYFORD",
    "CRICKLEWOOD",
    "CROUCH END",

    "DAGENHAM",
    "DALSTON",
    "DEPTFORD",
    "DOWNHAM",

    "EAST END",
    "EAST HAM",
    "EASTCOTE",
    "EDGWARE",
    "EDMONTON",
    "ENFIELD CHASE",

    "FARRINGDON",
    "FINCHLEY",
    "FITZROVIA",
    "FOREST GATE",
    "FRIERN BARNET",
    "FROGNAL",
    "FULHAM",

    "GOLDERS GREEN",
    "GROVE PARK",
    "GUNNERSBURY",

    "HACKNEY",
    "HACKNEY CENTRAL",
    "HACKNEY WICK",
    "HAGGERSTON",
    "HANWELL",
    "HARRINGAY",
    "HARROW ON THE HILL",
    "HENDON",
    "HERNE HILL",
    "HESTON",
    "HIGHBURY",
    "HIGHGATE",
    "HITHER GREEN",
    "HOMERTON",
    "HONOR OAK",
    "HORNCHURCH",
    "HORNSEY",
    "HOXTON",

    "ILFORD",
    "ISLEWORTH",
    "ISLINGTON",

    "KENTISH TOWN",
    "KENTON",
    "KILBURN",
    "KINGS CROSS",
    "KING'S CROSS",

    "LADBROKE GROVE",
    "LEE",
    "LEYTON",
    "LEYTONSTONE",
    "LIMEHOUSE",

    "MAIDA VALE",
    "MANOR PARK",
    "MAYFAIR",
    "MILE END",
    "MILL HILL",
    "MILLBANK",
    "MILLWALL",
    "MORDEN",
    "MUSWELL HILL",

    "NEW BARNET",
    "NEW MALDEN",
    "NINE ELMS",
    "NORTH KENSINGTON",
    "NORTHOLT",
    "NOTTING HILL",
    "NUNHEAD",

    "OLD FORD",
    "ORPINGTON",
    "OVAL",

    "PADDINGTON",
    "PALMERS GREEN",
    "PARK ROYAL",
    "PECKHAM",
    "PENGE",
    "PIMLICO",
    "PLAISTOW",
    "PLUMSTEAD",
    "PONDERS END",
    "POPLAR",
    "PUTNEY",

    "RAINHAM",
    "RAVENSCOURT PARK",
    "RAYNERS LANE",
    "REDBRIDGE",
    "RICHMOND",
    "ROEHAMPTON",
    "ROTHERHITHE",

    "SEVEN SISTERS",
    "SHADWELL",
    "SHEPHERD'S BUSH",
    "SHEPHERDS BUSH",
    "SHOREDITCH",
    "SIDCUP",
    "SILVERTOWN",
    "SLADE GREEN",
    "SNARESBROOK",
    "SOUTH KENSINGTON",
    "SOUTH NORWOOD",
    "SOUTHALL",
    "SOUTHGATE",
    "SOUTHWARK",
    "ST JOHN'S WOOD",
    "ST JOHNS WOOD",
    "ST PAUL'S CRAY",
    "ST PAULS CRAY",
    "STREATHAM",
    "STRATFORD",
    "SUDBURY",
    "SUTTON",
    "SYDENHAM",

    "TEDDINGTON",
    "TEMPLE",
    "THAMESMEAD",
    "THORNTON HEATH",
    "TOOTING",
    "TOTTENHAM",
    "TOTTERIDGE",
    "TOWER HILL",
    "TUFNELL PARK",
    "TULSE HILL",
    "TURNPIKE LANE",
    "TWICKENHAM",

    "UPMINSTER",
    "UPMINSTER BRIDGE",
    "UPNEY",
    "UPPER CLAPTON",
    "UPPER HOLLOWAY",
    "UPPER NORWOOD",
    "UPPER RUXLEY",
    "UPPER WALTHAMSTOW",
    "UPTON",
    "UPTON PARK",
    "UXBRIDGE",

    "VAUXHALL",

    "WADDON",
    "WALLINGTON",
    "WALTHAMSTOW",
    "WALTHAMSTOW VILLAGE",
    "WALWORTH",
    "WANDSWORTH",
    "WANSTEAD",
    "WAPPING",
    "WEALDSTONE",
    "WELL HALL",
    "WELLING",
    "WEMBLEY",
    "WEMBLEY PARK",
    "WENNINGTON",
    "WEST BROMPTON",
    "WEST DRAYTON",
    "WEST DULWICH",
    "WEST EALING",
    "WEST GREEN",
    "WEST HACKNEY",
    "WEST HAM",
    "WEST HAMPSTEAD",
    "WEST HARROW",
    "WEST HEATH",
    "WEST HENDON",
    "WEST KENSINGTON",
    "WEST NORWOOD",
    "WEST WICKHAM",
    "WESTCOMBE PARK",
    "WESTMINSTER",
    "WHETSTONE",
    "WHITE CITY",
    "WHITECHAPEL",
    "WIDMORE",
    "WHITTON",
    "WILLESDEN",
    "WIMBLEDON",
    "WINCHMORE HILL",
    "WOOD GREEN",
    "WOODFORD",
    "WOODFORD BRIDGE",
    "WOODFORD WELLS",
    "WOODFORD GREEN",
    "WOODLANDS",
    "WOODSIDE",
    "WOODSIDE PARK",
    "WOOLWICH",
    "WORCESTER PARK",
    "WORMWOOD SCRUBS",

    "YEADING",
    "YIEWSLEY"    
]
