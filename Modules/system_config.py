# modules/system_config.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database import db
from modules.auth import auth

def show_system_config(translator, auth_instance):
    """Display system configuration"""
    st.title(translator.t('system_config'))
    
    # Check if user has permission (only developer and super_admin)
    user_role = auth_instance.get_user_role()
    if user_role not in ['developer', 'super_admin']:
        st.error("Access denied. Only developers and super admins can access system configuration.")
        return
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "School Information",
        "Academic Settings",
        "User Management",
        "Database Management",
        "System Logs"
    ])
    
    with tab1:
        st.subheader(translator.t('school_name'))
        
        # Get current school info
        school_info = db.get_dataframe('''
            SELECT config_key, config_value, description 
            FROM system_config 
            WHERE config_key LIKE 'school_%'
            ORDER BY config_key
        ''')
        
        with st.form("school_info_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                school_name = st.text_input("School Name*", value="Demo School")
                school_address = st.text_area("School Address")
                school_phone = st.text_input("School Phone")
                school_email = st.text_input("School Email")
            
            with col2:
                school_principal = st.text_input("Principal Name")
                school_website = st.text_input("Website")
                established_year = st.number_input("Established Year", min_value=1900, max_value=2100, value=2000)
                school_motto = st.text_input("School Motto")
            
            if st.form_submit_button("Save School Information"):
                # Save school info
                configs = [
                    ('school_name', school_name, 'School Name'),
                    ('school_address', school_address, 'School Address'),
                    ('school_phone', school_phone, 'School Phone'),
                    ('school_email', school_email, 'School Email'),
                    ('school_principal', school_principal, 'Principal Name'),
                    ('school_website', school_website, 'School Website'),
                    ('school_established', str(established_year), 'Established Year'),
                    ('school_motto', school_motto, 'School Motto')
                ]
                
                for key, value, desc in configs:
                    # Check if exists
                    existing = db.fetch_one(
                        "SELECT id FROM system_config WHERE config_key = ?",
                        (key,)
                    )
                    
                    if existing:
                        db.execute_query('''
                            UPDATE system_config 
                            SET config_value = ?, description = ?
                            WHERE id = ?
                        ''', (value, desc, existing['id']))
                    else:
                        db.execute_query('''
                            INSERT INTO system_config (config_key, config_value, config_type, description)
                            VALUES (?, ?, 'school_info', ?)
                        ''', (key, value, desc))
                
                st.success("School information saved successfully!")
    
    with tab2:
        st.subheader("Academic Settings")
        
        with st.form("academic_settings_form"):
            current_year = datetime.now().year
            academic_year = st.text_input(
                "Current Academic Year*",
                value=f"{current_year}-{current_year + 1}"
            )
            
            grading_system = st.selectbox(
                "Grading System",
                ["Percentage", "GPA", "Letter Grades", "Custom"]
            )
            
            attendance_threshold = st.slider(
                "Minimum Attendance Percentage",
                min_value=50,
                max_value=100,
                value=75
            )
            
            pass_percentage = st.slider(
                "Passing Percentage",
                min_value=30,
                max_value=70,
                value=40
            )
            
            if st.form_submit_button("Save Academic Settings"):
                configs = [
                    ('academic_year', academic_year, 'Current Academic Year'),
                    ('grading_system', grading_system, 'Grading System Type'),
                    ('attendance_threshold', str(attendance_threshold), 'Minimum Attendance %'),
                    ('pass_percentage', str(pass_percentage), 'Passing Percentage')
                ]
                
                for key, value, desc in configs:
                    existing = db.fetch_one(
                        "SELECT id FROM system_config WHERE config_key = ?",
                        (key,)
                    )
                    
                    if existing:
                        db.execute_query('''
                            UPDATE system_config 
                            SET config_value = ?, description = ?
                            WHERE id = ?
                        ''', (value, desc, existing['id']))
                    else:
                        db.execute_query('''
                            INSERT INTO system_config (config_key, config_value, config_type, description)
                            VALUES (?, ?, 'academic_settings', ?)
                        ''', (key, value, desc))
                
                st.success("Academic settings saved!")
    
    with tab3:
        st.subheader(translator.t('user_management'))
        
        # View existing users
        users_df = db.get_dataframe('''
            SELECT id, username, full_name, email, phone, role, 
                   created_at, is_active
            FROM users
            ORDER BY role, username
        ''')
        
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)
        
        # Add new user
        st.markdown("---")
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username*")
                full_name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")
            
            with col2:
                password = st.text_input("Password*", type="password")
                confirm_password = st.text_input("Confirm Password*", type="password")
                role = st.selectbox(
                    "Role*",
                    ["admin", "teacher", "accountant", "staff"]
                )
                is_active = st.checkbox("Active", value=True)
            
            if st.form_submit_button("Add User"):
                if all([username, full_name, email, password, confirm_password]):
                    if password == confirm_password:
                        # Hash password
                        import hashlib
                        hashed_password = hashlib.sha256(password.encode()).hexdigest()
                        
                        query = '''
                            INSERT INTO users 
                            (username, password, full_name, email, phone, role, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        '''
                        
                        db.execute_query(query, (
                            username, hashed_password, full_name, email,
                            phone, role, 1 if is_active else 0
                        ))
                        
                        st.success("User added successfully!")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab4:
        st.subheader("Database Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Backup Database", use_container_width=True):
                # Create backup
                import shutil
                import os
                
                backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2('school_management.db', backup_file)
                
                with open(backup_file, 'rb') as f:
                    st.download_button(
                        label="Download Backup",
                        data=f,
                        file_name=backup_file,
                        mime="application/octet-stream"
                    )
                
                os.remove(backup_file)
        
        with col2:
            if st.button("Reset Demo Data", use_container_width=True):
                if st.checkbox("I understand this will reset all data except default users"):
                    if st.button("Confirm Reset", type="primary"):
                        # Reset all tables (keep users)
                        tables = [
                            'students', 'teachers', 'classes', 'subjects',
                            'attendance', 'teacher_attendance', 'timetable',
                            'results', 'fees', 'admission_applications',
                            'grading_system'
                        ]
                        
                        for table in tables:
                            db.execute_query(f"DELETE FROM {table}")
                        
                        # Reset system config except school info
                        db.execute_query("DELETE FROM system_config WHERE config_type != 'school_info'")
                        
                        st.success("Demo data reset successfully!")
                        st.rerun()
        
        # Database statistics
        st.markdown("---")
        st.subheader("Database Statistics")
        
        stats = []
        tables = ['students', 'teachers', 'classes', 'attendance', 
                 'results', 'fees', 'users', 'system_config']
        
        for table in tables:
            count = db.fetch_one(f"SELECT COUNT(*) FROM {table}")[0]
            stats.append({'Table': table, 'Records': count})
        
        stats_df = pd.DataFrame(stats)
        st.dataframe(stats_df, use_container_width=True)
    
    with tab5:
        st.subheader("System Logs")
        
        # Recent activities log
        st.info("Activity logs will be displayed here. Implement logging as needed.")
        
        # System information
        st.markdown("---")
        st.subheader("System Information")
        
        import platform
        import sys
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Python Version:** {platform.python_version()}")
            st.write(f"**Streamlit Version:** {st.__version__}")
            st.write(f"**OS:** {platform.system()} {platform.release()}")
        
        with col2:
            st.write(f"**Processor:** {platform.processor()}")
            st.write(f"**Machine:** {platform.machine()}")
            st.write(f"**Platform:** {platform.platform()}")