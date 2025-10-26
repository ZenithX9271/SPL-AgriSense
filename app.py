# streamlit_app.py - V14.0 (FINAL: Theme Button Now Changes Background/Text Colors)

import streamlit as st
import pandas as pd
import datetime
import time
import json
import random
import uuid
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
import requests
import numpy as np
import os
from dotenv import load_dotenv 
from groq import Groq
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import sendgrid
from sendgrid.helpers.mail import Mail

# --- ARGOS TRANSLATE IMPORTS ---
import argostranslate.package
import argostranslate.translate
# -------------------------------

# --- Configuration & Setup ---

PROJECT_NAME = "SPL-AgriSense"
MOCK_DATABASE_FILE = "mock_db.json"

# 1. API KEYS (CRITICAL SEPARATION)
SENDGRID_API_KEY = st.secrets['SENDGRID_API_KEY']             
GROQ_API_KEY = st.secrets['GROQ_API_KEY']                 

# 2. FERTILIZER CONTACT/EMAIL
MOCK_FERTILIZER_SHOP_CONTACT = "+91-99999 88 777"
MOCK_FERTILIZER_SHOP_EMAIL = "shash9271@gmail.com"

# 3. TEMPLATE & SENDER INFO
OTP_SENDER_EMAIL = "shashankpidigovula@gmail.com"
FERTILIZER_TEMPLATE_ID = "d-ee7654e7d78f4b38b419da9edb172a48"

# LLM Mocks (Used only if GROQ key is missing)
LLM_MOCK_RESPONSE_CROP_PRESENT = "Mock Response (N/A Key): Analyze your data. Apply a high-Nitrogen fertilizer (20:10:10 NPK) to boost growth, avoiding heavy rains this week."
LLM_MOCK_RESPONSE_NO_CROP = "Mock Response (N/A Key): Based on the NPK values, the ideal starter crop is **Mustard (Rabi)**. Focus on balancing Phosphorus initially."

# File Paths (For Developer Details Page)
PROF_IMAGE_PATH = 'Pictures/Prof_Image.jpg' 
SHASHANK_IMAGE_PATH = 'Pictures/Shashank_Image.jpeg'
RAJU_IMAGE_PATH = 'Pictures/Raju_Image.jpeg'
GAURAV_IMAGE_PATH = 'Pictures/Gaurav_Image.jpeg'
# PROF_IMAGE_PATH = '/Users/shash/Library/CloudStorage/OneDrive-IITDelhi/Currently Doing/Gemini/Pictures/Prof_Image.jpg' 
# SHASHANK_IMAGE_PATH = '/Users/shash/Library/CloudStorage/OneDrive-IITDelhi/Currently Doing/Gemini/Pictures/Shashank_Image.jpeg'
# RAJU_IMAGE_PATH = '/Users/shash/Library/CloudStorage/OneDrive-IITDelhi/Currently Doing/GemINI/Pictures/Raju_Image.jpeg'
# GAURAV_IMAGE_PATH = '/Users/shash/Library/CloudStorage/OneDrive-IITDelhi/Currently Doing/Gemini/Pictures/Gaurav_Image.jpeg'

st.set_page_config(page_title=PROJECT_NAME, layout="wide")

# ====================================================================
# --- CUSTOM THEME SETUP (MODIFIED TO FORCE BACKGROUND CHANGE) ---
# ====================================================================

# Define custom color palettes
THEME_PALETTES = {
    'AgriSense Dark': {
        'name': 'AgriSense Dark',
        'primary_color': '#4CAF50',        # Primary Button/Accent Color (Green)
        'main_bg': '#0E1117',              # Main Page Background (Dark)
        'secondary_bg': '#1F2430',         # Sidebar/Secondary Background (Darker Grey)
        'text_color': '#FFFFFF'            # Text Color (White)
    },
    'AgriSense Light': {
        'name': 'AgriSense Light',
        'primary_color': '#1E88E5',        # Primary Button/Accent Color (Blue)
        'main_bg': '#FFFFFF',              # Main Page Background (White)
        'secondary_bg': '#F0F2F6',         # Sidebar/Secondary Background (Light Grey)
        'text_color': '#262730'            # Text Color (Dark Grey)
    }
}

