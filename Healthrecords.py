import streamlit as st
import pandas as pd
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import uuid
import matplotlib.pyplot as plt
import altair as alt
import base64
import io
from PIL import Image
import torch
from transformers import BertTokenizer, BertForSequenceClassification, GPT2Tokenizer, GPT2LMHeadModel

# Set page configuration
st.set_page_config(
    page_title="Track My Health",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create database directory
os.makedirs("data", exist_ok=True)
DB_FILE = "data/trackmyhealth.db"

# Custom CSS with Apollo Hospitals-Inspired Styling
def local_css():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600&family=Lato:wght@400;500&display=swap" rel="stylesheet">
    <style>
    .main { background-color: #FFFFFF; color: #28A745; }
    h1, h2, h3 { font-family: 'Poppins', sans-serif; color: #28A745; letter-spacing: 1px; }
    p, label, div.stTextInput > div > div > input, div.stSelectbox > div > div > select { font-family: 'Lato', sans-serif; }
    .hero-section { background: linear-gradient(135deg, #28A745 0%, #FF69B4 100%); padding: 40px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px; animation: fadeIn 1s ease-in; }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    .card { border-radius: 15px; padding: 20px; background-color: #F8F9FA; box-shadow: 0 6px 12px rgba(40, 167, 69, 0.1); margin-bottom: 20px; transition: transform 0.3s ease; animation: fadeIn 1.5s ease-in; }
    .card:hover { transform: translateY(-5px); }
    .patient-card { background-color: #FFFFFF; border-left: 5px solid #28A745; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); margin-bottom: 15px; }
    .success-box { background-color: #D4EDDA; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28A745; }
    .warning-box { background-color: #FFF3CD; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #FFC107; }
    .info-box { background-color: #FFE6F0; color: #FF69B4; padding: 15px; border-radius: 8px; border-left: 5px solid #FF69B4; animation: fadeIn 2s ease-in; }
    .stButton > button { background: linear-gradient(90deg, #28A745 0%, #FF69B4 100%); color: white; border-radius: 8px; padding: 12px 24px; font-weight: 500; border: none; transition: all 0.3s ease; font-family: 'Lato', sans-serif; }
    .stButton > button:hover { background: linear-gradient(90deg, #218838 0%, #FF1493 100%); box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3); }
    .delete-btn { background: #DC3545 !important; }
    .delete-btn:hover { background: #C82333 !important; }
    .css-1d391kg { background: linear-gradient(135deg, #28A745 0%, #FF69B4 100%); }
    .css-1d391kg .sidebar-content { background: transparent; }
    div.stButton > button:first-child { background: linear-gradient(90deg, #28A745 0%, #FF69B4 100%); color: white; border-radius: 8px; padding: 12px 24px; font-weight: 500; border: none; transition: all 0.3s ease; }
    div.stButton > button:hover { background: linear-gradient(90deg, #218838 0%, #FF1493 100%); box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3); }
    .st-emotion-cache-16idsys p { font-size: 16px; font-family: 'Lato', sans-serif; }
    .st-emotion-cache-1y4p8pa { padding: 15px; border-radius: 0 0 15px 15px; border: 1px solid #E0E0E0; border-top: none; }
    .st-emotion-cache-1y4p8pa > div:first-child { border-radius: 15px 15px 0 0; overflow: hidden; }
    .dataframe { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
    .dataframe th { background: linear-gradient(90deg, #28A745 0%, #FF69B4 100%); color: white; padding: 12px; text-align: left; font-family: 'Lato', sans-serif; }
    .dataframe td { padding: 12px; border-bottom: 1px solid #E0E0E0; font-family: 'Lato', sans-serif; }
    .dataframe tr:nth-child(even) { background-color: #F8F9FA; }
    .dataframe tr:hover { background-color: #E9ECEF; }
    .header-container { display: flex; align-items: center; padding: 1.5rem; background-color: #FFFFFF; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 6px 12px rgba(40, 167, 69, 0.1); }
    .header-logo { width: 60px; margin-right: 15px; }
    .header-title { font-size: 2.5rem; font-weight: 700; color: #28A745; margin: 0; }
    .metric-card { background-color: #FFFFFF; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); text-align: center; animation: fadeIn 1.5s ease-in; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #28A745; margin: 10px 0; }
    .metric-label { font-size: 1rem; color: #6C757D; font-family: 'Lato', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Apply CSS
local_css()

# Database initialization
def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users table (for patients, hospitals, admin)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('patient', 'hospital', 'admin')),
        name TEXT,
        email TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        user_id TEXT UNIQUE REFERENCES users(id),
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth DATE,
        gender TEXT,
        profile_image TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Hospitals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hospitals (
        id TEXT PRIMARY KEY,
        user_id TEXT UNIQUE REFERENCES users(id),
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT,
        status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Contact information
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contact_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        phone TEXT,
        email TEXT,
        address TEXT,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Medical history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        hospital_id TEXT REFERENCES hospitals(id),
        blood_type TEXT,
        allergies TEXT,
        chronic_conditions TEXT,
        surgeries TEXT,
        family_history TEXT,
        uploaded_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Vital signs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vital_signs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        hospital_id TEXT REFERENCES hospitals(id),
        recorded_date TIMESTAMP,
        temperature REAL,
        blood_pressure TEXT,
        pulse INTEGER,
        respiratory_rate INTEGER,
        oxygen_saturation REAL,
        weight REAL,
        height REAL,
        bmi REAL,
        recorded_by TEXT,
        notes TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Appointments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        hospital_id TEXT REFERENCES hospitals(id),
        appointment_date TIMESTAMP,
        duration INTEGER,
        status TEXT,
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Uploaded reports
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        hospital_id TEXT REFERENCES hospitals(id),
        file_name TEXT,
        file_content BLOB,
        upload_date TIMESTAMP,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Insert demo data
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        current_time = datetime.now().isoformat()
        # Demo admin
        admin_user_id = f"USR_ADM_{uuid.uuid4()}"
        cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (admin_user_id, "admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin", "Admin User", "admin@trackmyhealth.com", current_time, current_time))
        
        # Demo patient
        patient_user_id = f"USR_PAT_{uuid.uuid4()}"
        patient_id = f"PAT_{uuid.uuid4()[:8]}"
        cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_user_id, "patient1", hashlib.sha256("patient123".encode()).hexdigest(), "patient", "John Doe", "john@example.com", current_time, current_time))
        cursor.execute('INSERT INTO patients (id, user_id, first_name, last_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, patient_user_id, "John", "Doe", "1980-05-15", "Male", current_time, current_time))
        cursor.execute('INSERT INTO contact_info (patient_id, phone, email, address, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (patient_id, "5551234567", "john.doe@example.com", "123 Main St", current_time, current_time))
        cursor.execute('INSERT INTO medical_history (patient_id, hospital_id, blood_type, allergies, chronic_conditions, uploaded_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (patient_id, None, "A+", "Pollen", "Hypertension", current_time, current_time))
        
        # Demo hospital
        hospital_user_id = f"USR_HOS_{uuid.uuid4()}"
        hospital_id = f"HOS_{uuid.uuid4()[:8]}"
        cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (hospital_user_id, "hospital1", hashlib.sha256("hospital123".encode()).hexdigest(), "hospital", "City Hospital", "contact@cityhospital.com", current_time, current_time))
        cursor.execute('INSERT INTO hospitals (id, user_id, name, address, phone, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (hospital_id, hospital_user_id, "City Hospital", "456 Health Ave", "5559876543", "approved", current_time, current_time))
        
        # Demo appointment
        cursor.execute('INSERT INTO appointments (patient_id, hospital_id, appointment_date, duration, status, reason, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, hospital_id, (datetime.now() + timedelta(days=1)).isoformat(), 30, "Scheduled", "Check-up", current_time, current_time))
    
    conn.commit()
    conn.close()

# Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, role, name FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == hash_password(password):
        return {'user_id': user[0], 'role': user[2], 'name': user[3]}
    return None

def update_last_login(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (current_time, user_id))
    conn.commit()
    conn.close()

# New Logo
def get_trackmyhealth_logo():
    logo_svg = '''
    <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
        <circle cx="30" cy="30" r="30" fill="#28A745"/>
        <path d="M15 30 Q30 10 45 30 Q30 50 15 30 Z" fill="#FF69B4" stroke="#FFFFFF" stroke-width="2"/>
        <path d="M25 20 V40 M35 20 V40" stroke="#FFFFFF" stroke-width="2"/>
        <path d="M20 30 H40" stroke="#FFFFFF" stroke-width="2" stroke-dasharray="5"/>
    </svg>
    '''
    return "data:image/svg+xml;base64," + base64.b64encode(logo_svg.encode()).decode()

# AI Models for Suggestions
@st.cache_resource
def load_bert_model():
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
    return tokenizer, model

@st.cache_resource
def load_gpt2_model():
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    return tokenizer, model

def bert_treatment_suggestion(history):
    tokenizer, model = load_bert_model()
    inputs = tokenizer(history, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    prediction = torch.argmax(outputs.logits, dim=1).item()
    if prediction == 1 and "Hypertension" in history:
        return "• **Diagnosis:** Hypertension detected.<br>• **Treatment:** Prescribe ACE inhibitors (e.g., Lisinopril 10 mg daily).<br>• **Lifestyle:** Recommend low-sodium diet and regular exercise."
    return "• No critical conditions detected. Continue monitoring."

def gpt2_health_tips(history):
    tokenizer, model = load_gpt2_model()
    prompt = f"Health tips for a patient with {history}:"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True)
    outputs = model.generate(**inputs, max_length=100, num_return_sequences=1)
    tip = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return tip.replace(prompt, "").strip()

# General Health Queries Section
def general_health_queries():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("General Health Queries")
    query = st.text_area("Ask a health-related question:")
    if st.button("Submit Query"):
        if query:
            response = gpt2_health_tips(query)
            st.markdown(f"<div class='info-box'>**AI Response:** {response}</div>", unsafe_allow_html=True)
        else:
            st.warning("Please enter a query.")
    st.markdown("</div>", unsafe_allow_html=True)

# Login Page
def login_page():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Track My Health</h1><p>Your trusted partner in centralized health records.</p></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Login")
        role = st.selectbox("Login as", ["Patient", "Hospital", "Admin"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.role = user['role']
                    st.session_state.authenticated = True
                    update_last_login(user['user_id'])
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
            else:
                st.warning("Please enter both username and password.")
        st.markdown("<div class='info-box'>Demo Credentials:<br>Patient: patient1 / patient123<br>Hospital: hospital1 / hospital123<br>Admin: admin / admin123</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("New User? Register Here")
        reg_role = st.selectbox("Register as", ["Patient", "Hospital"])
        if reg_role == "Patient":
            with st.form("patient_register_form"):
                cols = st.columns(2)
                with cols[0]: first_name = st.text_input("First Name*")
                with cols[1]: last_name = st.text_input("Last Name*")
                cols = st.columns(2)
                with cols[0]: gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                with cols[1]: dob = st.date_input("Date of Birth")
                email = st.text_input("Email*")
                phone = st.text_input("Phone Number*")
                submitted = st.form_submit_button("Register")
                if submitted:
                    if first_name and last_name and email and phone:
                        username = f"{first_name.lower()}.{last_name.lower()}"
                        password = "patient123"
                        user_id = f"USR_PAT_{uuid.uuid4()}"
                        patient_id = f"PAT_{uuid.uuid4()[:8]}"
                        password_hash = hash_password(password)
                        current_time = datetime.now().isoformat()
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        try:
                            cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, username, password_hash, "patient", f"{first_name} {last_name}", email, current_time, current_time))
                            cursor.execute('INSERT INTO patients (id, user_id, first_name, last_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, user_id, first_name, last_name, dob.isoformat(), gender, current_time, current_time))
                            cursor.execute('INSERT INTO contact_info (patient_id, phone, email, address, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (patient_id, phone, email, "", current_time, current_time))
                            conn.commit()
                            st.success(f"Registration successful! Username: {username}, Password: {password}")
                        except sqlite3.Error as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()
                    else:
                        st.warning("Please fill all required fields")
        else:
            with st.form("hospital_register_form"):
                hospital_name = st.text_input("Hospital Name*")
                address = st.text_area("Address*")
                phone = st.text_input("Phone Number*")
                email = st.text_input("Email*")
                submitted = st.form_submit_button("Submit for Approval")
                if submitted:
                    if hospital_name and address and phone and email:
                        username = hospital_name.lower().replace(" ", "")
                        password = "hospital123"
                        user_id = f"USR_HOS_{uuid.uuid4()}"
                        hospital_id = f"HOS_{uuid.uuid4()[:8]}"
                        password_hash = hash_password(password)
                        current_time = datetime.now().isoformat()
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        try:
                            cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, username, password_hash, "hospital", hospital_name, email, current_time, current_time))
                            cursor.execute('INSERT INTO hospitals (id, user_id, name, address, phone