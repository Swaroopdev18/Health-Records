# main.py
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
        # Hash the password (admin123)
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
        # Sample patient data
        patients = [
            {
                "id": "PAT_001",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-05-15",
                "gender": "Male"
            },
            {
                "id": "PAT_002",
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1992-08-23",
                "gender": "Female"
            },
            {
                "id": "PAT_003",
                "first_name": "Michael",
                "last_name": "Johnson",
                "date_of_birth": "1975-11-30",
                "gender": "Male"
            }
        ]
        
        # Insert sample patients
        for patient in patients:
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
            INSERT INTO patients (id, first_name, last_name, date_of_birth, gender, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient["id"],
                patient["first_name"],
                patient["last_name"],
                patient["date_of_birth"],
                patient["gender"],
                current_time,
                current_time
            ))
            
            # Insert sample contact info
            cursor.execute('''
            INSERT INTO contact_info (patient_id, phone, email, address, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                patient["id"],
                f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"{patient['first_name'].lower()}.{patient['last_name'].lower()}@example.com",
                f"{random.randint(100, 999)} Main St, Anytown, USA",
                current_time,
                current_time
            ))
            
            # Insert sample medical history
            blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            cursor.execute('''
            INSERT INTO medical_history (patient_id, blood_type, allergies, chronic_conditions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                patient["id"],
                random.choice(blood_types),
                "None" if random.random() > 0.3 else "Penicillin",
                "None" if random.random() > 0.3 else "Hypertension",
                current_time,
                current_time
            ))
            
            # Insert sample insurance info
            cursor.execute('''
            INSERT INTO insurance (patient_id, provider, policy_number, coverage_start_date, coverage_end_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient["id"],
                random.choice(["BlueCross", "Aetna", "UnitedHealth", "Medicare"]),
                f"POL-{random.randint(100000, 999999)}",
                "2023-01-01",
                "2023-12-31",
                current_time,
                current_time
            ))
            
            # Insert sample vital signs (a few entries)
            for i in range(5):
                record_date = (datetime.now() - timedelta(days=i*30)).isoformat()
                cursor.execute('''
                INSERT INTO vital_signs (
                    patient_id, recorded_date, temperature, blood_pressure, pulse, 
                    respiratory_rate, oxygen_saturation, weight, height, bmi, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient["id"],
                    record_date,
                    round(random.uniform(97.0, 99.0), 1),  # Temperature
                    f"{random.randint(110, 140)}/{random.randint(70, 90)}",  # Blood pressure
                    random.randint(60, 100),  # Pulse
                    random.randint(12, 20),  # Respiratory rate
                    round(random.uniform(95.0, 100.0), 1),  # Oxygen
                    round(random.uniform(140.0, 200.0), 1),  # Weight
                    round(random.uniform(60.0, 75.0), 1),  # Height
                    round(random.uniform(18.5, 30.0), 1),  # BMI
                    current_time,
                    current_time
                ))
    
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

# Health System Logo
def get_health_logo():
    # This function creates a simple logo for the health system
    logo_svg = '''
    <svg width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="50" height="50" rx="10" fill="#4361ee" />
        <path d="M25 10 L25 40 M10 25 L40 25" stroke="white" stroke-width="5" />
    </svg>
    '''
    return "data:image/svg+xml;base64," + base64.b64encode(logo_svg.encode()).decode()

# Login page
def login_page():
    # Create two-column layout
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
    # Show header with logo and user info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f'<div class="header-container"><img src="{get_health_logo()}" class="header-logo" /><h1 class="header-title">Health Record System</h1></div>', unsafe_allow_html=True)
    
    with col2:
        # Display user info and logout button
        st.markdown(f"<div style='text-align: right; padding: 10px;'>Logged in as <b>{st.session_state.user['name']}</b> ({st.session_state.user['role']})</div>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()
    
    # Navigation menu
    menu_options = ["Dashboard", "Patients", "Appointments", "Vitals", "Reports", "Settings"]
    selected_option = st.sidebar.selectbox("Navigation", menu_options)
    
    return selected_option

# Dashboard
def dashboard_page():
    st.header("Dashboard")
    
    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Total patients
    cursor.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]
    
    # Total appointments
    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointment_count = cursor.fetchone()[0]
    
    # Recent appointments
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date >= date('now', '-7 days')")
    recent_appointments = cursor.fetchone()[0]
    
    # Recent patient registrations
    cursor.execute("SELECT COUNT(*) FROM patients WHERE created_at >= datetime('now', '-30 days')")
    new_patients = cursor.fetchone()[0]
    
    conn.close()
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Total Patients</div>
            <div class="metric-value">{patient_count}</div>
        </div>
        ''', unsafe_allow_html=True)
        
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Upcoming Appointments</div>
            <div class="metric-value">{appointment_count}</div>
        </div>
        ''', unsafe_allow_html=True)
        
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Last 7 Days Appointments</div>
            <div class="metric-value">{recent_appointments}</div>
        </div>
        ''', unsafe_allow_html=True)
        
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">New Patients (30 days)</div>
            <div class="metric-value">{new_patients}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent patients and appointments
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Recent Patients")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT p.id, p.first_name, p.last_name, p.gender, p.created_at
        FROM patients p
        ORDER BY p.created_at DESC
        LIMIT 5
        ''')
        
        recent_patients = cursor.fetchall()
        conn.close()
        
        if recent_patients:
            # Create a DataFrame for display
            df_patients = pd.DataFrame([
                {
                    "ID": p[0],
                    "Name": f"{p[1]} {p[2]}",
                    "Gender": p[3],
                    "Registered": p[4].split('T')[0] if 'T' in p[4] else p[4]
                } for p in recent_patients
            ])
            
            st.dataframe(df_patients)
        else:
            st.info("No patients in the system.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Upcoming Appointments")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT a.id, p.first_name, p.last_name, a.appointment_date, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.appointment_date >= datetime('now')
        ORDER BY a.appointment_date ASC
        LIMIT 5
        ''')
        
        upcoming_appointments = cursor.fetchall()
        conn.close()
        
        if upcoming_appointments:
            # Create a DataFrame for display
            df_appointments = pd.DataFrame([
                {
                    "ID": a[0],
                    "Patient": f"{a[1]} {a[2]}",
                    "Date": a[3].split('T')[0] if 'T' in a[3] else a[3],
                    "Time": a[3].split('T')[1][:5] if 'T' in a[3] else "",
                    "Status": a[4]
                } for a in upcoming_appointments
            ])
            
            st.dataframe(df_appointments)
        else:
            st.info("No upcoming appointments.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Charts section
    st.markdown("---")
    st.subheader("Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Patient Gender Distribution")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT gender, COUNT(*) as count
        FROM patients
        GROUP BY gender
        ''')
        
        gender_data = cursor.fetchall()
        conn.close()
        
        if gender_data:
            gender_df = pd.DataFrame([
                {
                    "Gender": g[0],
                    "Count": g[1]
                } for g in gender_data
            ])
            
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
        
        # Sample data for appointments
        appointment_status = ["Scheduled", "Completed", "Cancelled", "No-show"]
        status_counts = [random.randint(5, 15) for _ in range(4)]
        
        status_df = pd.DataFrame({
            "Status": appointment_status,
            "Count": status_counts
        })
        
        status_chart = alt.Chart(status_df).mark_bar().encode(
            x='Status',
            y='Count',
            color=alt.Color('Status', scale=alt.Scale(scheme='blues'))
        ).properties(
            width=400,
            height=300
        )
        
        st.altair_chart(status_chart, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# patients management 