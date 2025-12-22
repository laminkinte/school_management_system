# app.py
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import base64
import io

# Import modules
from config import translator
from modules.auth import auth
from modules.dashboard import show_dashboard
from modules.students import show_students
from modules.teachers import show_teachers
from modules.attendance import show_attendance
from modules.classes import show_classes
from modules.timetable import show_timetable
from modules.results import show_results
from modules.fees import show_fees
from modules.reports import show_reports
from modules.system_config import show_system_config

# Page configuration
st.set_page_config(
    page_title="Professional School Management System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #34495e;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .language-switcher {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

def login_page():
    """Display login page"""
    st.title("🏫 Professional School Management System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Login", use_container_width=True):
                if auth.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        with col_btn2:
            if st.button("Reset", use_container_width=True):
                st.rerun()
        
        # Demo credentials
        st.markdown("---")
        st.markdown("**Demo Credentials:**")
        st.markdown("- Developer: `developer` / `dev123`")
        st.markdown("- Super Admin: `superadmin` / `admin123`")

def main_app():
    """Main application after login"""
    # Language switcher
    lang = st.sidebar.selectbox("🌍 Language", ["English", "العربية"], index=0)
    translator.set_language('en' if lang == "English" else 'ar')
    
    # User info in sidebar
    user = auth.get_current_user()
    st.sidebar.markdown(f"**👤 {user['full_name']}**")
    st.sidebar.markdown(f"**🎭 {translator.t(user['role'].replace('_', ' '))}**")
    
    # Navigation menu based on role
    menu_options = []
    
    # Common options for all roles
    menu_options.append(translator.t('dashboard'))
    
    # Role-based permissions
    user_role = auth.get_user_role()
    
    if user_role in ['developer', 'super_admin', 'admin']:
        menu_options.extend([
            translator.t('students'),
            translator.t('teachers'),
            translator.t('attendance'),
            translator.t('classes'),
            translator.t('timetable'),
            translator.t('results'),
            translator.t('fees'),
            translator.t('admission'),
            translator.t('reports')
        ])
    
    if user_role in ['developer', 'super_admin']:
        menu_options.append(translator.t('system_config'))
    
    # Navigation
    with st.sidebar:
        selected = option_menu(
            menu_title=translator.t('navigation'),
            options=menu_options,
            icons=['house', 'people', 'person-badge', 'calendar-check', 'books', 
                   'calendar', 'clipboard-data', 'cash-coin', 'person-plus', 
                   'bar-chart', 'gear'],
            menu_icon="cast",
            default_index=0
        )
    
    # Logout button
    if st.sidebar.button(translator.t('logout'), use_container_width=True):
        auth.logout()
        st.rerun()
    
    # Display selected module
    if selected == translator.t('dashboard'):
        show_dashboard(translator)
    elif selected == translator.t('students'):
        show_students(translator, auth)
    elif selected == translator.t('teachers'):
        show_teachers(translator, auth)
    elif selected == translator.t('attendance'):
        show_attendance(translator, auth)
    elif selected == translator.t('classes'):
        show_classes(translator, auth)
    elif selected == translator.t('timetable'):
        show_timetable(translator, auth)
    elif selected == translator.t('results'):
        show_results(translator, auth)
    elif selected == translator.t('fees'):
        show_fees(translator, auth)
    elif selected == translator.t('admission'):
        show_admission(translator, auth)
    elif selected == translator.t('reports'):
        show_reports(translator, auth)
    elif selected == translator.t('system_config'):
        show_system_config(translator, auth)

def show_admission(translator, auth):
    """Admission module"""
    st.title(translator.t('admission'))
    
    tab1, tab2, tab3 = st.tabs([
        translator.t('add'),
        "View Applications",
        "Process Applications"
    ])
    
    with tab1:
        with st.form("admission_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                student_name = st.text_input("Student Name")
                date_of_birth = st.date_input("Date of Birth", min_value=date(2000, 1, 1))
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                parent_name = st.text_input("Parent/Guardian Name")
            
            with col2:
                parent_phone = st.text_input("Parent Phone")
                parent_email = st.text_input("Parent Email")
                address = st.text_area("Address")
                applied_for_class = st.selectbox("Applied Class", ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"])
            
            remarks = st.text_area("Remarks")
            
            if st.form_submit_button("Submit Application"):
                if student_name and parent_name:
                    # Generate application ID
                    application_id = f"APP{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    query = '''
                        INSERT INTO admission_applications 
                        (application_id, student_name, date_of_birth, gender, parent_name, 
                         parent_phone, parent_email, address, applied_for_class, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    
                    db.execute_query(query, (
                        application_id, student_name, date_of_birth, gender, parent_name,
                        parent_phone, parent_email, address, applied_for_class, remarks
                    ))
                    
                    st.success(f"Application submitted successfully! Application ID: {application_id}")
                else:
                    st.error("Please fill all required fields")

def main():
    """Main function"""
    load_css()
    
    # Check authentication
    if not auth.is_authenticated():
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()