def inject_custom_css(theme):
    """Injects CSS to dynamically change primary color, background, and text."""
    
    # CSS targets specific Streamlit elements to override the default theme
    css = f"""
    <style>
        /* 1. Force background and text colors */
        .stApp {{
            background-color: {theme['main_bg']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* 2. Force Sidebar Background */
        .css-vk3258, .css-1dp5vir {{ /* These classes target the main page and sidebar */
            background-color: {theme['secondary_bg']} !important;
        }}
        
        /* 3. Force Primary Button Color */
        div.stButton > button[data-baseweb="button"], .stMarkdown button {{
            background-color: {theme['primary_color']} !important;
            border-color: {theme['primary_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* 4. Force General Text/Markdown Color */
        .stMarkdown, .stText, .stDataFrame, .stMetric, .stSelectbox label, .stTextInput label, .stDateInput label {{
            color: {theme['text_color']} !important;
        }}
        
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    

# ====================================================================
# --- CRITICAL LOCALIZATION ENGINE (Placed BEFORE ANY FUNCTION CALLS) ---
# ====================================================================

# Map of your custom codes to Argos codes
LANG_CODE_MAP = {
    'en': 'en', 'hi': 'hi', 'te': 'te', 'bn': 'bn', 'mr': 'mr', 
    'gu': 'gu', 'ta': 'ta', 'kn': 'kn', 'ml': 'ml', 'pa': 'pa' 
}
LANG_DISPLAY_MAP = {'en': 'English', 'hi': 'हिन्दी', 'te': 'తెలుగు (Telugu)', 'bn': 'বাংলা (Bengali)', 'mr': 'मराठी (Marathi)', 'gu': 'ગુજરાતી (Gujarati)', 'ta': 'தமிழ் (Tamil)', 'kn': 'ಕನ್ನಡ (Kannada)', 'ml': 'മലയാളം (Malayalam)', 'pa': 'ਪੰਜਾਬੀ (Punjabi)'}


# 1. Define the BASE Dictionary (Corrected structure)
LANG_DICT = {
    "en": {
        "nav_home": "🏠 Home", "nav_soil_results": "🧪 Soil Test Results", "nav_weather": "🌤️ Detailed Weather Forecast",
        "nav_profile": "👤 User Profile", "nav_developer": "💻 Developer Details",
        "welcome_greeting": "Hey {name}, Welcome to **{project}** 🇮🇳",
        "welcome_subtitle": "Your AI-Powered Agricultural Intelligence Platform", "developed_by": "Developed by Shashank",
        "logout_btn": "Logout", "login_title": "🌾 Welcome to {project} - Farmer Login", "login_btn": "Login",
        "signup_btn": "Create Account", "send_otp_btn": "Send OTP", "verify_btn": "Verify OTP & Create Account",
        "soil_header": "Comprehensive Field History", "soil_intro": "Below are the real-time results collected by your **{project}** device. Click on any test to analyze soil health and receive AI guidance.",
        "soil_box_header": "🔬 Test Result from {timestamp} at *{location}*", "data_header": "Soil & Crop Data",
        "crop_health_index": "Crop Health Index", "ai_agronomist_advice": "🧠 Get AI Agronomist Advice",
        "propose_crop": "🌱 Propose Optimal Crop", "partner_connect": "📞 Fertilizer Partner Connect", 
        "ask_chat": "💬 Ask Agronomist Chat", "delete_btn": "🗑️ Delete",
        "temp_unit": "°C", "rain_unit": "mm", "location_input": "Enter Location Name (Village/City)",
        "date_input": "Select Forecast Date", "fetch_btn": "Fetch Detailed Weather Forecast",
        "coords": "Field Coordinates", "avg_temp": "Avg Temp", "max_rain": "Max Rainfall",
        "action_insights": "Actionable Insights", "close_chat": "Close Chat", "subs_notifs": "Subscription & Notifications",
        "enable_notifs": "**Enable Fertilizer Partner Notifications**", "confirm_notif_enable": "Notifications are now **{status}**.",
        "data_shared": "**Data Shared!** Report sent to **{email}**. Partner will contact farmer directly.",
        "delete_success": "Test record deleted.", "no_tests": "No soil test results found. Please use the device to perform your first test."
    },
    "hi": { # Hindi translations (Your original provided content)
        "nav_home": "🏠 होम", "nav_soil_results": "🧪 मिट्टी परीक्षण परिणाम", "nav_weather": "🌤️ विस्तृत मौसम पूर्वानुमान",
        "nav_profile": "👤 उपयोगकर्ता प्रोफ़ाइल", "nav_developer": "💻 डेवलपर विवरण",
        "welcome_greeting": "नमस्ते {name}, **{project}** में आपका स्वागत है 🇮🇳",
        "welcome_subtitle": "आपका AI-संचालित कृषि बुद्धिमत्ता मंच", "developed_by": "शशांक द्वारा विकसित",
        "logout_btn": "लॉगआउट", "login_title": "🌾 {project} में आपका स्वागत है - किसान लॉगिन", "login_btn": "लॉगिन करें",
        "signup_btn": "खाता बनाएं", "send_otp_btn": "ओटीपी भेजें", "verify_btn": "ओटीपी सत्यापित करें और खाता बनाएं",
        "soil_header": "व्यापक क्षेत्र इतिहास", "soil_intro": "नीचे आपके **{project}** डिवाइस द्वारा एकत्र किए गए वास्तविक समय के परिणाम दिए गए हैं। मार्गदर्शन के लिए किसी भी परीक्षण पर क्लिक करें।",
        "soil_box_header": "🔬 {location} पर {timestamp} से परीक्षण परिणाम*", "data_header": "मिट्टी और फसल डेटा",
        "crop_health_index": "फसल स्वास्थ्य सूचकांक", "ai_agronomist_advice": "🧠 AI कृषि विशेषज्ञ सलाह लें",
        "propose_crop": "🌱 इष्टतम फसल सुझाएं", "partner_connect": "📞 उर्वरक भागीदार से जुड़ें", 
        "ask_chat": "💬 कृषि विशेषज्ञ से चैट करें", "delete_btn": "🗑️ हटाएं",
        "temp_unit": "°C", "rain_unit": "मिमी", "location_input": "स्थान का नाम (गांव/शहर) दर्ज करें",
        "date_input": "पूर्वानुमान तिथि चुनें", "fetch_btn": "विस्तृत मौसम पूर्वानुमान प्राप्त करें",
        "coords": "क्षेत्र निर्देशांक", "avg_temp": "औसत तापमान", "max_rain": "अधिकतम वर्षा",
        "action_insights": "कार्रवाई योग्य अंतर्दृष्टि", "close_chat": "चैट बंद करें", "subs_notifs": "सदस्यता और सूचनाएं",
        "enable_notifs": "**उर्वरक भागीदार सूचनाएं सक्षम करें**", "confirm_notif_enable": "सूचनाएं अब **{status}** हैं।",
        "data_shared": "**डेटा साझा किया गया!** रिपोर्ट **{email}** को भेजी गई। भागीदार आपसे संपर्क करेगा।",
        "delete_success": "परीक्षण रिकॉर्ड हटा दिया गया।", "no_tests": "कोई मिट्टी परीक्षण परिणाम नहीं मिला। कृपया अपना पहला परीक्षण करने के लिए डिवाइस का उपयोग करें।"
    },
    # The remaining 8 languages start as copies of English for fallback:
    "te": {}, "bn": {}, "mr": {}, "gu": {}, "ta": {}, "kn": {}, "ml": {}, "pa": {},
}

# 2. PERFORM CROSS-REFERENCE (AFTER LANG_DICT is fully defined)
for lang_code in ["te", "bn", "mr", "gu", "ta", "kn", "ml", "pa"]:
    LANG_DICT[lang_code] = LANG_DICT['en'].copy()

# Add specific translated navigation titles for sidebar/UI clarity
LANG_DICT["te"]["nav_home"] = "🏠 హోమ్ (Telugu)"
LANG_DICT["bn"]["nav_home"] = "🏠 হোম (Bengali)"
LANG_DICT["mr"]["nav_home"] = "🏠 होम (Marathi)"
LANG_DICT["gu"]["nav_home"] = "🏠 ગુજરાતી (Gujarati)"
LANG_DICT["ta"]["nav_home"] = "🏠 முகப்பு (Tamil)"
LANG_DICT["kn"]["nav_home"] = "🏠 ಮುಖಪುಟ (Kannada)"
LANG_DICT["ml"]["nav_home"] = "🏠 ഹോം (Malayalam)"
LANG_DICT["pa"]["nav_home"] = "🏠 ਘਰ (Punjabi)"


# --- Core Localization Functions ---

def get_lang_text(key):
    """Retrieves the localized string for the current language."""
    if 'current_lang' not in st.session_state:
        st.session_state['current_lang'] = 'en'
    
    lang = st.session_state['current_lang']
    
    if key in LANG_DICT[lang]:
        return LANG_DICT[lang][key]
    elif key in LANG_DICT['en']:
        return LANG_DICT['en'][key]
    else:
        return f"MISSING_TEXT:{key}"


def install_argos_models():
    """Installs required translation models (English <-> All 9 other languages)."""
    if 'argos_installed' not in st.session_state:
        st.session_state['argos_installed'] = False

    if st.session_state['argos_installed']:
        return

    st.info("🌐 Setting up offline translation models (Argos Translate)... This runs only once.")

    from_code = 'en'
    to_codes = [code for code in LANG_CODE_MAP.keys() if code != 'en']

    try:
        available_packages = argostranslate.package.get_available_packages()
        
        for to_code in to_codes:
            # Check for EN -> TARGET model
            pkg = next((p for p in available_packages if p.from_code == from_code and p.to_code == to_code), None)
            if pkg:
                argostranslate.package.install_from_path(pkg.download())
            
            # Check for TARGET -> EN model (for future LLM/User input translation back to EN)
            pkg_reverse = next((p for p in available_packages if p.from_code == to_code and p.to_code == from_code), None)
            if pkg_reverse and not pkg:
                 argostranslate.package.install_from_path(pkg_reverse.download())

        st.success("✅ Translation models are ready. Select your language from the sidebar.")
        st.session_state['argos_installed'] = True
        st.rerun()

    except Exception as e:
        st.error(f"Argos Model Setup Failed: {e}. Please ensure argostranslate is installed.")
        st.session_state['argos_installed'] = False


def translate_text(text, target_lang_code):
    """Translates text from English to the target language using Argos Translate."""
    if target_lang_code == 'en' or not st.session_state.get('argos_installed'):
        return text

    try:
        source_code = 'en'
        target_code = LANG_CODE_MAP.get(target_lang_code, 'en')

        return argostranslate.translate.translate(text, source_code, target_code)
    except Exception as e:
        # Fallback to English if translation fails
        return text


# --- Database & Utility Functions (Core Data Logic) ---

def load_db():
    try:
        with open(MOCK_DATABASE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}, "soil_tests": []}

def save_db(db):
    with open(MOCK_DATABASE_FILE, 'w') as f:
        json.dump(db, f, indent=4)
        
def check_user_by_credential(db, credential):
    for user_id, user_data in db['users'].items():
        if user_data['contact_or_email'] == credential:
            return user_id, user_data
    return None, None

def add_new_user(db, name, credential, password_hash):
    user_id = str(uuid.uuid4())
    db['users'][user_id] = {
        'user_id': user_id,
        'name': name,
        'contact_or_email': credential,
        'password': password_hash,
        'joined_on': datetime.datetime.now().strftime("%Y-%m-%d"),
        'enable_fertilizer_notifications': False,
    }
    save_db(db)
    return user_id

# ====================================================================
# --- CONSOLIDATED DATA SIMULATION ---
# ====================================================================

def generate_random_soil_data():
    """Generates a realistic set of random soil composition and nutrient data."""
    data = {
        # Soil Constituents (Percentages)
        'Organic_Matter_pct': round(random.uniform(0.5, 5.0), 2),
        'Clay_pct': round(random.uniform(10, 40), 2),
        'Silt_pct': round(random.uniform(20, 50), 2),
        
        # Nutrients (PPM)
        'Nitrogen_ppm': random.randint(50, 400),
        'Phosphorus_ppm': random.randint(10, 80),
        'Potassium_ppm': random.randint(100, 500),
        'pH_value': round(random.uniform(5.5, 8.5), 1),
        'EC_mS_cm': round(random.uniform(0.1, 4.0), 2), # Electrical Conductivity
    }
    # Adjust Sand to make it sum to 100 for simplicity in simulation
    data['Sand_pct'] = max(0, 100 - data['Organic_Matter_pct'] - data['Clay_pct'] - data['Silt_pct'])
    return data

def generate_simulation_output(user_contact_or_email, name, location_name):
    """Simulates the data output from the SPL-AgriSense device."""
    
    # Simulate Geo-location for a few Indian cities
    location_map = {
        "Pune, India": (18.5204, 73.8567),
        "Patna, India": (25.5941, 85.1376),
        "Ludhiana, India": (30.9010, 75.8573),
        "Hyderabad, India": (17.3850, 78.4867),
        "Kanpur, India": (26.4499, 80.3319),
    }
    
    # Use location_name to pick a geo-coordinate, or a random one if not mapped
    geo_loc = location_map.get(location_name, (random.uniform(10, 35), random.uniform(70, 88)))

    # Simulate YOLO model output (Current Crop)
    crops = ["Paddy", "Wheat", "Maize", "Sugarcane", "None Detected"]
    # 70% chance of a crop being present
    crop_present = random.choices(crops, weights=[0.2, 0.2, 0.2, 0.1, 0.3], k=1)[0]
    
    # Assemble the final data record
    data_record = {
        'Test_ID': str(uuid.uuid4()), # Unique ID for this test
        'Device_User_Name': name,
        'User_Contact_or_Email': user_contact_or_email,
        'Test_Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Location_Name': location_name,
        'Latitude': round(geo_loc[0], 4),
        'Longitude': round(geo_loc[1], 4),
        'Crop_Detected': crop_present,
        'Crop_Health_Index': round(random.uniform(0.5, 1.0) if crop_present != "None Detected" else 0.0, 2), # Simulated health index
        **generate_random_soil_data() # Unpack all soil data
    }
    
    return data_record

def simulate_new_soil_test(user_credential, user_name, field_location):
    """
    Simulates a new soil test and returns the data record.
    This is the function called to generate new data for the 'Run' button.
    """
    # In a real system, this is where the device data would be extracted.
    test_data = generate_simulation_output(user_credential, user_name, field_location)
    return test_data

def ensure_mock_data_exists(db, credential, name):
    user_tests = [test for test in db['soil_tests'] if test['User_Contact_or_Email'] == credential]
    if len(user_tests) < 2:
        for i in range(2 - len(user_tests)):
            db['soil_tests'].append(simulate_new_soil_test(
                credential, 
                name, 
                random.choice(["Pune, India", "Hyderabad, India"])
            ))
        save_db(db)
# ====================================================================

@st.cache_data(show_spinner=False)
def get_lat_lon(place_name):
    geolocator = Nominatim(user_agent=PROJECT_NAME)
    try:
        location = geolocator.geocode(place_name, country_codes='in')
        if location:
            return (location.latitude, location.longitude)
    except GeocoderServiceError:
        pass
    return None, None

@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, date):
    # Mock data fetch for demo speed
    return pd.DataFrame({'temperature_2m': np.random.uniform(20, 35, 24), 'rain': np.random.uniform(0, 5, 24)}, index=pd.to_datetime([f"{date} {h:02d}:00:00" for h in range(24)]))


# --- LLM Functions ---

def build_llm_chain():
    """Initializes and returns the LangChain LLM setup using Groq."""
    try:
        global GROQ_API_KEY
        
        if not GROQ_API_KEY:
            st.warning("⚠️ GROQ API Key is missing. Recommendations will be mocked.")
            return None
        
        llm = ChatGroq(
            api_key=GROQ_API_KEY, 
            model="llama-3.1-8b-instant" 
        )
        
        # Recommendation Prompt (For the initial recommendation button)
        prompt_template = """
        You are an expert AI Agronomist for Indian farmers, focused on providing **efficient, actionable, and profitable** advice. 
        Your recommendations must be tailored to the specific context of Indian agriculture, focusing on NPK ratios, local crop suitability, and seasonal weather patterns. 
        Analyze the following data and provide a concise recommendation in a clear, easy-to-read format (use bullet points and bolding) in less than 200 words.
        
        **CONTEXT:** {context}
        
        **INSTRUCTION:** If 'Crop Detected' is 'None Detected', recommend the single most profitable and resilient crop for the next season based on the soil and region, and the essential starter fertilizer. If a crop IS detected, recommend the exact NPK fertilizer ratio, specific dosage (in kg/acre), and ideal application timing/method based on the current weather and crop health.

        **RECOMMENDATION:**
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = LLMChain(prompt=prompt, llm=llm)
        return chain
        
    except Exception as e:
        return None

