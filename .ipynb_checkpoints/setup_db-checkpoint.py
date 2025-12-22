# setup_db.py
from database import db
import streamlit as st

def setup_database():
    """Initialize database with sample data for demo"""
    st.title("Database Setup")
    
    if st.button("Initialize Database with Sample Data"):
        try:
            # Sample data for demonstration
            
            # Add sample classes
            classes = [
                ('Grade 1 A', 'Grade 1', 'A', 30, None, '2024-2025'),
                ('Grade 2 B', 'Grade 2', 'B', 30, None, '2024-2025'),
                ('Grade 3 C', 'Grade 3', 'C', 30, None, '2024-2025'),
                ('Grade 4 A', 'Grade 4', 'A', 30, None, '2024-2025'),
                ('Grade 5 B', 'Grade 5', 'B', 30, None, '2024-2025')
            ]
            
            for class_data in classes:
                db.execute_query('''
                    INSERT INTO classes (class_name, grade_level, section, capacity, class_teacher_id, academic_year)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', class_data)
            
            # Add sample teachers
            teachers = [
                ('TCH001', 'John Smith', '1980-05-15', 'Male', '123 Main St', '555-0101', 'john@school.com', 'M.Ed', 'Mathematics', '2020-01-15', 'Active'),
                ('TCH002', 'Sarah Johnson', '1985-08-22', 'Female', '456 Oak Ave', '555-0102', 'sarah@school.com', 'M.Sc', 'Science', '2019-03-10', 'Active'),
                ('TCH003', 'Robert Brown', '1975-11-30', 'Male', '789 Pine Rd', '555-0103', 'robert@school.com', 'B.Ed', 'English', '2018-07-22', 'Active'),
                ('TCH004', 'Emily Davis', '1990-02-14', 'Female', '321 Elm St', '555-0104', 'emily@school.com', 'M.A', 'History', '2021-09-05', 'Active')
            ]
            
            for teacher in teachers:
                db.execute_query('''
                    INSERT INTO teachers 
                    (teacher_id, full_name, date_of_birth, gender, address, phone, email, 
                     qualification, specialization, hire_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', teacher)
            
            # Add sample students
            import random
            from datetime import datetime, timedelta
            
            first_names = ['Ali', 'Omar', 'Fatima', 'Aisha', 'Mohammed', 'Sarah', 'Ahmed', 'Layla', 'Youssef', 'Mariam']
            last_names = ['Khan', 'Al-Mansoor', 'Abdullah', 'Hassan', 'Farid', 'Naser', 'Zahra', 'Rashid', 'Salem', 'Qureshi']
            
            for i in range(1, 51):
                student_id = f"STU{1000 + i}"
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                full_name = f"{first_name} {last_name}"
                
                # Random date of birth between 2010 and 2015
                dob_year = random.randint(2010, 2015)
                dob_month = random.randint(1, 12)
                dob_day = random.randint(1, 28)
                date_of_birth = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"
                
                gender = random.choice(['Male', 'Female'])
                class_id = random.randint(1, 5)
                
                # Random admission date in the last 3 years
                admission_date = datetime.now() - timedelta(days=random.randint(0, 1000))
                
                db.execute_query('''
                    INSERT INTO students 
                    (student_id, full_name, date_of_birth, gender, class_id, admission_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_id, full_name, date_of_birth, gender, class_id, admission_date.strftime('%Y-%m-%d'), 'Active'))
            
            st.success("Database initialized successfully with sample data!")
            st.info(f"Added: 5 classes, 4 teachers, 50 students")
            
        except Exception as e:
            st.error(f"Error initializing database: {e}")

if __name__ == "__main__":
    setup_database()