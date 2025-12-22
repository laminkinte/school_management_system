# database.py
import sqlite3
from sqlite3 import Error
from datetime import datetime, date
import pandas as pd
import streamlit as st

class Database:
    def __init__(self, db_file='school_management.db'):
        self.db_file = db_file
        self.conn = None
        self.create_connection()
        self.create_tables()
    
    def create_connection(self):
        """Create a database connection"""
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            return self.conn
        except Error as e:
            st.error(f"Error connecting to database: {e}")
            return None
    
    def create_tables(self):
        """Create all necessary tables"""
        try:
            cursor = self.conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    date_of_birth DATE,
                    gender TEXT,
                    address TEXT,
                    parent_name TEXT,
                    parent_phone TEXT,
                    parent_email TEXT,
                    class_id INTEGER,
                    admission_date DATE,
                    status TEXT DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes (id)
                )
            ''')
            
            # Teachers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    date_of_birth DATE,
                    gender TEXT,
                    address TEXT,
                    phone TEXT,
                    email TEXT,
                    qualification TEXT,
                    specialization TEXT,
                    hire_date DATE,
                    status TEXT DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Classes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT NOT NULL,
                    grade_level TEXT,
                    section TEXT,
                    capacity INTEGER,
                    class_teacher_id INTEGER,
                    academic_year TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_teacher_id) REFERENCES teachers (id)
                )
            ''')
            
            # Subjects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_code TEXT UNIQUE NOT NULL,
                    subject_name TEXT NOT NULL,
                    description TEXT,
                    class_id INTEGER,
                    teacher_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
                )
            ''')
            
            # Attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    class_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    status TEXT NOT NULL,
                    remarks TEXT,
                    recorded_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    FOREIGN KEY (recorded_by) REFERENCES users (id),
                    UNIQUE(student_id, date)
                )
            ''')
            
            # Teacher Attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teacher_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    status TEXT NOT NULL,
                    remarks TEXT,
                    recorded_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES teachers (id),
                    FOREIGN KEY (recorded_by) REFERENCES users (id),
                    UNIQUE(teacher_id, date)
                )
            ''')
            
            # Timetable table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timetable (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    day_of_week TEXT NOT NULL,
                    period INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    room TEXT,
                    academic_year TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    FOREIGN KEY (subject_id) REFERENCES subjects (id),
                    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
                )
            ''')
            
            # Results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    class_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    exam_type TEXT,
                    marks_obtained REAL,
                    total_marks REAL,
                    percentage REAL,
                    grade TEXT,
                    remarks TEXT,
                    exam_date DATE,
                    recorded_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    FOREIGN KEY (subject_id) REFERENCES subjects (id),
                    FOREIGN KEY (recorded_by) REFERENCES users (id)
                )
            ''')
            
            # Fees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    fee_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    due_date DATE NOT NULL,
                    paid_amount REAL DEFAULT 0,
                    payment_date DATE,
                    status TEXT DEFAULT 'Unpaid',
                    payment_method TEXT,
                    transaction_id TEXT,
                    remarks TEXT,
                    collected_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (collected_by) REFERENCES users (id)
                )
            ''')
            
            # System Configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT,
                    config_type TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Admission Applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admission_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT UNIQUE NOT NULL,
                    student_name TEXT NOT NULL,
                    date_of_birth DATE,
                    gender TEXT,
                    parent_name TEXT,
                    parent_phone TEXT,
                    parent_email TEXT,
                    address TEXT,
                    applied_for_class TEXT,
                    application_date DATE DEFAULT CURRENT_DATE,
                    status TEXT DEFAULT 'Pending',
                    remarks TEXT,
                    processed_by INTEGER,
                    processed_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (processed_by) REFERENCES users (id)
                )
            ''')
            
            # Grading System table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grading_system (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grade TEXT NOT NULL,
                    min_percentage REAL NOT NULL,
                    max_percentage REAL NOT NULL,
                    grade_point REAL,
                    description TEXT,
                    academic_year TEXT
                )
            ''')
            
            self.conn.commit()
            
            # Insert default users if not exists
            self.create_default_users()
            
        except Error as e:
            st.error(f"Error creating tables: {e}")
    
    def create_default_users(self):
        """Create default users for the system"""
        try:
            cursor = self.conn.cursor()
            
            # Check if developer exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'developer'")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO users (username, password, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('developer', 'dev123', 'System Developer', 'developer@school.com', 'developer'))
            
            # Check if super admin exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'superadmin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO users (username, password, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('superadmin', 'admin123', 'Super Administrator', 'superadmin@school.com', 'super_admin'))
            
            self.conn.commit()
            
        except Error as e:
            st.error(f"Error creating default users: {e}")
    
    def execute_query(self, query, params=()):
        """Execute a query"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor.lastrowid
        except Error as e:
            st.error(f"Error executing query: {e}")
            return None
    
    def fetch_all(self, query, params=()):
        """Fetch all rows from a query"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching data: {e}")
            return []
    
    def fetch_one(self, query, params=()):
        """Fetch one row from a query"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            st.error(f"Error fetching data: {e}")
            return None
    
    def get_dataframe(self, query, params=()):
        """Get query results as pandas DataFrame"""
        try:
            return pd.read_sql_query(query, self.conn, params=params)
        except Error as e:
            st.error(f"Error getting dataframe: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()

# Global database instance
db = Database()