def build_clarification_prompt(soil_data, weather_df, user_question):
    """Generates the context-aware system prompt for the clarification chat."""
    
    # 1. Prepare Context String
    soil_context = f"N:{soil_data['Nitrogen_ppm']}ppm, P:{soil_data['Phosphorus_ppm']}ppm, K:{soil_data['Potassium_ppm']}ppm. pH:{soil_data['pH_value']}. EC:{soil_data['EC_mS_cm']} mS/cm."
    
    avg_temp = f"{weather_df['temperature_2m'].mean():.1f}" if not weather_df.empty else "N/A"
    max_rain = f"{weather_df['rain'].max():.1f}" if not weather_df.empty else "N/A"
    weather_context = f"Avg Temp: {avg_temp} °C, Max Rain: {max_rain} mm."
    
    context = f"""
    --- USER FIELD DATA ---
    Location: {soil_data['Location_Name']}, India (Lat: {soil_data['Latitude']}, Lon: {soil_data['Longitude']})
    Current Crop: {soil_data['Crop_Detected']} (Health: {soil_data['Crop_Health_Index']:.0%})
    Soil Analysis: {soil_context}
    Weather Forecast: {weather_context}
    ---
    """
    
    # 2. Prepare System Instruction
    system_instruction = f"""
    You are an extremely helpful, knowledgeable, and localized Indian AI Agronomist (Expert Chatbot). 
    Your primary role is to clarify the farmer's doubts by considering ALL the provided field data (Soil, Crop, Weather, Location).
    Keep responses concise, empathetic, and highly localized to the {soil_data['Location_Name']} region of India. 
    Use simple Hindi/local terminology where appropriate for clarity to an Indian farmer.
    Answer the user's question: "{user_question}".
    """
    
    return system_instruction, context

