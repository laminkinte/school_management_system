import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

# Import modules
from config import APP_CONFIG, LANGUAGES, ROLES
from utils import lang_manager, init_session_state
from auth import auth
from database import db

# Import modules
from modules.dashboard import DashboardModule
from modules.user_management import UserManagementModule
from modules.attendance import AttendanceModule
from modules.classes import ClassesModule
from modules.admission import AdmissionModule
from modules.timetable import TimetableModule
from modules.results import ResultsModule
from modules.fees import FeesModule
from modules.system_config import SystemConfigModule
from modules.reports import ReportsModule

# Add this function at the top of app.py
def load_css():
    """Load custom CSS from file"""
    try:
        with open('assets/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback inline CSS if file not found
        st.markdown("""
        <style>
        .stApp { font-family: Arial, sans-serif; }
        </style>
        """, unsafe_allow_html=True)

# Call this function at the beginning of main()
def main():
    load_css()

class SchoolManagementSystem:
    """Main application class"""
    
    def __init__(self):
        """Initialize application"""
        self.set_page_config()
        init_session_state()
        self.lang_manager = lang_manager
        self.text = self.lang_manager.get_text
        
        # Check if database exists
        if not os.path.exists('school_management.db'):
            st.warning("Database not found. Running initial setup...")
            self.run_initial_setup()
        
        # Initialize modules
        self.modules = {
            'dashboard': DashboardModule(),
            'user_management': UserManagementModule(),
            'attendance': AttendanceModule(),
            'classes': ClassesModule(),
            'admission': AdmissionModule(),
            'timetable': TimetableModule(),
            'results': ResultsModule(),
            'fees': FeesModule(),
            'system_config': SystemConfigModule(),
            'reports': ReportsModule()
        }
    
    def run_initial_setup(self):
        """Run initial database setup"""
        from auth import auth
        
        # Create default admin user
        auth.create_default_admin()
        
        st.success("✅ Database initialized successfully!")
        st.info("Default admin credentials:\nUsername: superadmin\nPassword: admin123")
    
    def set_page_config(self):
        """Set page configuration"""
        st.set_page_config(
            page_title=APP_CONFIG['title'],
            layout=APP_CONFIG['layout'],
            initial_sidebar_state=APP_CONFIG['initial_sidebar_state']
        )
    
    def login_page(self):
        """Display login page"""
        st.markdown(f"""
            <div style="text-align: center; padding: 50px 0;">
                <h1>{self.text('app_title')}</h1>
                <p>{self.text('welcome_message')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.subheader(self.text('login'))
                
                username = st.text_input(self.text('username'))
                password = st.text_input(self.text('password'), type="password")
                
                # Language selector
                language = st.selectbox(
                    self.text('language'),
                    options=list(LANGUAGES.keys()),
                    index=0 if st.session_state.get('language', 'en') == 'en' else 1
                )
                
                submitted = st.form_submit_button(self.text('login'), type="primary")
                
                if submitted:
                    # Set language
                    language_code = LANGUAGES[language]
                    self.lang_manager.set_language(language_code)
                    
                    # Attempt login
                    with st.spinner(self.text('logging_in')):
                        success, message = auth.login(username, password)
                        
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
    
    def sidebar_menu(self):
        """Display sidebar menu based on user role"""
        text = self.text
        
        with st.sidebar:
            # User info
            if st.session_state.get('authenticated'):
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px 0;">
                        <h3>{text('welcome')}</h3>
                        <h4>{st.session_state.get('full_name', '')}</h4>
                        <p><small>{st.session_state.get('role', '').replace('_', ' ').title()}</small></p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.divider()
            
            # Language selector
            current_lang = st.session_state.get('language', 'en')
            lang_display = 'English' if current_lang == 'en' else 'العربية'
            
            if st.button(f"🌍 {lang_display}"):
                new_lang = 'ar' if current_lang == 'en' else 'en'
                self.lang_manager.set_language(new_lang)
                st.rerun()
            
            st.divider()
            
            # Menu options based on role
            menu_options = []
            
            # Dashboard - Available to all
            menu_options.append({"icon": "📊", "label": text("dashboard"), "key": "dashboard"})
            
            # User Management - Admin and above
            if auth.has_permission(ROLES['ADMIN']):
                menu_options.append({"icon": "👥", "label": text("user_management"), "key": "user_management"})
            
            # Attendance - Teacher and above
            if auth.has_permission(ROLES['TEACHER']):
                menu_options.append({"icon": "✅", "label": text("attendance"), "key": "attendance"})
            
            # Classes - Teacher and above
            if auth.has_permission(ROLES['TEACHER']):
                menu_options.append({"icon": "🏫", "label": text("classes"), "key": "classes"})
            
            # Admission - Admin and above
            if auth.has_permission(ROLES['ADMIN']):
                menu_options.append({"icon": "📝", "label": text("admission"), "key": "admission"})
            
            # Timetable - Teacher and above
            if auth.has_permission(ROLES['TEACHER']):
                menu_options.append({"icon": "📅", "label": text("timetable"), "key": "timetable"})
            
            # Results - Teacher and above
            if auth.has_permission(ROLES['TEACHER']):
                menu_options.append({"icon": "📈", "label": text("results"), "key": "results"})
            
            # Fees - Admin and above
            if auth.has_permission(ROLES['ADMIN']):
                menu_options.append({"icon": "💰", "label": text("fees"), "key": "fees"})
            
            # System Configuration - Super Admin and above
            if auth.has_permission(ROLES['SUPER_ADMIN']):
                menu_options.append({"icon": "⚙️", "label": text("system_config"), "key": "system_config"})
            
            # Reports - Teacher and above
            if auth.has_permission(ROLES['TEACHER']):
                menu_options.append({"icon": "📋", "label": text("reports"), "key": "reports"})
            
            # Developer Console - Developer only
            if auth.has_permission(ROLES['DEVELOPER']):
                menu_options.append({"icon": "💻", "label": text("developer_console"), "key": "developer"})
            
            # Create menu
            icons = [opt["icon"] for opt in menu_options]
            labels = [opt["label"] for opt in menu_options]
            keys = [opt["key"] for opt in menu_options]
            
            selected = option_menu(
                menu_title=None,
                options=labels,
                icons=icons,
                menu_icon="cast",
                default_index=0,
                key="main_menu"
            )
            
            # Set selected page
            if selected:
                selected_index = labels.index(selected)
                st.session_state['page'] = keys[selected_index]
            
            st.divider()
            
            # Logout button
            if st.session_state.get('authenticated'):
                if st.button(text('logout'), use_container_width=True):
                    auth.logout()
    
    def developer_console(self):
        """Developer console page"""
        text = self.text
        
        st.title(text('developer_console'))
        
        tab1, tab2, tab3, tab4 = st.tabs([
            text('database_status'),
            text('system_logs'),
            text('performance'),
            text('backup')
        ])
        
        with tab1:
            self.display_database_status()
        
        with tab2:
            self.display_system_logs()
        
        with tab3:
            self.display_performance_metrics()
        
        with tab4:
            self.display_backup_restore()
    
    def display_database_status(self):
        """Display database status information"""
        text = self.text
        
        # Check database connection
        status, message = db.check_connection()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(text('database_status'), "✅ Connected" if status else "❌ Disconnected")
            st.write(f"**Message:** {message}")
        
        with col2:
            st.metric(text('database_size'), db.get_database_size())
        
        # Table statistics
        st.subheader(text('table_statistics'))
        
        query = """
            SELECT 
                name as table_name,
                (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%') as table_count
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        
        try:
            tables = db.execute_query(query, fetch_all=True)
            if tables:
                # Get row counts for each table
                table_data = []
                for table in tables:
                    count_query = f"SELECT COUNT(*) as row_count FROM {table['table_name']}"
                    count_result = db.execute_query(count_query, fetch_one=True)
                    table_data.append({
                        'table_name': table['table_name'],
                        'row_count': count_result['row_count'] if count_result else 0
                    })
                
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
                
                # Database actions
                st.subheader(text('database_actions'))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(text('optimize_database')):
                        success, msg = db.vacuum_database()
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                
                with col2:
                    if st.button(text('check_integrity')):
                        integrity_query = "PRAGMA integrity_check"
                        result = db.execute_query(integrity_query, fetch_one=True)
                        if result and result['integrity_check'] == 'ok':
                            st.success("✅ Database integrity check passed")
                        else:
                            st.error("❌ Database integrity check failed")
                
                with col3:
                    if st.button(text('export_schema')):
                        schema_query = "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        schemas = db.execute_query(schema_query, fetch_all=True)
                        schema_text = "\n\n".join([s['sql'] for s in schemas])
                        st.download_button(
                            label="Download Schema",
                            data=schema_text,
                            file_name="database_schema.sql",
                            mime="text/sql"
                        )
                        
        except Exception as e:
            st.error(f"Error fetching table statistics: {e}")
    
    def display_system_logs(self):
        """Display system logs"""
        text = self.text
        
        st.subheader(text('system_logs'))
        
        # Log viewer
        log_level = st.selectbox(text('log_level'), ['INFO', 'WARNING', 'ERROR', 'DEBUG', 'ALL'])
        lines = st.slider(text('log_lines'), 10, 1000, 100)
        
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Log file path
        log_file = os.path.join(logs_dir, "system.log")
        
        # Read logs if file exists
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()[-lines:]
            
            # Filter by log level
            if log_level != 'ALL':
                logs = [log for log in logs if log_level in log]
            
            log_content = "".join(logs)
        else:
            log_content = "No log file found. Logs will appear here as the system runs."
        
        st.text_area(text('logs'), value=log_content, height=300)
        
        # Log management
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(text('clear_logs')):
                if os.path.exists(log_file):
                    open(log_file, 'w').close()
                    st.success("Logs cleared")
                    st.rerun()
        
        with col2:
            if st.button(text('download_logs')):
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        log_data = f.read()
                    
                    st.download_button(
                        label="Download Log File",
                        data=log_data,
                        file_name="system_logs.log",
                        mime="text/plain"
                    )
    
    def display_performance_metrics(self):
        """Display performance metrics"""
        text = self.text
        
        st.subheader(text('performance_metrics'))
        
        # Get some database metrics
        try:
            # Table sizes
            size_query = """
                SELECT name as table_name, 
                       (pgsize/1024.0/1024.0) as size_mb
                FROM dbstat 
                WHERE name NOT LIKE 'sqlite_%'
                ORDER BY pgsize DESC
            """
            
            # Note: dbstat requires SQLite 3.15.0+
            # Fallback to simpler query
            table_query = """
                SELECT name as table_name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            
            tables = db.execute_query(table_query, fetch_all=True)
            
            metrics_data = []
            for table in tables:
                count_query = f"SELECT COUNT(*) as count FROM {table['table_name']}"
                count_result = db.execute_query(count_query, fetch_one=True)
                metrics_data.append({
                    'table_name': table['table_name'],
                    'row_count': count_result['count'] if count_result else 0
                })
            
            df = pd.DataFrame(metrics_data)
            
            # Display metrics
            total_tables = len(df)
            total_rows = df['row_count'].sum()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(text('total_tables'), total_tables)
            
            with col2:
                st.metric(text('total_rows'), total_rows)
            
            with col3:
                # Get database file size
                db_size = db.get_database_size()
                st.metric(text('database_size'), db_size)
            
            # Table sizes visualization
            st.subheader(text('table_sizes'))
            
            if len(df) > 0:
                fig = px.bar(
                    df,
                    x='table_name',
                    y='row_count',
                    title=text('row_count_by_table'),
                    labels={
                        'table_name': text('table_name'),
                        'row_count': text('row_count')
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error fetching performance metrics: {e}")
    
    def display_backup_restore(self):
        """Display backup and restore interface"""
        text = lang_manager.get_text
        
        st.subheader(text('backup_database'))
        
        # Backup section
        col1, col2 = st.columns(2)
        
        with col1:
            backup_name = st.text_input(
                text('backup_name'), 
                value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if st.button(text('create_backup'), type="primary"):
                with st.spinner(text('creating_backup')):
                    backup_path = f"{backup_name}.db"
                    success, message = db.backup_database(backup_path)
                    
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        with col2:
            # List existing backups
            backups_dir = "backups"
            if not os.path.exists(backups_dir):
                os.makedirs(backups_dir)
            
            backups = [f for f in os.listdir(backups_dir) if f.endswith('.db')]
            
            if backups:
                selected_backup = st.selectbox(
                    text('select_backup'),
                    backups
                )
                
                if st.button(text('restore_backup'), type="primary"):
                    if selected_backup:
                        with st.spinner(text('restoring_backup')):
                            backup_path = os.path.join(backups_dir, selected_backup)
                            success, message = db.restore_database(backup_path)
                            
                            if success:
                                st.success(f"✅ {message}")
                                st.info("Please refresh the page to use the restored database.")
                            else:
                                st.error(f"❌ {message}")
            else:
                st.info(text('no_backups_found'))
        
        # Backup history
        st.subheader(text('backup_history'))
        
        # Show backups in current directory
        current_backups = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.db')]
        current_backups.sort(reverse=True)
        
        if current_backups:
            for backup in current_backups[:5]:  # Show last 5 backups
                backup_path = backup
                backup_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
                size_mb = backup_size / (1024 * 1024)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(backup)
                with col2:
                    st.write(f"{size_mb:.2f} MB")
                with col3:
                    st.write("✅")
                with col4:
                    if st.button("Delete", key=f"del_{backup}"):
                        try:
                            os.remove(backup_path)
                            st.success(f"Deleted {backup}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {e}")
                st.divider()
        else:
            st.info(text('no_backup_history'))
    
    def run(self):
        """Run the main application"""
        text = self.text
        
        # Check authentication
        if not st.session_state.get('authenticated'):
            self.login_page()
            return
        
        # Display sidebar menu
        self.sidebar_menu()
        
        # Display selected page
        current_page = st.session_state.get('page', 'dashboard')
        
        # Developer console special handling
        if current_page == 'developer':
            if auth.has_permission(ROLES['DEVELOPER']):
                self.developer_console()
            else:
                st.warning(text('no_permission'))
                self.modules['dashboard'].display()
        else:
            # Display regular module
            if current_page in self.modules:
                self.modules[current_page].display()
            else:
                self.modules['dashboard'].display()
        
        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"© {datetime.now().year} {text('app_title')}")
        
        with col2:
            st.write(f"v1.0.0 | {text('user')}: {st.session_state.get('username', '')}")
        
        with col3:
            st.write(text('rights_reserved'))

def main():
    """Main function"""
    try:
        app = SchoolManagementSystem()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()