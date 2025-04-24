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
                            cursor.execute( 'INSERT INTO hospitals (id, user_id, name, address, phone, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (hospital_id, user_id, "City Hospital", "123 Main St", "555-1234", "approved", current_time, current_time))
                            conn.commit()
                            st.success("Registration submitted for admin approval.")
                        except sqlite3.Error as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()
                    else:
                        st.warning("Please fill all required fields")
        st.markdown("</div>", unsafe_allow_html=True)

# Navigation
def navigation():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="header-container"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1 class="header-title">Track My Health</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: right; padding: 10px;'><b>{st.session_state.user['name']}</b> ({st.session_state.role.capitalize()}) | <a href='#' onclick='window.location.reload()'>Logout</a></div>", unsafe_allow_html=True)
    if st.session_state.role == "patient":
        menu = ["Dashboard", "Appointments", "Medical History", "About"]
    elif st.session_state.role == "hospital":
        menu = ["Dashboard", "Appointments", "Medical History", "Patient Management", "About"]
    else:
        menu = ["Admin Dashboard", "Hospital Approvals", "About"]
    return st.sidebar.selectbox("Menu", menu)

# Admin Dashboard
def admin_dashboard():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Welcome, Admin!</h1><p>Manage hospital registrations and system settings.</p></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a professional admin managing healthcare records for this section?")
    general_health_queries()

# Hospital Approvals (Admin)
def hospital_approvals():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Hospital Registration Approvals</h1></div>', unsafe_allow_html=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, name, address, phone, email, status FROM hospitals WHERE status = 'pending'")
    pending_hospitals = cursor.fetchall()
    if pending_hospitals:
        for hospital in pending_hospitals:
            hospital_id, user_id, name, address, phone, email, status = hospital
            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"**Hospital:** {name}<br>**Address:** {address}<br>**Phone:** {phone}<br>**Email:** {email}<br>**Status:** {status}", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Approve {name}", key=f"approve_{hospital_id}"):
                    cursor.execute("UPDATE hospitals SET status = 'approved' WHERE id = ?", (hospital_id,))
                    conn.commit()
                    st.success(f"{name} approved successfully")
                    st.experimental_rerun()
            with col2:
                if st.button(f"Reject {name}", key=f"reject_{hospital_id}"):
                    cursor.execute("UPDATE hospitals SET status = 'rejected' WHERE id = ?", (hospital_id,))
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.commit()
                    st.success(f"{name} rejected and removed")
                    st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No pending hospital registrations.")
    conn.close()
    general_health_queries()

# Patient Dashboard
def patient_dashboard():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Welcome, {st.session_state.user["name"]}!</h1><p>Manage your health records with ease.</p></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a happy patient managing their health records for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patients WHERE user_id = ?", (st.session_state.user['user_id'],))
    patient_id = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE patient_id = ? AND status = 'Scheduled'", (patient_id,))
    upcoming_appointments = cursor.fetchone()[0]
    conn.close()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Upcoming Appointments</div><div class='metric-value'>{upcoming_appointments}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card'><div class='metric-label'>Health Score</div><div class='metric-value'>85</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>Next Steps: Book an appointment or view your medical history.</div>", unsafe_allow_html=True)
    # AI Health Tips
    cursor.execute("SELECT blood_type, allergies, chronic_conditions FROM medical_history WHERE patient_id = ?", (patient_id,))
    health_data = cursor.fetchone()
    if health_data:
        blood_type, allergies, conditions = health_data
        history = f"Blood Type: {blood_type}, Allergies: {allergies}, Conditions: {conditions}"
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.subheader("AI Health Tips")
        tips = gpt2_health_tips(history)
        st.markdown(f"{tips}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    conn.close()
    general_health_queries()

# Hospital Dashboard
def hospital_dashboard():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Welcome, {st.session_state.user["name"]}!</h1><p>Manage your patients and appointments.</p></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a professional doctor in a hospital setting for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hospitals WHERE user_id = ?", (st.session_state.user['user_id'],))
    hospital_id = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE hospital_id = ? AND status = 'Scheduled'", (hospital_id,))
    pending_appointments = cursor.fetchone()[0]
    conn.close()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Pending Appointments</div><div class='metric-value'>{pending_appointments}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card'><div class='metric-label'>Patients Today</div><div class='metric-value'>5</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>Manage appointments or update patient records.</div>", unsafe_allow_html=True)
    general_health_queries()

# Appointments (Patient)
def patient_appointments():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Book an Appointment</h1></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a patient booking an appointment at a hospital for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patients WHERE user_id = ?", (st.session_state.user['user_id'],))
    patient_id = cursor.fetchone()[0]
    cursor.execute("SELECT id, name, address, phone FROM hospitals WHERE status = 'approved'")
    hospitals = cursor.fetchall()
    with st.form("book_appointment_form"):
        hospital = st.selectbox("Select Hospital", [f"{h[1]} ({h[2]})" for h in hospitals], format_func=lambda x: x.split(" (")[0])
        hospital_id = next(h[0] for h in hospitals if f"{h[1]} ({h[2]})" == hospital)
        col1, col2 = st.columns(2)
        with col1: appointment_date = st.date_input("Date", min_value=datetime.now().date())
        with col2: appointment_time = st.time_input("Time", value=datetime.now().time().replace(minute=0, second=0))
        duration = st.slider("Duration (minutes)", 15, 120, 30, 15)
        reason = st.text_input("Reason for Visit")
        submitted = st.form_submit_button("Book Appointment")
        if submitted:
            if appointment_date and reason:
                appointment_datetime = datetime.combine(appointment_date, appointment_time).isoformat()
                current_time = datetime.now().isoformat()
                try:
                    cursor.execute('INSERT INTO appointments (patient_id, hospital_id, appointment_date, duration, status, reason, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, hospital_id, appointment_datetime, duration, "Scheduled", reason, current_time, current_time))
                    conn.commit()
                    st.success(f"Appointment booked with {hospital.split(' (')[0]} on {appointment_date} at {appointment_time}")
                except sqlite3.Error as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please select a date and provide a reason")
    conn.close()
    st.markdown("<h3>Upcoming Appointments</h3>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT a.id, h.name, a.appointment_date, a.duration, a.status, a.reason FROM appointments a JOIN hospitals h ON a.hospital_id = h.id WHERE a.patient_id = ? AND a.appointment_date >= datetime('now') ORDER BY a.appointment_date ASC", (patient_id,))
    appointments = cursor.fetchall()
    if appointments:
        df = pd.DataFrame([{"ID": a[0], "Hospital": a[1], "Date": a[2].split("T")[0], "Time": a[2].split("T")[1][:5], "Duration": f"{a[3]} min", "Status": a[4], "Reason": a[5]} for a in appointments])
        st.dataframe(df)
    else:
        st.info("No upcoming appointments.")
    conn.close()
    general_health_queries()

# Appointments (Hospital)
def hospital_appointments():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Manage Appointments</h1></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a hospital staff managing appointments for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hospitals WHERE user_id = ?", (st.session_state.user['user_id'],))
    hospital_id = cursor.fetchone()[0]
    cursor.execute("SELECT a.id, p.first_name, p.last_name, a.appointment_date, a.duration, a.status, a.reason FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.hospital_id = ? ORDER BY a.appointment_date ASC", (hospital_id,))
    appointments = cursor.fetchall()
    if appointments:
        df = pd.DataFrame([{"ID": a[0], "Patient": f"{a[1]} {a[2]}", "Date": a[3].split("T")[0], "Time": a[3].split("T")[1][:5], "Duration": f"{a[4]} min", "Status": a[5], "Reason": a[6]} for a in appointments])
        st.dataframe(df)
        selected_appt = st.selectbox("Select Appointment", [f"{a[0]} - {a[1]} {a[2]} ({a[3].split('T')[0]})" for a in appointments])
        if selected_appt:
            appt_id = selected_appt.split(" - ")[0]
            cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", ("Completed", appt_id))
            conn.commit()
            st.success(f"Appointment {appt_id} marked as completed")
    else:
        st.info("No appointments scheduled.")
    conn.close()
    general_health_queries()

# Medical History (Patient)
def patient_medical_history():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Your Medical History</h1></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a patient reviewing their medical history for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patients WHERE user_id = ?", (st.session_state.user['user_id'],))
    patient_id = cursor.fetchone()[0]
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    cursor.execute("SELECT blood_type, allergies, chronic_conditions, surgeries, family_history FROM medical_history WHERE patient_id = ?", (patient_id,))
    history = cursor.fetchone()
    if history:
        st.subheader("Medical History")
        blood_type, allergies, conditions, surgeries, family_history = history
        st.markdown(f"**Blood Type:** {blood_type}<br>**Allergies:** {allergies}<br>**Chronic Conditions:** {conditions}<br>**Surgeries:** {surgeries if surgeries else 'None'}<br>**Family History:** {family_history if family_history else 'None'}", unsafe_allow_html=True)
    else:
        st.info("No medical history available.")
    cursor.execute("SELECT recorded_date, temperature, blood_pressure, pulse, oxygen_saturation, weight, bmi FROM vital_signs WHERE patient_id = ? ORDER BY recorded_date DESC", (patient_id,))
    vitals = cursor.fetchall()
    if vitals:
        st.subheader("Vital Signs Trends")
        df = pd.DataFrame([{"Date": v[0].split("T")[0], "Temperature (°F)": v[1], "BP (mmHg)": v[2], "Pulse (bpm)": v[3], "O2 Sat (%)": v[4], "Weight (lbs)": v[5], "BMI": v[6]} for v in vitals])
        st.line_chart(df.set_index("Date")[["Temperature (°F)", "Pulse (bpm)", "O2 Sat (%)"]])
        st.line_chart(df.set_index("Date")[["Weight (lbs)", "BMI"]])
    st.markdown("</div>", unsafe_allow_html=True)
    conn.close()
    general_health_queries()

# Medical History (Hospital)
def hospital_medical_history():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Patient Medical History</h1></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a doctor reviewing a patient's medical history for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hospitals WHERE user_id = ?", (st.session_state.user['user_id'],))
    hospital_id = cursor.fetchone()[0]
    cursor.execute("SELECT p.id, p.first_name, p.last_name FROM patients p JOIN appointments a ON p.id = a.patient_id WHERE a.hospital_id = ? GROUP BY p.id", (hospital_id,))
    patients = cursor.fetchall()
    if patients:
        patient = st.selectbox("Select Patient", [f"{p[1]} {p[2]} ({p[0]})" for p in patients], format_func=lambda x: x.split(" (")[0])
        patient_id = patient.split(" (")[1].rstrip(")")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        # Medical History
        cursor.execute("SELECT blood_type, allergies, chronic_conditions, surgeries, family_history FROM medical_history WHERE patient_id = ? AND hospital_id = ?", (patient_id, hospital_id))
        history = cursor.fetchone()
        if history:
            st.subheader("Medical History")
            blood_type, allergies, conditions, surgeries, family_history = history
            history_text = f"Blood Type: {blood_type}, Allergies: {allergies}, Conditions: {conditions}, Surgeries: {surgeries if surgeries else 'None'}, Family History: {family_history if family_history else 'None'}"
            st.markdown(f"**Blood Type:** {blood_type}<br>**Allergies:** {allergies}<br>**Chronic Conditions:** {conditions}<br>**Surgeries:** {surgeries if surgeries else 'None'}<br>**Family History:** {family_history if family_history else 'None'}", unsafe_allow_html=True)
        # Vital Signs
        cursor.execute("SELECT recorded_date, temperature, blood_pressure, pulse, oxygen_saturation, weight, bmi FROM vital_signs WHERE patient_id = ? AND hospital_id = ? ORDER BY recorded_date DESC", (patient_id, hospital_id))
        vitals = cursor.fetchall()
        if vitals:
            st.subheader("Vital Signs Trends")
            df = pd.DataFrame([{"Date": v[0].split("T")[0], "Temperature (°F)": v[1], "BP (mmHg)": v[2], "Pulse (bpm)": v[3], "O2 Sat (%)": v[4], "Weight (lbs)": v[5], "BMI": v[6]} for v in vitals])
            st.line_chart(df.set_index("Date")[["Temperature (°F)", "Pulse (bpm)", "O2 Sat (%)"]])
            st.line_chart(df.set_index("Date")[["Weight (lbs)", "BMI"]])
        # Reports
        cursor.execute("SELECT file_name, upload_date FROM reports WHERE patient_id = ? AND hospital_id = ?", (patient_id, hospital_id))
        reports = cursor.fetchall()
        if reports:
            st.subheader("Uploaded Reports")
            df = pd.DataFrame([{"File Name": r[0], "Upload Date": r[1].split("T")[0]} for r in reports])
            st.dataframe(df)
        # AI Treatment Suggestions
        st.subheader("AI Treatment Suggestions")
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        suggestion = bert_treatment_suggestion(history_text if history else "No history")
        st.markdown(suggestion, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No patients available.")
    conn.close()
    general_health_queries()

# Upload Patient Details (Hospital)
def hospital_patient_management():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>Patient Management</h1></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a hospital staff adding patient details for this section?")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hospitals WHERE user_id = ?", (st.session_state.user['user_id'],))
    hospital_id = cursor.fetchone()[0]
    with st.form("add_patient_form"):
        cols = st.columns(2)
        with cols[0]: first_name = st.text_input("First Name*")
        with cols[1]: last_name = st.text_input("Last Name*")
        cols = st.columns(2)
        with cols[0]: gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        with cols[1]: dob = st.date_input("Date of Birth")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email")
        address = st.text_area("Address")
        cols = st.columns(3)
        with cols[0]: blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        with cols[1]: allergies = st.text_input("Allergies")
        with cols[2]: conditions = st.text_input("Chronic Conditions")
        submitted = st.form_submit_button("Add Patient")
        if submitted:
            if first_name and last_name:
                patient_id = f"PAT_{uuid.uuid4()[:8]}"
                user_id = f"USR_PAT_{uuid.uuid4()}"
                password_hash = hashlib.sha256("patient123".encode()).hexdigest()
                current_time = datetime.now().isoformat()
                try:
                    cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, f"{first_name.lower()}.{last_name.lower()}", password_hash, "patient", f"{first_name} {last_name}", email, current_time, current_time))
                    cursor.execute('INSERT INTO patients (id, user_id, first_name, last_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, user_id, first_name, last_name, dob.isoformat(), gender, current_time, current_time))
                    cursor.execute('INSERT INTO contact_info (patient_id, phone, email, address, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (patient_id, phone, email, address, current_time, current_time))
                    cursor.execute('INSERT INTO medical_history (patient_id, hospital_id, blood_type, allergies, chronic_conditions, uploaded_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (patient_id, hospital_id, blood_type, allergies, conditions, current_time, current_time))
                    conn.commit()
                    st.success(f"Patient {first_name} {last_name} added with ID: {patient_id}")
                except sqlite3.Error as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("First and last names are required")
    conn.close()
    general_health_queries()

# About Page
def about_page():
    st.markdown(f'<div class="hero-section"><img src="{get_trackmyhealth_logo()}" class="header-logo" /><h1>About Track My Health</h1></div>', unsafe_allow_html=True)
    # AI-Generated Image
    st.markdown("Would you like to generate an image of a healthcare team for the About page?")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    **Track My Health** is a premium centralized electronic health record system designed to simplify healthcare management. We empower patients and hospitals with secure, intelligent tools for better care.

    - **Mission**: To revolutionize healthcare with technology.
    - **Contact**: support@trackmyhealth.com
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    general_health_queries()

# Main App
if __name__ == "__main__":
    initialize_database()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.role = None
    if not st.session_state.authenticated:
        login_page()
    else:
        navigation_option = navigation()
        if navigation_option == "Dashboard":
            if st.session_state.role == "patient":
                patient_dashboard()
            elif st.session_state.role == "hospital":
                hospital_dashboard()
            else:
                admin_dashboard()
        elif navigation_option == "Appointments":
            if st.session_state.role == "patient":
                patient_appointments()
            else:
                hospital_appointments()
        elif navigation_option == "Medical History":
            if st.session_state.role == "hospital":
                hospital_medical_history()
            elif st.session_state.role == "patient":
                patient_medical_history()
            else:
                st.warning("Medical history access is for patients and hospitals only.")
        elif navigation_option == "Patient Management" and st.session_state.role == "hospital":
            hospital_patient_management()
        elif navigation_option == "Hospital Approvals" and st.session_state.role == "admin":
            hospital_approvals()
        elif navigation_option == "About":
            about_page()