def get_recommendation_from_ai(soil_data, weather_df):
    chain = build_llm_chain()
    
    if chain is None:
        time.sleep(1.5)
        crop = soil_data['Crop_Detected']
        if crop != "None Detected":
            return LLM_MOCK_RESPONSE_CROP_PRESENT
        else:
            return LLM_MOCK_RESPONSE_NO_CROP

    avg_temp = f"{weather_df['temperature_2m'].mean():.1f}" if not weather_df.empty else "N/A"
    max_rain = f"{weather_df['rain'].max():.1f}" if not weather_df.empty else "N/A"
    
    context_data = f"""
    - Farmer Location: {soil_data['Location_Name']}, India (Lat: {soil_data['Latitude']}, Lon: {soil_data['Longitude']})
    - Soil Composition: N:{soil_data['Nitrogen_ppm']}ppm, P:{soil_data['Phosphorus_ppm']}ppm, K:{soil_data['Potassium_ppm']}ppm. pH:{soil_data['pH_value']}. EC:{soil_data['EC_mS_cm']} mS/cm.
    - Crop Status (YOLO): {soil_data['Crop_Detected']} (Health Index: {soil_data['Crop_Health_Index']:.0%})
    - Current Weather (24h Avg): Avg Temp: {avg_temp} °C, Max Rain: {max_rain} mm.
    """

    try:
        response = chain.run(context=context_data)
        return response
    except Exception as e:
        return f"LLM Run Failed. Error: {e}"

# --- SENDGRID EMAIL FUNCTIONS (REAL INTEGRATION) ---

def send_otp_email(email_address, otp_code):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        html_content = f"""
        <h1>{PROJECT_NAME} Verification Code</h1>
        <p>Your One-Time Password (OTP) is: <b>{otp_code}</b></p>
        <p>This code is valid for 5 minutes. Do not share it with anyone.</p>
        """
        message = Mail(
            from_email=OTP_SENDER_EMAIL,
            to_emails=email_address,
            subject=f"[{PROJECT_NAME}] Your OTP Verification Code",
            html_content=html_content
        )
        response = sg.send(message)
        return response.status_code == 202
        
    except Exception as e:
        print(f"OTP Email Error: {e}")
        return False

