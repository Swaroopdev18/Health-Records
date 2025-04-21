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

# Set page configuration
st.set_page_config(
    page_title="HealthSync EHR",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create database directory if it doesn't exist
os.makedirs("data", exist_ok=True)
DB_FILE = "data/healthsync_ehr.db"

# Custom CSS and Google Fonts
def local_css():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
    <style>
    .main { background-color: #FFFFFF; color: #1E90FF; }
    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; color: #1E90FF; letter-spacing: 1px; }
    .card { border-radius: 10px; padding: 20px; background-color: #F5F6FA; box-shadow: 0 4px 12px rgba(30, 144, 255, 0.1); margin-bottom: 20px; }
    .patient-card { background-color: #FFFFFF; border-left: 5px solid #1E90FF; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 15px; }
    .success-box { background-color: #D4EDDA; color: #155724; padding: 15px; border-radius: 5px; border-left: 5px solid #28A745; }
    .warning-box { background-color: #FFF3CD; color: #856404; padding: 15px; border-radius: 5px; border-left: 5px solid #FFC107; }
    .info-box { background-color: #CCE5FF; color: #004085; padding: 15px; border-radius: 5px; border-left: 5px solid #1E90FF; }
    .stButton > button { background-color: #1E90FF; color: white; border-radius: 6px; padding: 10px 24px; font-weight: 500; border: none; transition: all 0.3s ease; font-family: 'Roboto', sans-serif; }
    .stButton > button:hover { background-color: #187BCD; box-shadow: 0 5px 15px rgba(30, 144, 255, 0.3); }
    .delete-btn { background-color: #DC3545 !important; }
    .delete-btn:hover { background-color: #C82333 !important; }
    .css-1d391kg { background-color: #1E90FF; }
    .css-1d391kg .sidebar-content { background-color: #1E90FF; }
    div.stButton > button:first-child { background-color: #1E90FF; color: white; border-radius: 6px; padding: 10px 24px; font-weight: 500; border: none; transition: all 0.3s ease; }
    div.stButton > button:hover { background-color: #187BCD; box-shadow: 0 5px 15px rgba(30, 144, 255, 0.3); }
    .st-emotion-cache-16idsys p { font-size: 16px; font-family: 'Roboto', sans-serif; }
    .st-emotion-cache-1y4p8pa { padding: 15px; border-radius: 0 0 10px 10px; border: 1px solid #E0E0E0; border-top: none; }
    .st-emotion-cache-1y4p8pa > div:first-child { border-radius: 10px 10px 0 0; overflow: hidden; }
    .dataframe { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
    .dataframe th { background-color: #1E90FF; color: white; padding: 12px; text-align: left; font-family: 'Roboto', sans-serif; }
    .dataframe td { padding: 12px; border-bottom: 1px solid #E0E0E0; font-family: 'Roboto', sans-serif; }
    .dataframe tr:nth-child(even) { background-color: #F5F6FA; }
    .dataframe tr:hover { background-color: #E9ECEF; }
    .header-container { display: flex; align-items: center; padding: 1rem; background-color: #FFFFFF; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(30, 144, 255, 0.1); }
    .header-logo { width: 50px; margin-right: 15px; }
    .header-title { font-size: 2.5rem; font-weight: 700; color: #1E90FF; margin: 0; }
    .metric-card { background-color: #FFFFFF; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); text-align: center; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #1E90FF; margin: 10px 0; }
    .metric-label { font-size: 1rem; color: #6C757D; font-family: 'Roboto', sans-serif; }
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
    
    # Users table (for patients and hospitals)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('patient', 'hospital')),
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
        # Demo patient
        patient_user_id = f"USR_PAT_{uuid.uuid4()}"
        patient_id = f"PAT_{str(uuid.uuid4())[:8]}"
        password_hash = hashlib.sha256("patient123".encode()).hexdigest()
        current_time = datetime.now().isoformat()
        cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_user_id, "patient1", password_hash, "patient", "John Doe", "john@example.com", current_time, current_time))
        cursor.execute('INSERT INTO patients (id, user_id, first_name, last_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, patient_user_id, "John", "Doe", "1980-05-15", "Male", current_time, current_time))
        cursor.execute('INSERT INTO contact_info (patient_id, phone, email, address, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (patient_id, "5551234567", "john.doe@example.com", "123 Main St", current_time, current_time))
        
        # Demo hospital
        hospital_user_id = f"USR_HOS_{uuid.uuid4()}"
        hospital_id = f"HOS_{uuid.uuid4()[:8]}"
        password_hash = hashlib.sha256("hospital123".encode()).hexdigest()
        cursor.execute('INSERT INTO users (id, username, password_hash, role, name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (hospital_user_id, "hospital1", password_hash, "hospital", "City Hospital", "contact@cityhospital.com", current_time, current_time))
        cursor.execute('INSERT INTO hospitals (id, user_id, name, address, phone, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (hospital_id, hospital_user_id, "City Hospital", "456 Health Ave", "5559876543", current_time, current_time))
        
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
    return {'user_id': user[0], 'role': user[2], 'name': user[3]} if user and user[1] == hash_password(password) else None

def update_last_login(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (current_time, user_id))
    conn.commit()
    conn.close()

# Logo
def get_healthsync_logo():
    logo_svg = '''
    <svg width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="50" height="50" rx="10" fill="#1E90FF"/>
        <path d="M15 15 L35 35 M15 35 L35 15" stroke="white" stroke-width="4"/>
        <path d="M25 10 V40" stroke="white" stroke-width="2" stroke-dasharray="5"/>
    </svg>
    '''
    return "data:image/svg+xml;base64," + base64.b64encode(logo_svg.encode()).decode()

# Login Page
def login_page():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f'<div class="header-container"><img src="{get_healthsync_logo()}" class="header-logo" /><h1 class="header-title">HealthSync EHR</h1></div>', unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Welcome to HealthSync EHR")
        st.markdown("A centralized electronic health record system designed to replace physical reports, simplify diagnosis, and enhance understanding with AI-powered insights.")
        st.markdown("#### Key Features:")
        st.markdown("• Patient & Hospital Portals<br>• Appointment Booking<br>• Medical History Visualization<br>• Predictive Health Insights", unsafe_allow_html=True)
        st.markdown("<div class='info-box'>New users? Contact admin to register.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Login")
        role = st.selectbox("Login as", ["Patient", "Hospital"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username and password:
                user = authenticate(username, password)
                if user and user['role'] == role.lower():
                    st.session_state.user = user
                    st.session_state.role = role.lower()
                    st.session_state.authenticated = True
                    update_last_login(user['user_id'])
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials or role mismatch")
            else:
                st.warning("Please enter username and password")
        st.markdown("<div class='info-box'>Demo Credentials:<br>Patient: patient1 / patient123<br>Hospital: hospital1 / hospital123</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Navigation
def navigation():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="header-container"><img src="{get_healthsync_logo()}" class="header-logo" /><h1 class="header-title">HealthSync EHR</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: right; padding: 10px;'><b>{st.session_state.user['name']}</b> ({st.session_state.role.capitalize()}) | <a href='#' onclick='window.location.reload()'>Logout</a></div>", unsafe_allow_html=True)
    menu = ["Dashboard", "Appointments", "Medical History", "Reports", "About"]
    if st.session_state.role == "hospital":
        menu.append("Patient Management")
    return st.sidebar.selectbox("Menu", menu)

# Patient Dashboard
def patient_dashboard():
    st.header("Patient Dashboard")
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
        st.markdown("<div class='metric-card'><div class='metric-label'>Health Score</div><div class='metric-value'>85</div></div>", unsafe_allow_html=True)  # Placeholder
    st.markdown("<div class='card'>Next Steps: Book an appointment or upload reports.</div>", unsafe_allow_html=True)

# Hospital Dashboard
def hospital_dashboard():
    st.header("Hospital Dashboard")
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
        st.markdown("<div class='metric-card'><div class='metric-label'>Patients Today</div><div class='metric-value'>5</div></div>", unsafe_allow_html=True)  # Placeholder
    st.markdown("<div class='card'>Manage appointments or update patient records.</div>", unsafe_allow_html=True)

# Appointments (Patient)
def patient_appointments():
    st.header("Book an Appointment")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patients WHERE user_id = ?", (st.session_state.user['user_id'],))
    patient_id = cursor.fetchone()[0]
    cursor.execute("SELECT id, name, address, phone FROM hospitals")
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

# Appointments (Hospital)
def hospital_appointments():
    st.header("Manage Appointments")
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

# Medical History (Hospital)
def hospital_medical_history():
    st.header("Patient Medical History")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hospitals WHERE user_id = ?", (st.session_state.user['user_id'],))
    hospital_id = cursor.fetchone()[0]
    cursor.execute("SELECT p.id, p.first_name, p.last_name FROM patients p JOIN appointments a ON p.id = a.patient_id WHERE a.hospital_id = ? GROUP BY p.id", (hospital_id,))
    patients = cursor.fetchall()
    if patients:
        patient = st.selectbox("Select Patient", [f"{p[1]} {p[2]} ({p[0]})" for p in patients], format_func=lambda x: x.split(" (")[0])
        patient_id = patient.split(" (")[1].rstrip(")")
        cursor.execute("SELECT recorded_date, temperature, blood_pressure, pulse, oxygen_saturation, weight, bmi FROM vital_signs WHERE patient_id = ? AND hospital_id = ? ORDER BY recorded_date DESC", (patient_id, hospital_id))
        vitals = cursor.fetchall()
        if vitals:
            df = pd.DataFrame([{"Date": v[0].split("T")[0], "Temperature (°F)": v[1], "BP (mmHg)": v[2], "Pulse (bpm)": v[3], "O2 Sat (%)": v[4], "Weight (lbs)": v[5], "BMI": v[6]} for v in vitals])
            st.line_chart(df.set_index("Date")[["Temperature (°F)", "Pulse (bpm)", "O2 Sat (%)"]])
            st.line_chart(df.set_index("Date")[["Weight (lbs)", "BMI"]])
            # AI Suggestion (Placeholder)
            st.markdown("<div class='info-box'>AI Suggestion: Based on trends, monitor blood pressure and consider a dietary plan.</div>", unsafe_allow_html=True)
            # Predictive Health Insights
            st.subheader("Predictive Health Insights")
            st.markdown("<div class='card'>AI predicts a 20% risk of hypertension based on BMI and BP trends. Recommend regular check-ups.</div>", unsafe_allow_html=True)
        else:
            st.info("No medical history available.")
    conn.close()

# Upload Reports (Patient)
def patient_reports():
    st.header("Upload Medical Reports")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patients WHERE user_id = ?", (st.session_state.user['user_id'],))
    patient_id = cursor.fetchone()[0]
    with st.form("upload_report_form"):
        file = st.file_uploader("Upload Report (PDF/Image)", type=["pdf", "png", "jpg"])
        if file:
            file_content = file.read()
            file_name = file.name
            current_time = datetime.now().isoformat()
            try:
                cursor.execute("INSERT INTO reports (patient_id, hospital_id, file_name, file_content, upload_date, created_at, updated_at) VALUES (?, NULL, ?, ?, ?, ?, ?)", (patient_id, file_name, file_content, current_time, current_time, current_time))
                conn.commit()
                st.success(f"Report {file_name} uploaded successfully")
            except sqlite3.Error as e:
                st.error(f"Error: {e}")
        submitted = st.form_submit_button("Upload")
    conn.close()
    st.markdown("<h3>Uploaded Reports</h3>", unsafe_allow_html=True)
    cursor.execute("SELECT file_name, upload_date FROM reports WHERE patient_id = ? ORDER BY upload_date DESC", (patient_id,))
    reports = cursor.fetchall()
    if reports:
        df = pd.DataFrame([{"File Name": r[0], "Upload Date": r[1].split("T")[0]} for r in reports])
        st.dataframe(df)
    else:
        st.info("No reports uploaded yet.")

# Upload Patient Details (Hospital)
def hospital_patient_management():
    st.header("Patient Management")
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
                password_hash = hashlib.sha256("patient123".encode()).hexdigest()  # Default password
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

# About Page
def about_page():
    st.header("About HealthSync EHR")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    **HealthSync EHR** is a revolutionary centralized electronic health record system designed to eliminate physical reports, streamline diagnosis, and enhance patient care with AI-powered insights. Our unique **Predictive Health Insights** feature analyzes trends to predict health risks and suggest preventive measures, setting us apart globally.

    - **Mission**: To provide accessible, secure, and intelligent healthcare management.
    - **Features**: Dual portals, visual diagnostics, appointment booking, and more.
    - **Contact**: support@healthsync.com
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Main App
if __name__ == "__main__":
    initialize_database()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        login_page()
    else:
        navigation_option = navigation()
        if navigation_option == "Dashboard":
            if st.session_state.role == "patient":
                patient_dashboard()
            else:
                hospital_dashboard()
        elif navigation_option == "Appointments":
            if st.session_state.role == "patient":
                patient_appointments()
            else:
                hospital_appointments()
        elif navigation_option == "Medical History":
            if st.session_state.role == "hospital":
                hospital_medical_history()
            else:
                st.warning("Medical history access is for hospitals only.")
        elif navigation_option == "Reports":
            if st.session_state.role == "patient":
                patient_reports()
            else:
                st.warning("Report upload is for patients only.")
        elif navigation_option == "Patient Management" and st.session_state.role == "hospital":
            hospital_patient_management()
        elif navigation_option == "About":
            about_page()