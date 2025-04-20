import streamlit as st
import pandas as pd
import sqlite3
import os
import json
import hashlib
from datetime import datetime, timedelta
import uuid
import time
import random
import matplotlib.pyplot as plt
import altair as alt
import base64
from PIL import Image
import io

# Set page configuration
st.set_page_config(
    page_title="Health Record System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create database directory if it doesn't exist
os.makedirs("data", exist_ok=True)
DB_FILE = "data/health_records.db"

# Add custom CSS
def local_css():
    st.markdown("""
    <style>
    /* Main Container */
    .main {
        background-color: #f8f9fa;
        color: #333;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Custom Card Style */
    .card {
        border-radius: 10px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Patient Info Card */
    .patient-card {
        background-color: #ffffff;
        border-left: 5px solid #4361ee;
        padding: 15px;
        border-radius:.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    
    /* Success Callout */
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin-bottom: 15px;
    }
    
    /* Warning Callout */
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
        margin-bottom: 15px;
    }
    
    /* Info Callout */
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #17a2b8;
        margin-bottom: 15px;
    }
    
    /* Beautiful Buttons */
    .stButton>button {
        background-color: #4361ee;
        color: white;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #3a56d4;
        box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
    }
    
    /* Delete Button */
    .delete-btn {
        background-color: #e74c3c !important;
    }
    
    .delete-btn:hover {
        background-color: #c0392b !important;
    }
    
    /* Custom Sidebar */
    .css-1d391kg {
        background-color: #2c3e50;
    }
    
    .css-1d391kg .sidebar-content {
        background-color: #2c3e50;
    }
    
    /* Streamlit Elements */
    div.stButton > button:first-child {
        background-color: #4361ee;
        color: white;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #3a56d4;
        box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
    }
    
    /* Alert boxes */
    .st-emotion-cache-16idsys p {
        font-size: 16px;
    }
    
    /* Tabs styling */
    .st-emotion-cache-1y4p8pa {
        padding: 15px;
        border-radius: 0 0 10px 10px;
        border: 1px solid #e0e0e0;
        border-top: none;
    }
    
    .st-emotion-cache-1y4p8pa > div:first-child {
        border-radius: 10px 10px 0 0;
        overflow: hidden;
    }
    
    /* Data tables */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 20px;
    }
    
    .dataframe th {
        background-color: #4361ee;
        color: white;
        padding: 12px;
        text-align: left;
    }
    
    .dataframe td {
        padding: 12px;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .dataframe tr:hover {
        background-color: #e9ecef;
    }
    
    /* Custom header with logo */
    .header-container {
        display: flex;
        align-items: center;
        padding: 1rem;
        background-color: white;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-logo {
        width: 50px;
        margin-right: 15px;
    }
    
    .header-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #4361ee;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Apply CSS
local_css()

# Database initialization
def initialize_database():
    """Create database and tables if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        last_login TIMESTAMP,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth DATE,
        gender TEXT,
        profile_image TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create contact information table
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
    
    # Create medical history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        blood_type TEXT,
        allergies TEXT,
        chronic_conditions TEXT,
        surgeries TEXT,
        family_history TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create vital signs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vital_signs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
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
    
    # Create appointments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        provider_id TEXT REFERENCES users(id),
        appointment_date TIMESTAMP,
        duration INTEGER,
        status TEXT,
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create insurance information table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS insurance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        provider TEXT,
        policy_number TEXT,
        group_number TEXT,
        coverage_start_date DATE,
        coverage_end_date DATE,
        coverage_details TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create visit records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS visit_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        visit_date DATE,
        provider_id TEXT,
        chief_complaint TEXT,
        diagnosis TEXT,
        treatment_plan TEXT,
        notes TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create medication records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT REFERENCES patients(id),
        medication_name TEXT,
        dosage TEXT,
        frequency TEXT,
        start_date DATE,
        end_date DATE,
        prescriber TEXT,
        notes TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Insert a demo admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        current_time = datetime.now().isoformat()
        cursor.execute('''
        INSERT INTO users (id, username, password_hash, name, role, email, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "USR_admin_" + str(int(time.time())),
            "admin",
            password_hash,
            "Administrator",
            "admin",
            "admin@healthsystem.com",
            current_time,
            current_time
        ))
    
    # Insert some demo patients if none exist
    cursor.execute("SELECT COUNT(*) FROM patients")
    if cursor.fetchone()[0] == 0:
        patients = [
            {"id": "PAT_001", "first_name": "John", "last_name": "Doe", "date_of_birth": "1980-05-15", "gender": "Male"},
            {"id": "PAT_002", "first_name": "Jane", "last_name": "Smith", "date_of_birth": "1992-08-23", "gender": "Female"},
            {"id": "PAT_003", "first_name": "Michael", "last_name": "Johnson", "date_of_birth": "1975-11-30", "gender": "Male"}
        ]
        for patient in patients:
            current_time = datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO patients (id, first_name, last_name, date_of_birth, gender, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (patient["id"], patient["first_name"], patient["last_name"], patient["date_of_birth"], patient["gender"], current_time, current_time))
            cursor.execute('''
            INSERT INTO contact_info (patient_id, phone, email, address, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (patient["id"], f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}", f"{patient['first_name'].lower()}.{patient['last_name'].lower()}@example.com", f"{random.randint(100, 999)} Main St, Anytown, USA", current_time, current_time))
            cursor.execute('''
            INSERT INTO medical_history (patient_id, blood_type, allergies, chronic_conditions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (patient["id"], random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]), "None" if random.random() > 0.3 else "Penicillin", "None" if random.random() > 0.3 else "Hypertension", current_time, current_time))
            cursor.execute('''
            INSERT INTO insurance (patient_id, provider, policy_number, coverage_start_date, coverage_end_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (patient["id"], random.choice(["BlueCross", "Aetna", "UnitedHealth", "Medicare"]), f"POL-{random.randint(100000, 999999)}", "2023-01-01", "2023-12-31", current_time, current_time))
            for i in range(5):
                record_date = (datetime.now() - timedelta(days=i*30)).isoformat()
                cursor.execute('''
                INSERT INTO vital_signs (patient_id, recorded_date, temperature, blood_pressure, pulse, respiratory_rate, oxygen_saturation, weight, height, bmi, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient["id"], record_date, round(random.uniform(97.0, 99.0), 1), f"{random.randint(110, 140)}/{random.randint(70, 90)}", random.randint(60, 100), random.randint(12, 20), round(random.uniform(95.0, 100.0), 1), round(random.uniform(140.0, 200.0), 1), round(random.uniform(60.0, 75.0), 1), round(random.uniform(18.5, 30.0), 1), current_time, current_time))
    
    conn.commit()
    conn.close()

# Authentication functions
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

# Health System Logo
def get_health_logo():
    logo_svg = '''
    <svg width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="50" height="50" rx="10" fill="#4361ee" />
        <path d="M25 10 L25 40 M10 25 L40 25" stroke="white" stroke-width="5" />
    </svg>
    '''
    return "data:image/svg+xml;base64," + base64.b64encode(logo_svg.encode()).decode()

# Login page
def login_page():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f'<div class="header-container"><img src="{get_health_logo()}" class="header-logo" /><h1 class="header-title">Health Record System</h1></div>', unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Welcome to the Health Record System")
        st.markdown("Manage patient records, appointments, and medical history with ease.")
        st.markdown("#### Features:")
        st.markdown("• Complete patient profiles<br>• Medical history tracking<br>• Vital signs monitoring<br>• Appointment scheduling<br>• Advanced reporting", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.authenticated = True
                    update_last_login(user['user_id'])
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
        st.markdown("<div class='info-box'>Default admin credentials:<br>Username: admin<br>Password: admin123</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Main Navigation
def main_navigation():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="header-container"><img src="{get_health_logo()}" class="header-logo" /><h1 class="header-title">Health Record System</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: right; padding: 10px;'>Logged in as <b>{st.session_state.user['name']}</b> ({st.session_state.user['role']})</div>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    menu_options = ["Dashboard", "Patients", "Appointments", "Vitals", "Reports", "Settings"]
    return st.sidebar.selectbox("Navigation", menu_options)

# Dashboard
def dashboard_page():
    st.header("Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointment_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date >= date('now', '-7 days')")
    recent_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM patients WHERE created_at >= datetime('now', '-30 days')")
    new_patients = cursor.fetchone()[0]
    conn.close()
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">Total Patients</div><div class="metric-value">{patient_count}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">Upcoming Appointments</div><div class="metric-value">{appointment_count}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">Last 7 Days Appointments</div><div class="metric-value">{recent_appointments}</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div class="metric-label">New Patients (30 days)</div><div class="metric-value">{new_patients}</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Recent Patients")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT p.id, p.first_name, p.last_name, p.gender, p.created_at FROM patients p ORDER BY p.created_at DESC LIMIT 5')
        recent_patients = cursor.fetchall()
        conn.close()
        if recent_patients:
            df_patients = pd.DataFrame([{"ID": p[0], "Name": f"{p[1]} {p[2]}", "Gender": p[3], "Registered": p[4].split('T')[0] if 'T' in p[4] else p[4]} for p in recent_patients])
            st.dataframe(df_patients)
        else:
            st.info("No patients in the system.")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Upcoming Appointments")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT a.id, p.first_name, p.last_name, a.appointment_date, a.status FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.appointment_date >= datetime(\'now\') ORDER BY a.appointment_date ASC LIMIT 5')
        upcoming_appointments = cursor.fetchall()
        conn.close()
        if upcoming_appointments:
            df_appointments = pd.DataFrame([{"ID": a[0], "Patient": f"{a[1]} {a[2]}", "Date": a[3].split('T')[0] if 'T' in a[3] else a[3], "Time": a[3].split('T')[1][:5] if 'T' in a[3] else "", "Status": a[4]} for a in upcoming_appointments])
            st.dataframe(df_appointments)
        else:
            st.info("No upcoming appointments.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Patient Gender Distribution")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT gender, COUNT(*) as count FROM patients GROUP BY gender')
        gender_data = cursor.fetchall()
        conn.close()
        if gender_data:
            gender_df = pd.DataFrame([{"Gender": g[0], "Count": g[1]} for g in gender_data])
            fig, ax = plt.subplots()
            ax.pie(gender_df['Count'], labels=gender_df['Gender'], autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("No patient data available for chart.")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Appointments by Status")
        appointment_status = ["Scheduled", "Completed", "Cancelled", "No-show"]
        status_counts = [random.randint(5, 15) for _ in range(4)]
        status_df = pd.DataFrame({"Status": appointment_status, "Count": status_counts})
        status_chart = alt.Chart(status_df).mark_bar().encode(x='Status', y='Count', color=alt.Color('Status', scale=alt.Scale(scheme='blues'))).properties(width=400, height=300)
        st.altair_chart(status_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Patients Management
def patients_page():
    st.header("Patient Management")
    tab1, tab2, tab3, tab4 = st.tabs(["Search Patients", "Add Patient", "Update Patient", "Delete Patient"])
    with tab1:
        st.subheader("Search Patients")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("Search by ID, Name or Phone", key="search_patient")
        with search_col2:
            search_button = st.button("Search")
        if search_button and search_term:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT p.id, p.first_name, p.last_name, p.gender, p.date_of_birth, c.phone FROM patients p LEFT JOIN contact_info c ON p.id = c.patient_id WHERE p.id LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ? OR c.phone LIKE ?', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            search_results = cursor.fetchall()
            conn.close()
            if search_results:
                st.success(f"Found {len(search_results)} matching patients")
                for result in search_results:
                    patient_id, first_name, last_name, gender, dob, phone = result
                    st.markdown(f'''
                    <div class="patient-card">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <strong>{first_name} {last_name}</strong> ({gender})
                                <br>ID: {patient_id}
                                <br>DOB: {dob if dob else 'Not available'}
                                <br>Phone: {phone if phone else 'Not available'}
                            </div>
                            <div>
                                <form action="" method="get" target="_self">
                                    <input type="hidden" name="view_patient_id" value="{patient_id}">
                                    <button type="submit" style="background-color: #4361ee; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                                        View Details
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.warning(f"No patients found matching '{search_term}'")
        if 'view_patient_id' in st.experimental_get_query_params():
            patient_id = st.experimental_get_query_params()['view_patient_id'][0]
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT p.id, p.first_name, p.last_name, p.gender, p.date_of_birth, c.phone, c.email, c.address, c.emergency_contact_name, c.emergency_contact_phone, m.blood_type, m.allergies, m.chronic_conditions FROM patients p LEFT JOIN contact_info c ON p.id = c.patient_id LEFT JOIN medical_history m ON p.id = m.patient_id WHERE p.id = ?', (patient_id,))
            patient_details = cursor.fetchone()
            if patient_details:
                p_id, f_name, l_name, gender, dob, phone, email, address, emerg_name, emerg_phone, blood_type, allergies, conditions = patient_details
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader(f"Patient Details: {f_name} {l_name}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Personal Information")
                    st.markdown(f"**ID:** {p_id}")
                    st.markdown(f"**Name:** {f_name} {l_name}")
                    st.markdown(f"**Gender:** {gender}")
                    st.markdown(f"**Date of Birth:** {dob}")
                    st.markdown("##### Contact Information")
                    st.markdown(f"**Phone:** {phone if phone else 'Not available'}")
                    st.markdown(f"**Email:** {email if email else 'Not available'}")
                    st.markdown(f"**Address:** {address if address else 'Not available'}")
                with col2:
                    st.markdown("##### Emergency Contact")
                    st.markdown(f"**Name:** {emerg_name if emerg_name else 'Not available'}")
                    st.markdown(f"**Phone:** {emerg_phone if emerg_phone else 'Not available'}")
                    st.markdown("##### Medical Information")
                    st.markdown(f"**Blood Type:** {blood_type if blood_type else 'Not available'}")
                    st.markdown(f"**Allergies:** {allergies if allergies else 'None'}")
                    st.markdown(f"**Chronic Conditions:** {conditions if conditions else 'None'}")
                cursor.execute('SELECT recorded_date, temperature, blood_pressure, pulse, oxygen_saturation, weight FROM vital_signs WHERE patient_id = ? ORDER BY recorded_date DESC LIMIT 5', (patient_id,))
                vitals = cursor.fetchall()
                if vitals:
                    st.markdown("##### Recent Vital Signs")
                    vitals_df = pd.DataFrame([{"Date": v[0].split('T')[0] if 'T' in v[0] else v[0], "Temperature": f"{v[1]} °F" if v[1] else "N/A", "Blood Pressure": v[2] if v[2] else "N/A", "Pulse": v[3] if v[3] else "N/A", "O2 Sat": f"{v[4]}%" if v[4] else "N/A", "Weight": f"{v[5]} lbs" if v[5] else "N/A"} for v in vitals])
                    st.dataframe(vitals_df)
                cursor.execute('SELECT medication_name, dosage, frequency, start_date, end_date FROM medications WHERE patient_id = ? ORDER BY start_date DESC', (patient_id,))
                medications = cursor.fetchall()
                if medications:
                    st.markdown("##### Current Medications")
                    meds_df = pd.DataFrame([{"Medication": m[0], "Dosage": m[1], "Frequency": m[2], "Start Date": m[3], "End Date": m[4] if m[4] else "Ongoing"} for m in medications])
                    st.dataframe(meds_df)
                cursor.execute('SELECT appointment_date, duration, status, reason FROM appointments WHERE patient_id = ? ORDER BY appointment_date DESC LIMIT 5', (patient_id,))
                appointments = cursor.fetchall()
                if appointments:
                    st.markdown("##### Recent Appointments")
                    appt_df = pd.DataFrame([{"Date": a[0].split('T')[0] if 'T' in a[0] else a[0], "Time": a[0].split('T')[1][:5] if 'T' in a[0] else "", "Duration": f"{a[1]} min", "Status": a[2], "Reason": a[3]} for a in appointments])
                    st.dataframe(appt_df)
                st.markdown("</div>", unsafe_allow_html=True)
            conn.close()
    with tab2:
        st.subheader("Add New Patient")
        with st.form("add_patient_form"):
            st.markdown("##### Personal Information")
            cols = st.columns(2)
            with cols[0]: first_name = st.text_input("First Name*")
            with cols[1]: last_name = st.text_input("Last Name*")
            cols = st.columns(2)
            with cols[0]: gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            with cols[1]: dob = st.date_input("Date of Birth")
            st.markdown("##### Contact Information")
            cols = st.columns(2)
            with cols[0]: phone = st.text_input("Phone Number")
            with cols[1]: email = st.text_input("Email Address")
            address = st.text_area("Address", height=100)
            st.markdown("##### Emergency Contact")
            cols = st.columns(2)
            with cols[0]: emergency_name = st.text_input("Contact Name")
            with cols[1]: emergency_phone = st.text_input("Contact Phone")
            st.markdown("##### Medical Information")
            cols = st.columns(3)
            with cols[0]: blood_type = st.selectbox("Blood Type", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            with cols[1]: allergies = st.text_input("Allergies")
            with cols[2]: conditions = st.text_input("Chronic Conditions")
            submitted = st.form_submit_button("Add Patient")
            if submitted:
                if first_name and last_name and re.match(r"^\d{10}$", phone) if phone else True:
                    patient_id = f"PAT_{str(uuid.uuid4())[:8]}"
                    current_time = datetime.now().isoformat()
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    try:
                        cursor.execute('INSERT INTO patients (id, first_name, last_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (patient_id, first_name, last_name, dob.isoformat(), gender, current_time, current_time))
                        cursor.execute('INSERT INTO contact_info (patient_id, phone, email, address, emergency_contact_name, emergency_contact_phone, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, phone, email, address, emergency_name, emergency_phone, current_time, current_time))
                        cursor.execute('INSERT INTO medical_history (patient_id, blood_type, allergies, chronic_conditions, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (patient_id, blood_type, allergies, conditions, current_time, current_time))
                        conn.commit()
                        st.success(f"Patient {first_name} {last_name} added successfully with ID: {patient_id}")
                    except sqlite3.Error as e:
                        st.error(f"Database error: {e}")
                    finally:
                        conn.close()
                else:
                    st.warning("First and last names are required, and phone must be 10 digits if provided")
    with tab3:
        st.subheader("Update Patient")
        update_search = st.text_input("Enter Patient ID or Name to Update", key="update_search")
        if update_search:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, first_name, last_name FROM patients WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?', (f'%{update_search}%', f'%{update_search}%', f'%{update_search}%'))
            patient_results = cursor.fetchall()
            if patient_results:
                update_patient_id = st.selectbox("Select Patient to Update", options=[p[0] for p in patient_results], format_func=lambda x: f"{x} - {next((p[1] + ' ' + p[2] for p in patient_results if p[0] == x), '')}")
                if update_patient_id:
                    cursor.execute('SELECT p.id, p.first_name, p.last_name, p.gender, p.date_of_birth, c.phone, c.email, c.address, c.emergency_contact_name, c.emergency_contact_phone, m.blood_type, m.allergies, m.chronic_conditions FROM patients p LEFT JOIN contact_info c ON p.id = c.patient_id LEFT JOIN medical_history m ON p.id = m.patient_id WHERE p.id = ?', (update_patient_id,))
                    patient_data = cursor.fetchone()
                    if patient_data:
                        p_id, f_name, l_name, gender, dob, phone, email, address, emerg_name, emerg_phone, blood_type, allergies, conditions = patient_data
                        with st.form("update_patient_form"):
                            st.markdown("##### Personal Information")
                            cols = st.columns(2)
                            with cols[0]: new_first_name = st.text_input("First Name*", value=f_name)
                            with cols[1]: new_last_name = st.text_input("Last Name*", value=l_name)
                            cols = st.columns(2)
                            with cols[0]: new_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], index=["Male", "Female", "Other", "Prefer not to say"].index(gender) if gender else 0)
                            with cols[1]: new_dob = st.date_input("Date of Birth", value=datetime.fromisoformat(dob) if dob else datetime.now())
                            st.markdown("##### Contact Information")
                            cols = st.columns(2)
                            with cols[0]: new_phone = st.text_input("Phone Number", value=phone if phone else "")
                            with cols[1]: new_email = st.text_input("Email Address", value=email if email else "")
                            new_address = st.text_area("Address", value=address if address else "", height=100)
                            st.markdown("##### Emergency Contact")
                            cols = st.columns(2)
                            with cols[0]: new_emergency_name = st.text_input("Contact Name", value=emerg_name if emerg_name else "")
                            with cols[1]: new_emergency_phone = st.text_input("Contact Phone", value=emerg_phone if emerg_phone else "")
                            st.markdown("##### Medical Information")
                            cols = st.columns(3)
                            with cols[0]: new_blood_type = st.selectbox("Blood Type", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], index=["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(blood_type) if blood_type in ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] else 0)
                            with cols[1]: new_allergies = st.text_input("Allergies", value=allergies if allergies else "")
                            with cols[2]: new_conditions = st.text_input("Chronic Conditions", value=conditions if conditions else "")
                            update_submitted = st.form_submit_button("Update Patient")
                            if update_submitted:
                                if new_first_name and new_last_name and (re.match(r"^\d{10}$", new_phone) if new_phone else True):
                                    current_time = datetime.now().isoformat()
                                    try:
                                        cursor.execute('UPDATE patients SET first_name = ?, last_name = ?, date_of_birth = ?, gender = ?, updated_at = ? WHERE id = ?', (new_first_name, new_last_name, new_dob.isoformat(), new_gender, current_time, update_patient_id))
                                        cursor.execute('UPDATE contact_info SET phone = ?, email = ?, address = ?, emergency_contact_name = ?, emergency_contact_phone = ?, updated_at = ? WHERE patient_id = ?', (new_phone, new_email, new_address, new_emergency_name, new_emergency_phone, current_time, update_patient_id))
                                        cursor.execute('UPDATE medical_history SET blood_type = ?, allergies = ?, chronic_conditions = ?, updated_at = ? WHERE patient_id = ?', (new_blood_type, new_allergies, new_conditions, current_time, update_patient_id))
                                        conn.commit()
                                        st.success(f"Patient {new_first_name} {new_last_name} updated successfully")
                                    except sqlite3.Error as e:
                                        st.error(f"Database error: {e}")
                                else:
                                    st.warning("First and last names are required, and phone must be 10 digits if provided")
            else:
                st.warning(f"No patients found matching '{update_search}'")
            conn.close()
    with tab4:
        st.subheader("Delete Patient")
        st.warning("⚠️ Deleting a patient will permanently remove all their data from the system.")
        delete_search = st.text_input("Enter Patient ID or Name to Delete", key="delete_search")
        if delete_search:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, first_name, last_name FROM patients WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?', (f'%{delete_search}%', f'%{delete_search}%', f'%{delete_search}%'))
            patient_results = cursor.fetchall()
            if patient_results:
                delete_patient_id = st.selectbox("Select Patient to Delete", options=[p[0] for p in patient_results], format_func=lambda x: f"{x} - {next((p[1] + ' ' + p[2] for p in patient_results if p[0] == x), '')}")
                if delete_patient_id:
                    patient_name = next((f"{p[1]} {p[2]}" for p in patient_results if p[0] == delete_patient_id), "")
                    st.markdown(f"<div class='warning-box'>Are you sure you want to delete patient: <b>{patient_name}</b> ({delete_patient_id})?</div>", unsafe_allow_html=True)
                    confirm_delete = st.checkbox("I understand this action cannot be undone", key="confirm_delete")
                    if confirm_delete and st.button("Delete Patient", key="execute_delete"):
                        try:
                            cursor.execute("DELETE FROM medications WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM visit_records WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM insurance WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM appointments WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM vital_signs WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM medical_history WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM contact_info WHERE patient_id = ?", (delete_patient_id,))
                            cursor.execute("DELETE FROM patients WHERE id = ?", (delete_patient_id,))
                            conn.commit()
                            st.success(f"Patient {patient_name} ({delete_patient_id}) has been deleted successfully")
                        except sqlite3.Error as e:
                            st.error(f"Database error: {e}")
            else:
                st.warning(f"No patients found matching '{delete_search}'")
            conn.close()

# Appointments Management
def appointments_page():
    st.header("Appointment Management")
    tab1, tab2, tab3 = st.tabs(["View Appointments", "Schedule Appointment", "Manage Appointments"])
    with tab1:
        st.subheader("View Appointments")
        col1, col2, col3 = st.columns(3)
        with col1: view_option = st.selectbox("View", ["All", "Upcoming", "Past", "Today"])
        with col2: status_filter = st.selectbox("Status", ["All", "Scheduled", "Completed", "Cancelled", "No-show"])
        with col3: date_filter = st.date_input("Date", datetime.now())
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = 'SELECT a.id, p.id as patient_id, p.first_name, p.last_name, a.appointment_date, a.duration, a.status, a.reason, u.name as provider_name FROM appointments a JOIN patients p ON a.patient_id = p.id LEFT JOIN users u ON a.provider_id = u.id WHERE 1=1'
        params = []
        if view_option == "Upcoming": query += " AND a.appointment_date > datetime('now')"
        elif view_option == "Past": query += " AND a.appointment_date < datetime('now')"
        elif view_option == "Today": query += " AND date(a.appointment_date) = date('now')"
        if status_filter != "All": query += " AND a.status = ?"; params.append(status_filter)
        if view_option == "All" and date_filter: query += " AND date(a.appointment_date) = ?"; params.append(date_filter.isoformat())
        query += " ORDER BY a.appointment_date ASC"
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        if appointments:
            appointments_df = pd.DataFrame([{"ID": a[0], "Patient ID": a[1], "Patient Name": f"{a[2]} {a[3]}", "Date": a[4].split("T")[0] if "T" in a[4] else a[4], "Time": a[4].split("T")[1][:5] if "T" in a[4] else "", "Duration": f"{a[5]} min" if a[5] else "N/A", "Status": a[6], "Reason": a[7], "Provider": a[8] if a[8] else "Not assigned"} for a in appointments])
            st.dataframe(appointments_df)
            selected_appt = st.selectbox("Select appointment to view details", [f"{a[0]} - {a[2]} {a[3]} ({a[4].split('T')[0] if 'T' in a[4] else a[4]})" for a in appointments])
            if selected_appt:
                appt_id = selected_appt.split(" - ")[0]
                cursor.execute('SELECT a.id, p.id as patient_id, p.first_name, p.last_name, a.appointment_date, a.duration, a.status, a.reason, a.notes, u.name as provider_name FROM appointments a JOIN patients p ON a.patient_id = p.id LEFT JOIN users u ON a.provider_id = u.id WHERE a.id = ?', (appt_id,))
                appt_details = cursor.fetchone()
                if appt_details:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.subheader(f"Appointment Details #{appt_details[0]}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Patient:** {appt_details[2]} {appt_details[3]} (ID: {appt_details[1]})")
                        st.markdown(f"**Date:** {appt_details[4].split('T')[0] if 'T' in appt_details[4] else appt_details[4]}")
                        st.markdown(f"**Time:** {appt_details[4].split('T')[1][:5] if 'T' in appt_details[4] else 'N/A'}")
                        st.markdown(f"**Duration:** {appt_details[5]} minutes")
                    with col2:
                        st.markdown(f"**Status:** {appt_details[6]}")
                        st.markdown(f"**Reason:** {appt_details[7]}")
                        st.markdown(f"**Provider:** {appt_details[9] if appt_details[9] else 'Not assigned'}")
                    st.markdown("**Notes:**")
                    st.markdown(f"{appt_details[8] if appt_details[8] else 'No notes recorded.'}")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No appointments found matching the selected criteria.")
        conn.close()
    with tab2:
        st.subheader("Schedule New Appointment")
        with st.form("schedule_appointment_form"):
            patient_search = st.text_input("Search Patient (ID or Name)")
            patient_id = None
            patient_name = ""
            if patient_search:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT id, first_name, last_name FROM patients WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?', (f'%{patient_search}%', f'%{patient_search}%', f'%{patient_search}%'))
                patient_results = cursor.fetchall()
                conn.close()
                if patient_results:
                    patient_options = [f"{p[0]} - {p[1]} {p[2]}" for p in patient_results]
                    selected_patient = st.selectbox("Select Patient", options=patient_options)
                    if selected_patient:
                        patient_id = selected_patient.split(" - ")[0]
                        patient_name = selected_patient.split(" - ")[1]
                        st.success(f"Selected patient: {patient_name}")
                else:
                    st.warning(f"No patients found matching '{patient_search}'")
            st.markdown("### Appointment Details")
            col1, col2 = st.columns(2)
            with col1: appointment_date = st.date_input("Date", min_value=datetime.now().date())
            with col2: appointment_time = st.time_input("Time", value=datetime.now().time().replace(minute=0, second=0, microsecond=0))
            col1, col2 = st.columns(2)
            with col1: duration = st.slider("Duration (minutes)", min_value=15, max_value=120, value=30, step=15)
            with col2: status = st.selectbox("Status", ["Scheduled", "Tentative"])
            reason = st.text_input("Reason for Visit")
            notes = st.text_area("Notes")
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM users WHERE role = "doctor" OR role = "admin"')
            providers = cursor.fetchall()
            if providers:
                provider_options = [f"{p[0]} - {p[1]}" for p in providers]
                provider_options.insert(0, "Not assigned")
                selected_provider = st.selectbox("Provider", options=provider_options)
                provider_id = selected_provider.split(" - ")[0] if selected_provider != "Not assigned" else None
            else:
                st.warning("No providers found in the system.")
                provider_id = None
            submitted = st.form_submit_button("Schedule Appointment")
            if submitted:
                if patient_id and appointment_date:
                    appointment_datetime = datetime.combine(appointment_date, appointment_time).isoformat()
                    current_time = datetime.now().isoformat()
                    try:
                        cursor.execute('INSERT INTO appointments (patient_id, provider_id, appointment_date, duration, status, reason, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, provider_id, appointment_datetime, duration, status, reason, notes, current_time, current_time))
                        conn.commit()
                        st.success(f"Appointment scheduled successfully for {patient_name} on {appointment_date} at {appointment_time}")
                    except sqlite3.Error as e:
                        st.error(f"Database error: {e}")
                    finally:
                        conn.close()
                else:
                    st.warning("Please select a patient and appointment date")
            conn.close()
    with tab3:
        st.subheader("Manage Appointments")
        appt_search = st.text_input("Enter Appointment ID or Patient Name", key="appt_search")
        if appt_search:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT a.id, p.id as patient_id, p.first_name, p.last_name, a.appointment_date FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.id LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ?', (f'%{appt_search}%', f'%{appt_search}%', f'%{appt_search}%'))
            appt_results = cursor.fetchall()
            if appt_results:
                manage_appt_id = st.selectbox("Select Appointment to Manage", options=[a[0] for a in appt_results], format_func=lambda x: f"{x} - {next((a[2] + ' ' + a[3] + ' (' + (a[4].split('T')[0] if 'T' in a[4] else a[4]) + ')' for a in appt_results if a[0] == x), '')}")
                if manage_appt_id:
                    cursor.execute('SELECT a.id, a.patient_id, a.provider_id, a.appointment_date, a.duration, a.status, a.reason, a.notes FROM appointments a WHERE a.id = ?', (manage_appt_id,))
                    appt_data = cursor.fetchone()
                    update_tab, delete_tab = st.tabs(["Update Appointment", "Cancel/Delete Appointment"])
                    with update_tab:
                        with st.form("update_appointment_form"):
                            cursor.execute("SELECT id, first_name, last_name FROM patients WHERE id = ?", (appt_data[1],))
                            patient_info = cursor.fetchone()
                            patient_name = f"{patient_info[1]} {patient_info[2]}" if patient_info else "Unknown"
                            st.markdown(f"Updating appointment for **{patient_name}**")
                            appt_datetime = datetime.fromisoformat(appt_data[3]) if "T" in appt_data[3] else datetime.strptime(appt_data[3], "%Y-%m-%d %H:%M:%S")
                            appt_date = appt_datetime.date()
                            appt_time = appt_datetime.time()
                            col1, col2 = st.columns(2)
                            with col1: new_date = st.date_input("Date", value=appt_date)
                            with col2: new_time = st.time_input("Time", value=appt_time)
                            col1, col2 = st.columns(2)
                            with col1: new_duration = st.slider("Duration (minutes)", min_value=15, max_value=120, value=appt_data[4], step=15)
                            with col2: new_status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled", "No-show"], index=["Scheduled", "Completed", "Cancelled", "No-show"].index(appt_data[5]) if appt_data[5] in ["Scheduled", "Completed", "Cancelled", "No-show"] else 0)
                            new_reason = st.text_input("Reason for Visit", value=appt_data[6] if appt_data[6] else "")
                            new_notes = st.text_area("Notes", value=appt_data[7] if appt_data[7] else "")
                            cursor.execute('SELECT id, name FROM users WHERE role = "doctor" OR role = "admin"')
                            providers = cursor.fetchall()
                            if providers:
                                provider_options = [f"{p[0]} - {p[1]}" for p in providers]
                                provider_options.insert(0, "Not assigned")
                                current_provider_str = f"{appt_data[2]} - {next((p[1] for p in providers if p[0] == appt_data[2]), 'Not assigned')}" if appt_data[2] else "Not assigned"
                                selected_index = provider_options.index(current_provider_str) if current_provider_str in provider_options else 0
                                selected_provider = st.selectbox("Provider", options=provider_options, index=selected_index)
                                new_provider_id = selected_provider.split(" - ")[0] if selected_provider != "Not assigned" else None
                            else:
                                st.warning("No providers found in the system.")
                                new_provider_id = None
                            update_submitted = st.form_submit_button("Update Appointment")
                            if update_submitted:
                                try:
                                    new_datetime = datetime.combine(new_date, new_time).isoformat()
                                    current_time = datetime.now().isoformat()
                                    cursor.execute('UPDATE appointments SET provider_id = ?, appointment_date = ?, duration = ?, status = ?, reason = ?, notes = ?, updated_at = ? WHERE id = ?', (new_provider_id, new_datetime, new_duration, new_status, new_reason, new_notes, current_time, manage_appt_id))
                                    conn.commit()
                                    st.success(f"Appointment #{manage_appt_id} updated successfully")
                                except sqlite3.Error as e:
                                    st.error(f"Database error: {e}")
                    with delete_tab:
                        st.markdown("<div class='warning-box'>⚠️ Cancelling or deleting an appointment cannot be undone.</div>", unsafe_allow_html=True)
                        action = st.radio("Action", ["Cancel Appointment", "Delete Appointment"])
                        if action == "Cancel Appointment":
                            if st.button("Cancel This Appointment"):
                                try:
                                    current_time = datetime.now().isoformat()
                                    cursor.execute('UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?', ("Cancelled", current_time, manage_appt_id))
                                    conn.commit()
                                    st.success(f"Appointment #{manage_appt_id} has been cancelled")
                                except sqlite3.Error as e:
                                    st.error(f"Database error: {e}")
                        else:
                            confirm_delete = st.checkbox("I understand this will permanently delete this appointment", key="confirm_appt_delete")
                            if confirm_delete and st.button("Delete This Appointment"):
                                try:
                                    cursor.execute("DELETE FROM appointments WHERE id = ?", (manage_appt_id,))
                                    conn.commit()
                                    st.success(f"Appointment #{manage_appt_id} has been deleted successfully")
                                except sqlite3.Error as e:
                                    st.error(f"Database error: {e}")
            else:
                st.warning(f"No appointments found matching '{appt_search}'")
            conn.close()

# Vitals Management
def vitals_page():
    st.header("Vital Signs Management")
    tab1, tab2, tab3 = st.tabs(["Record Vitals", "Vital Signs History", "Vital Signs Charts"])
    with tab1:
        st.subheader("Record Patient Vital Signs")
        patient_search = st.text_input("Search Patient (ID or Name)", key="vitals_patient_search")
        if patient_search:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, first_name, last_name FROM patients WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?', (f'%{patient_search}%', f'%{patient_search}%', f'%{patient_search}%'))
            patient_results = cursor.fetchall()
            if patient_results:
                patient_options = [f"{p[0]} - {p[1]} {p[2]}" for p in patient_results]
                selected_patient = st.selectbox("Select Patient", options=patient_options, key="vitals_patient_select")
                if selected_patient:
                    patient_id = selected_patient.split(" - ")[0]
                    patient_name = selected_patient.split(" - ")[1]
                    st.success(f"Recording vitals for: {patient_name}")
                    with st.form("record_vitals_form"):
                        st.markdown("### Vital Signs")
                        col1, col2 = st.columns(2)
                        with col1: record_date = st.date_input("Date", value=datetime.now().date())
                        with col2: record_time = st.time_input("Time", value=datetime.now().time())
                        col1, col2, col3 = st.columns(3)
                        with col1: temperature = st.number_input("Temperature (°F)", min_value=93.0, max_value=108.0, value=98.6, step=0.1)
                        with col2: bp_systolic = st.number_input("Blood Pressure - Systolic", min_value=70, max_value=200, value=120)
                        with col3: bp_diastolic = st.number_input("Blood Pressure - Diastolic", min_value=40, max_value=120, value=80)
                        col1, col2, col3 = st.columns(3)
                        with col1: pulse = st.number_input("Pulse (bpm)", min_value=30, max_value=220, value=75)
                        with col2: respiratory_rate = st.number_input("Respiratory Rate (breaths/min)", min_value=8, max_value=40, value=16)
                        with col3: oxygen = st.number_input("Oxygen Saturation (%)", min_value=70.0, max_value=100.0, value=98.0, step=0.1)
                        col1, col2, col3 = st.columns(3)
                        with col1: weight = st.number_input("Weight (lbs)", min_value=1.0, max_value=500.0, value=150.0, step=0.1)
                        with col2: height = st.number_input("Height (inches)", min_value=20.0, max_value=96.0, value=68.0, step=0.1)
                        with col3: bmi = st.number_input("BMI", min_value=10.0, max_value=50.0, value=round((weight * 703) / (height * height), 1), step=0.1, disabled=True)
                        notes = st.text_area("Notes")
                        submitted = st.form_submit_button("Record Vital Signs")
                        if submitted:
                            try:
                                recorded_datetime = datetime.combine(record_date, record_time).isoformat()
                                current_time = datetime.now().isoformat()
                                bmi = round((weight * 703) / (height * height), 1)
                                blood_pressure = f"{bp_systolic}/{bp_diastolic}"
                                conn = sqlite3.connect(DB_FILE)
                                cursor = conn.cursor()
                                cursor.execute('INSERT INTO vital_signs (patient_id, recorded_date, temperature, blood_pressure, pulse, respiratory_rate, oxygen_saturation, weight, height, bmi, recorded_by, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (patient_id, recorded_datetime, temperature, blood_pressure, pulse, respiratory_rate, oxygen, weight, height, bmi, st.session_state.user['name'], notes, current_time, current_time))
                                conn.commit()
                                st.success(f"Vital signs recorded successfully for {patient_name}")
                                st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                                st.markdown(f"#### Vital Signs Summary for {patient_name}")
                                st.markdown(f"**Temperature:** {temperature} °F")
                                st.markdown(f"**Blood Pressure:** {blood_pressure} mmHg")
                                st.markdown(f"**Pulse:** {pulse} bpm")
                                st.markdown(f"**Respiratory Rate:** {respiratory_rate} breaths/min")
                                st.markdown(f"**Oxygen Saturation:** {oxygen}%")
                                st.markdown(f"**Weight:** {weight} lbs")
                                st.markdown(f"**Height:** {height} inches")
                                st.markdown(f"**BMI:** {bmi}")
                                st.markdown("</div>", unsafe_allow_html=True)
                            except sqlite3.Error as e:
                                st.error(f"Database error: {e}")
                            finally:
                                conn.close()
            else:
                st.warning(f"No patients found matching '{patient_search}'")
            conn.close()
    with tab2:
        st.subheader("Patient Vital Signs History")
        history_patient_search = st.text_input("Search Patient (ID or Name)", key="history_patient_search")
        if history_patient_search:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, first_name, last_name FROM patients WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?', (f'%{history_patient_search}%', f'%{history_patient_search}%', f'%{history_patient_search}%'))
            patient_results = cursor.fetchall()
            if patient_results:
                patient_options = [f"{p[0]} - {p[1]} {p[2]}" for p in patient_results]
                selected_patient = st.selectbox("Select Patient", options=patient_options, key="history_patient_select")
                if selected_patient:
                    patient_id = selected_patient.split(" - ")[0]
                    patient_name = selected_patient.split(" - ")[1]
                    cursor.execute('SELECT id, recorded_date, temperature, blood_pressure, pulse, respiratory_rate, oxygen_saturation, weight, height, bmi, recorded_by, notes FROM vital_signs WHERE patient_id = ? ORDER BY recorded_date DESC', (patient_id,))
                    vitals_history = cursor.fetchall()
                    if vitals_history:
                        st.markdown(f"### Vital Signs History for {patient_name}")
                        vitals_df = pd.DataFrame([{"Date": v[1].split("T")[0] if "T" in v[1] else v[1].split(" ")[0], "Time": v[1].split("T")[1][:5] if "T" in v[1] else v[1].split(" ")[1][:5] if " " in v[1] else "", "Temperature (°F)": v[2], "Blood Pressure (mmHg)": v[3], "Pulse (bpm)": v[4], "Respiratory Rate (breaths/min)": v[5], "Oxygen Saturation (%)": v[6], "Weight (lbs)": v[7], "Height (inches)": v[8], "BMI": v[9], "Recorded By": v[10], "Notes": v[11] if v[11] else "N/A"} for v in vitals_history])
                        st.dataframe(vitals_df)
                    else:
                        st.info(f"No vital signs history available for {patient_name}.")
            else:
                st.warning(f"No patients found matching '{history_patient_search}'")
            conn.close()
    with tab3:
        st.subheader("Vital Signs Charts")
        chart_patient_search = st.text_input("Search Patient (ID or Name)", key="chart_patient_search")
        if chart_patient_search:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, first_name, last_name FROM patients WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?', (f'%{chart_patient_search}%', f'%{chart_patient_search}%', f'%{chart_patient_search}%'))
            patient_results = cursor.fetchall()
            if patient_results:
                patient_options = [f"{p[0]} - {p[1]} {p[2]}" for p in patient_results]
                selected_patient = st.selectbox("Select Patient", options=patient_options, key="chart_patient_select")
                if selected_patient:
                    patient_id = selected_patient.split(" - ")[0]
                    patient_name = selected_patient.split(" - ")[1]
                    cursor.execute('SELECT recorded_date, temperature, pulse, oxygen_saturation, weight, height, bmi FROM vital_signs WHERE patient_id = ? ORDER BY recorded_date ASC', (patient_id,))
                    vitals_chart_data = cursor.fetchall()
                    if vitals_chart_data:
                        chart_df = pd.DataFrame([{"Date": v[0].split("T")[0] if "T" in v[0] else v[0], "Temperature (°F)": v[1], "Pulse (bpm)": v[2], "Oxygen Saturation (%)": v[3], "Weight (lbs)": v[4], "Height (inches)": v[5], "BMI": v[6]} for v in vitals_chart_data])
                        st.line_chart(chart_df.set_index("Date")[["Temperature (°F)", "Pulse (bpm)", "Oxygen Saturation (%)"]])
                        st.line_chart(chart_df.set_index("Date")[["Weight (lbs)", "BMI"]])
                    else:
                        st.info(f"No vital signs data available for {patient_name}.")
            else:
                st.warning(f"No patients found matching '{chart_patient_search}'")
            conn.close()

# Reports (Placeholder)
def reports_page():
    st.header("Reports")
    st.info("Reports functionality is under development.")

# Settings (Placeholder)
def settings_page():
    st.header("Settings")
    st.info("Settings functionality is under development.")

# Main App Logic
if __name__ == "__main__":
    initialize_database()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        login_page()
    else:
        selected_option = main_navigation()
        if selected_option == "Dashboard": dashboard_page()
        elif selected_option == "Patients": patients_page()
        elif selected_option == "Appointments": appointments_page()
        elif selected_option == "Vitals": vitals_page()
        elif selected_option == "Reports": reports_page()
        elif selected_option == "Settings": settings_page()