def send_fertilizer_email(user_data, soil_data):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
        dynamic_data = {
            "farmer_name": user_data.get('name', 'N/A'),
            "farmer_contact": user_data.get('contact_or_email', 'N/A'),
            "test_date": soil_data['Test_Timestamp'],
            "location_name": soil_data['Location_Name'],
            "lat_lon": f"{soil_data['Latitude']:.4f}, {soil_data['Longitude']:.4f}",
            "n_ppm": soil_data['Nitrogen_ppm'],
            "p_ppm": soil_data['Phosphorus_ppm'],
            "k_ppm": soil_data['Potassium_ppm'],
            "ph_value": soil_data['pH_value'],
            "ec_value": soil_data['EC_mS_cm'],
            "crop_detected": soil_data['Crop_Detected'],
            "crop_health": f"{soil_data['Crop_Health_Index']:.0%}"
        }

        message = Mail(
            from_email=OTP_SENDER_EMAIL,
            to_emails=MOCK_FERTILIZER_SHOP_EMAIL,
            subject=f"NEW LEAD: SPL-AgriSense Soil Report for {soil_data['Location_Name']}",
        )
        
        message.template_id = FERTILIZER_TEMPLATE_ID
        message.dynamic_template_data = dynamic_data
        
        response = sg.send(message)
        
        return response.status_code == 202
        
    except Exception as e:
        print(f"Fertilizer Email Error: {e}")
        return False

# --- OTP/Authentication Functions (MODIFIED to use REAL EMAIL) ---

def send_mock_otp(credential):
    otp = str(random.randint(100000, 999999))
    st.session_state['otp_code'] = otp
    
    if send_otp_email(credential, otp):
        st.success(f"✅ OTP sent successfully to **{credential}**. Please check your inbox.")
        st.session_state['signup_stage'] = 2
        return True
    else:
        st.error(f"Email failed to send. Check the console for SendGrid errors.")
        st.info(f"DEBUG MOCK: Use OTP **{otp}** to proceed with signup.")  
        st.session_state['signup_stage'] = 2
        return True

def render_login_page():
    # --- Localization applied here ---
    st.title(get_lang_text("login_title").format(project=PROJECT_NAME))
    
    # Language selection on the login page
    lang_options = LANG_DISPLAY_MAP
    st.session_state['current_lang'] = st.selectbox("🌐 Select Language", options=list(lang_options.keys()), format_func=lambda x: lang_options[x])
    
    tab1, tab2 = st.tabs(["🔒 Login", get_lang_text("signup_btn")])
    db = load_db()
    
    with tab1:
        st.subheader("Login to your Account")
        login_credential = st.text_input("Contact Number or Email", key="login_cred")
        login_password = st.text_input("Password", type="password", key="login_pass")
        if st.button(get_lang_text("login_btn"), use_container_width=True):
            user_id, user_data = check_user_by_credential(db, login_credential)
            if user_id and login_password == user_data['password']:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_id
                st.session_state['user_data'] = user_data
                st.session_state['signup_stage'] = 1
                st.rerun()
            else:
                st.error("Invalid credentials.")
                
    with tab2:
        st.subheader(get_lang_text("signup_btn"))
        if st.session_state.get('signup_stage', 1) == 1:
            with st.form("signup_form_1"):
                st.session_state['signup_name'] = st.text_input("Full Name", value=st.session_state.get('signup_name', ''))
                st.session_state['signup_credential'] = st.text_input("Contact Number or Email (for OTP)", value=st.session_state.get('signup_credential', ''))
                if st.form_submit_button(get_lang_text("send_otp_btn"), use_container_width=True, type="primary"):
                    if not st.session_state['signup_name'] or not st.session_state['signup_credential']:
                        st.error("Please fill in both name and contact/email.")
                    elif check_user_by_credential(db, st.session_state['signup_credential'])[0]:
                        st.error("Account already exists for this contact/email. Please login.")
                    else:
                        send_mock_otp(st.session_state['signup_credential'])
                        st.rerun()
        elif st.session_state.get('signup_stage', 2) == 2:
            st.info(f"OTP sent to **{st.session_state['signup_credential']}**.")
            with st.form("signup_form_2"):
                user_otp = st.text_input("Enter 6-Digit OTP", max_chars=6)
                new_password = st.text_input("Set a Password", type="password")
                if st.form_submit_button(get_lang_text("verify_btn"), use_container_width=True, type="primary"):
                    if user_otp != st.session_state['otp_code']:
                        st.error("❌ Invalid OTP. Please check the code and try again.")
                    elif not new_password:
                        st.error("Please set a password.")
                    else:
                        add_new_user(db, st.session_state['signup_name'], st.session_state['signup_credential'], new_password)
                        st.session_state['signup_stage'] = 3
                        st.balloons()
                        st.rerun()
        elif st.session_state.get('signup_stage', 3) == 3:
            st.success(f"🎉 Account created successfully for **{st.session_state['signup_name']}**!")
            st.write("You can now log in using your contact/email and your new password.")
            if st.button(get_lang_text("login_btn")):
                st.session_state['signup_stage'] = 1
                st.rerun()

# --- CHATBOT UI FUNCTION ---

def render_clarification_chat(test, db):
    """Renders the chat interface for a specific soil test."""
    
    chat_key = f"chat_history_{test['Test_ID']}"
    
    if chat_key not in st.session_state:
        # Localized initial message
        st.session_state[chat_key] = []
        initial_msg = "Hello! I am your AI Agronomist. Ask me any question about your soil or crop based on this test data."
        st.session_state[chat_key].append({"role": "assistant", "content": initial_msg})

    st.subheader(get_lang_text("ask_chat"))
    
    for message in st.session_state[chat_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about this test..."):
        
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        weather_df_today = fetch_weather(test['Latitude'], test['Longitude'], datetime.date.today())
        system_instruction, context_data = build_clarification_prompt(test, weather_df_today, prompt)

        with st.chat_message("assistant"):
            with st.spinner("AI Agronomist is thinking..."):
                chain = build_llm_chain()
                
                if chain is None:
                    response = "Sorry, the LLM service is currently unavailable. Please check the API keys."
                else:
                    # Construct the full prompt including context and user message
                    full_prompt = f"{system_instruction}\n\nCONTEXT:\n{context_data}\n\nUSER QUESTION: {prompt}"
                    
                    try:
                        # 1. Get English response from LLM
                        english_response = chain.run(context=full_prompt)
                        
                        # 2. Translate response based on selected language
                        current_lang = st.session_state['current_lang']
                        response = translate_text(english_response, current_lang)

                    except Exception as e:
                        response = f"LLM Error during query execution. Please try again. ({e})"
                
                st.markdown(response)

        st.session_state[chat_key].append({"role": "assistant", "content": response})

# --- Shared Components (Localization applied here) ---

def render_soil_test_box(test, db):
    timestamp = test['Test_Timestamp']
    location = test['Location_Name']
    user_data = st.session_state['user_data']  
    
    with st.container(border=True):
        col_header, col_delete = st.columns([5, 1])
        # Localized header text
        header_text = get_lang_text("soil_box_header").format(timestamp=timestamp, location=location)
        col_header.markdown(f"**{header_text}**")
        
        if col_delete.button(get_lang_text("delete_btn"), key=f"del_btn_{test['Test_ID']}", type="secondary", use_container_width=True, help="Removes this specific test record."):
            db['soil_tests'].remove(test)
            save_db(db)
            st.success(get_lang_text("delete_success"))
            st.rerun()

        col_data, col_geo_weather = st.columns([3, 2])
        
        with col_data:
            st.subheader(get_lang_text("data_header"))
            soil_nutrients = {
                'Nutrient': ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 'pH Value', 'EC (mS/cm)'],
                'Value': [test['Nitrogen_ppm'], test['Phosphorus_ppm'], test['Potassium_ppm'], test['pH_value'], test['EC_mS_cm']],
                'Unit': ['ppm', 'ppm', 'ppm', '-', 'mS/cm']
            }
            st.dataframe(pd.DataFrame(soil_nutrients).set_index('Nutrient'), use_container_width=True, hide_index=False)
            st.markdown("---")
            col_c1, col_c2 = st.columns(2)
            col_c1.metric("Current Crop (YOLO)", test['Crop_Detected'])
            # Note: Metric labels are static text, so they use get_lang_text
            col_c2.metric(get_lang_text("crop_health_index"), f"{test['Crop_Health_Index']:.0%}")

        with col_geo_weather:
            st.subheader(get_lang_text("coords"))
            st.metric(get_lang_text("coords"), f"{test['Latitude']:.4f}° N, {test['Longitude']:.4f}° E")
            
            test_date = datetime.datetime.strptime(timestamp.split(' ')[0], "%Y-%m-%d").date()
            weather_df = fetch_weather(test['Latitude'], test['Longitude'], test_date)

            if not weather_df.empty:
                avg_temp = weather_df['temperature_2m'].mean()
                max_rain = weather_df['rain'].max()
                st.metric(get_lang_text("avg_temp"), f"{avg_temp:.1f}{get_lang_text('temp_unit')}")
                st.metric(get_lang_text("max_rain"), f"{max_rain:.1f} {get_lang_text('rain_unit')}")
                st.caption(f"Weather for {test_date}")
            else:
                st.warning("Weather data unavailable.")
                
        st.markdown("<hr style='border: 1px solid #333;'>", unsafe_allow_html=True)
        st.markdown(f"**{get_lang_text('action_insights')}**", help="Get personalized advice or connect with partners.")
        
        col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
        
        # Localized button labels
        rec_button_label = get_lang_text("ai_agronomist_advice") if test['Crop_Detected'] != "None Detected" else get_lang_text("propose_crop")
        
        # --- LLM Recommendation Button (Dynamic Translation on result) ---
        if col_r1.button(rec_button_label, key=f"rec_btn_{test['Test_ID']}", use_container_width=True, type="primary"):
            with st.spinner('Analyzing 10+ factors using Groq to generate personalized advice...'):
                weather_df_today = fetch_weather(test['Latitude'], test['Longitude'], datetime.date.today())
                
                # 1. Get English response
                english_recommendation = get_recommendation_from_ai(test, weather_df_today)
                
                # 2. Translate the full text
                final_recommendation = translate_text(english_recommendation, st.session_state['current_lang'])
                
                st.session_state[f"recommendation_{test['Test_ID']}"] = final_recommendation
                
        # --- Fertilizer Partner Connect Button ---
        if col_r2.button(get_lang_text("partner_connect"), key=f"notify_btn_{test['Test_ID']}", use_container_width=True):
            if user_data.get('enable_fertilizer_notifications', False):
                 with st.spinner(f"Sending detailed report via email to partner at {MOCK_FERTILIZER_SHOP_EMAIL}..."):
                     if send_fertilizer_email(user_data, test):
                         st.session_state[f"notify_sent_{test['Test_ID']}"] = True
                         st.success(get_lang_text("data_shared").format(email=MOCK_FERTILIZER_SHOP_EMAIL))
                     else:
                         st.error("Failed to send email notification. Check SendGrid key and network.")
            else:
                 st.error("Please enable **Fertilizer Partner Notifications** in your User Profile to use this feature.")

        # --- Chat Clarification Button ---
        if col_r3.button(get_lang_text("ask_chat"), key=f"chat_btn_{test['Test_ID']}", use_container_width=True, type="secondary"):
            st.session_state['active_chat_test_id'] = test['Test_ID']
            st.session_state['show_chat'] = True
            st.rerun()

        # Display Chat Interface if active for this test
        if st.session_state.get('show_chat', False) and st.session_state.get('active_chat_test_id') == test['Test_ID']:
             st.markdown("---")
             render_clarification_chat(test, db)
             if st.button(get_lang_text("close_chat"), key=f"close_chat_btn_{test['Test_ID']}"):
                 st.session_state['show_chat'] = False
                 st.session_state['active_chat_test_id'] = None
                 st.rerun()

        # Persistent status messages
        if f"notify_sent_{test['Test_ID']}" in st.session_state and st.session_state[f"notify_sent_{test['Test_ID']}"]:
            st.caption(f"Report sent to {MOCK_FERTILIZER_SHOP_EMAIL}")

        if f"recommendation_{test['Test_ID']}" in st.session_state:
            st.markdown("---")
            st.info(st.session_state[f"recommendation_{test['Test_ID']}"])


# --- New Function to Handle Data Simulation and Page Update ---

def handle_new_test_simulation(user_data, db):
    """Simulates a new soil test, saves it, and sends a notification."""
    user_tests = [test for test in db['soil_tests'] if test['User_Contact_or_Email'] == user_data['contact_or_email']]
    # Use the location of the latest test or a default if no tests exist
    location = user_tests[-1]['Location_Name'] if user_tests else "Ludhiana, India"
    
    # 1. Simulate the new data using the consolidated functions
    new_test_data = simulate_new_soil_test(
        user_data['contact_or_email'],
        user_data['name'],
        location
    )
    
    # 2. Inject and save to database
    db['soil_tests'].append(new_test_data)
    save_db(db)
    
    # 3. Show a toast notification
    st.toast(
        f"🔔 **New Soil Test Results!** Field at {new_test_data['Location_Name']} tested: N-{new_test_data['Nitrogen_ppm']}ppm. Check the dashboard for guidance!",
        icon="📱"
    )

# --- Theme Toggle Function ---

def render_theme_button():
    """Renders a button to toggle a custom primary color and background theme."""
    st.sidebar.markdown("---")
    st.sidebar.caption("🎨 **Website Appearance Toggle**")

    # Get the current theme to determine the next state
    current_theme_name = st.session_state.get('custom_theme_primary', THEME_PALETTES['AgriSense Dark'])['name']
    
    if current_theme_name == 'AgriSense Dark':
        button_label = '☀️ Switch to Light Theme (Blue)'
        next_theme_key = 'AgriSense Light'
    else:
        button_label = '🌙 Switch to Dark Theme (Green)'
        next_theme_key = 'AgriSense Dark'

    if st.sidebar.button(button_label, key="theme_toggle_btn", use_container_width=True, help="Toggles the app's custom theme."):
        # Update session state with the new theme palette
        st.session_state['custom_theme_primary'] = THEME_PALETTES[next_theme_key]
        st.rerun()

# --- Main Page Rendering ---

def render_main_dashboard():
    """Renders the main dashboard using sidebar navigation."""
    db = load_db()
    
    # 1. Initialize theme state and inject CSS
    if 'custom_theme_primary' not in st.session_state:
        st.session_state['custom_theme_primary'] = THEME_PALETTES['AgriSense Dark']
        
    inject_custom_css(st.session_state['custom_theme_primary'])
    # ------------------------------------
    
    st.session_state['user_data'] = db['users'].get(st.session_state['user_id'], {})
    user_data = st.session_state['user_data']
    user_name = user_data.get('name', 'Farmer')
    
    ensure_mock_data_exists(db, user_data['contact_or_email'], user_name)
    
    # Language Options Dictionary for Sidebar Selector Display (using the global map)
    lang_options = LANG_DISPLAY_MAP

    # --- Sidebar: Language Selector (Top) ---
    st.session_state['current_lang'] = st.sidebar.selectbox(
        "🌐 Select Language", 
        options=list(lang_options.keys()), 
        format_func=lambda x: lang_options[x]
    )

    # --- Sidebar: Navigation Selector ---
    st.sidebar.markdown(f"## **👋 Hello, {user_name}**")
    
    page = st.sidebar.radio(
        "Navigation",
        [get_lang_text("nav_home"), get_lang_text("nav_soil_results"), get_lang_text("nav_weather"), get_lang_text("nav_profile"), get_lang_text("nav_developer")],
        index=0
    )
    st.sidebar.markdown("---")
    
    # --- Sidebar: Logout Button (Bottom) ---
    if st.sidebar.button(get_lang_text("logout_btn"), type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- THEME BUTTON CALL ---
    render_theme_button()
    # -------------------------

    # --- Main Content Renderer (Routing must use the localized page name) ---
    if page == get_lang_text("nav_home"):
        render_welcome_page(user_name)
    elif page == get_lang_text("nav_soil_results"):
        render_soil_test_results(user_data, db)
    elif page == get_lang_text("nav_weather"):
        render_detailed_weather_forecast(user_data, db)
    elif page == get_lang_text("nav_profile"):
        render_user_profile(user_data, db)
    elif page == get_lang_text("nav_developer"):
        render_developer_details()

def render_welcome_page(user_name):
    st.title(get_lang_text("welcome_greeting").format(name=user_name, project=PROJECT_NAME))
    st.subheader(get_lang_text("welcome_subtitle"))
    st.caption(get_lang_text("developed_by"))
    st.markdown("---")
    
    db = load_db()
    user_data = st.session_state['user_data']

    # --- UPDATED: ADDED 'RUN' BUTTON ---
    if st.button("🔄 Simulate New Field Test / Get Latest Data", use_container_width=True, type="primary"):
        handle_new_test_simulation(user_data, db)
        st.rerun()
    # ------------------------------------
    
    st.markdown("---")
    
    st.markdown(translate_text(
    """
    **Hope you are having a great time in farming!** 🌾
    We know that farming is hard work, which is why we built **SPL-AgriSense**—your personal digital assistant for maximizing yield and profit. Our platform analyzes your field's soil composition, local weather, and crop health to provide specific, data-driven recommendations.
    
    * **Check your latest soil reports** to see nutrient levels and get **AI Agronomist Advice**.
    * **Plan your week** with the **Detailed Weather Forecast**.
    
    Let's make this your most profitable season yet! Click on **Soil Test Results** to start analyzing your field data now.
    """, st.session_state['current_lang']))

    st.markdown("---")
    
    user_tests = [test for test in db['soil_tests'] if test['User_Contact_or_Email'] == user_data['contact_or_email']]
    latest_test = sorted(user_tests, key=lambda x: x['Test_Timestamp'], reverse=True)[0] if user_tests else None
    
    if latest_test:
        st.subheader("Latest Field Snapshot")
        col1, col2, col3 = st.columns(3)
        col1.metric("Last Tested", latest_test['Test_Timestamp'].split(' ')[0])
        col2.metric("N-P-K Ratio (ppm)", f"{latest_test['Nitrogen_ppm']}:{latest_test['Phosphorus_ppm']}:{latest_test['Potassium_ppm']}")
        col3.metric("Current Crop", latest_test['Crop_Detected'])
    else:
        st.info(get_lang_text("no_tests"))

def render_user_profile(user_data, db):
    st.header(get_lang_text("nav_profile"))
    st.info(f"**User ID:** {user_data.get('user_id', 'N/A')}")
    
    col_p1, col_p2 = st.columns(2)
    col_p1.metric("Full Name", user_data.get('name', 'N/A'))
    col_p2.metric("Contact / Email", user_data.get('contact_or_email', 'N/A'))
    
    st.markdown("---")
    st.subheader(get_lang_text("subs_notifs"))
    
    current_status = user_data.get('enable_fertilizer_notifications', False)
    
    new_status = st.checkbox(
        get_lang_text("enable_notifs"),
        value=current_status,
        help="Allow your latest field data to be shared with our network of local fertilizer shops for personalized outreach."
    )
    
    if new_status != current_status:
        user_data['enable_fertilizer_notifications'] = new_status
        db['users'][st.session_state['user_id']] = user_data
        save_db(db)
        status_text = "ENABLED" if new_status else "DISABLED"
        st.success(get_lang_text("confirm_notif_enable").format(status=status_text))
        st.session_state['user_data'] = user_data

def render_soil_test_results(user_data, db):
    st.header(get_lang_text("nav_soil_results"))
    st.markdown(get_lang_text("soil_intro").format(project=PROJECT_NAME))
    
    user_tests = [test for test in db['soil_tests'] if test['User_Contact_or_Email'] == user_data['contact_or_email']]
    
    if not user_tests:
        st.info(get_lang_text("no_tests"))
        return
        
    for test in sorted(user_tests, key=lambda x: x['Test_Timestamp'], reverse=True):
        render_soil_test_box(test, db)
        st.markdown("---")

def render_detailed_weather_forecast(user_data, db):
    st.header(get_lang_text("nav_weather"))
    
    user_tests = [test for test in db['soil_tests'] if test['User_Contact_or_Email'] == user_data['contact_or_email']]
    latest_test = sorted(user_tests, key=lambda x: x['Test_Timestamp'], reverse=True)[0] if user_tests else None
    default_loc = latest_test['Location_Name'] if latest_test else "Delhi, India"
    
    col_w1, col_w2 = st.columns(2)
    weather_place = col_w1.text_input(get_lang_text("location_input"), default_loc, key="weather_place_input")
    weather_date = col_w2.date_input(get_lang_text("date_input"), datetime.date.today(), key="weather_date_input")
    
    if st.button(get_lang_text("fetch_btn"), use_container_width=True, type="primary"):
        
        lat_w, lon_w = get_lat_lon(weather_place)
        
        if lat_w is None or lon_w is None:
            st.error("Could not find precise coordinates for this location. Please check the spelling.")
        else:
            st.success(f"Showing 24-hour hourly forecast for: **{weather_place}** ({lat_w:.4f}, {lon_w:.4f}) on **{weather_date}**")
            
            with st.spinner("Fetching meteorological data..."):
                weather_df = fetch_weather(lat_w, lon_w, weather_date)
            
            if not weather_df.empty:
                st.subheader("Hourly Weather Trends")
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    st.markdown("<div style='text-align: center; font-weight: bold;'>Temperature (°C)</div>", unsafe_allow_html=True)
                    st.line_chart(weather_df['temperature_2m'].rename("Temperature (°C)"), height=300)
                    
                with chart_col2:
                    st.markdown("<div style='text-align: center; font-weight: bold;'>Rainfall (mm)</div>", unsafe_allow_html=True)
                    st.line_chart(weather_df['rain'].rename("Rainfall (mm)"), height=300)
                    
                st.markdown("---")
                st.subheader("Raw Hourly Data")
                st.dataframe(weather_df.reset_index().rename(columns={'index': 'Time'}), use_container_width=True)
            else:
                st.warning("Weather data could not be loaded for the selected date and location.")

def render_developer_details():
    st.header(get_lang_text("nav_developer"))
    st.markdown("---")
    col_text, col_image = st.columns([2, 1])
    with col_text:
        st.subheader("Academic Guidance & Course Context")
        st.markdown(f"""
        The **{PROJECT_NAME}** platform was developed as a core project for the **SPL361 - Information & Communication Technologies and Society** course. 
        Our goal was to address a challenge directly related to the **UN Sustainable Development Goals (SDG)**, specifically aiming at **Goal 2: Zero Hunger** and **Goal 17: Partnerships for the Goals**. By leveraging AI and IoT data to optimize resource use and boost agricultural yield in India, we aim to contribute to sustainable farming and farmer welfare.
        """)
    with col_image:
        try:
            st.image(PROF_IMAGE_PATH, caption="Prof. Rathin Biswas", use_column_width='auto')
        except:
            st.warning(f"Image not found at: {PROF_IMAGE_PATH}")
        st.markdown(f"""
        ### Prof. Rathin Biswas
        **Faculty, IIT Delhi (SPP)**
        [Faculty Website Link](https://spp.iitd.ac.in/faculty-profile/12)
        """)
    st.markdown("---")
    st.subheader("Core Development Team")
    st.markdown("The following students contributed to the conceptualization and development of the platform:")
    dev1, dev2, dev3 = st.columns(3)
    with dev1:
        st.markdown("**Shashank**")
        try:
            st.image(SHASHANK_IMAGE_PATH, caption="Project Lead & Core Dev", use_column_width='auto')
        except:
            st.warning("Shashank Image Placeholder")
        st.markdown("""
        **Role:** Project Lead, Backend Logic, AI Integration (LLM Chain)
        **Email:** shashank_dev@iitd.ac.in
        """)
    with dev2:
        st.markdown("**Raju**")
        try:
            st.image(RAJU_IMAGE_PATH, caption="Data & Simulation Expert", use_column_width='auto')
        except:
            st.warning("Raju Image Placeholder")
        st.markdown("""
        **Role:** Data Simulation, Weather API Handler, Authentication Flow
        **Email:** raju_agri@iitd.ac.in
        """)
    with dev3:
        st.markdown("**Gaurav**")
        try:
            st.image(GAURAV_IMAGE_PATH, caption="Frontend & UX Designer", use_column_width='auto')
        except:
            st.warning("Gaurav Image Placeholder")
        st.markdown("""
        **Role:** Streamlit Dashboard Design, UI/UX Implementation, Mock Data Handling
        **Email:** gaurav_ux@iitd.ac.in
        """)

# --- Application Flow ---

def main():
    
    if st.session_state.get('logged_in', False):
        # Only attempt to install models when logged in and before rendering
        install_argos_models()  
        render_main_dashboard()
    else:
        render_login_page()

if __name__ == "__main__":
    if 'current_lang' not in st.session_state:
        st.session_state['current_lang'] = 'en'
        
    main()
