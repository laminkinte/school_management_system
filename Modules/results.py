# modules/results.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from database import db

def show_results(translator, auth):
    """Display results management"""
    st.title(translator.t('results'))
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "View Results",
        "Add Results",
        "Bulk Upload",
        "Grading System"
    ])
    
    with tab1:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            classes = db.fetch_all("SELECT id, class_name FROM classes")
            class_options = {c['class_name']: c['id'] for c in classes}
            selected_class_name = st.selectbox("Select Class", ["All"] + list(class_options.keys()))
        
        with col2:
            exam_types = db.fetch_all("SELECT DISTINCT exam_type FROM results")
            exam_type_options = ["All"] + [e[0] for e in exam_types if e[0]]
            selected_exam_type = st.selectbox("Exam Type", exam_type_options)
        
        with col3:
            student_search = st.text_input("Search Student")
        
        # Build query
        query = '''
            SELECT r.*, s.full_name as student_name, s.student_id,
                   c.class_name, sub.subject_name
            FROM results r
            JOIN students s ON r.student_id = s.id
            JOIN classes c ON r.class_id = c.id
            JOIN subjects sub ON r.subject_id = sub.id
            WHERE 1=1
        '''
        params = []
        
        if selected_class_name != "All":
            query += " AND c.class_name = ?"
            params.append(selected_class_name)
        
        if selected_exam_type != "All":
            query += " AND r.exam_type = ?"
            params.append(selected_exam_type)
        
        if student_search:
            query += " AND (s.full_name LIKE ? OR s.student_id LIKE ?)"
            params.extend([f"%{student_search}%", f"%{student_search}%"])
        
        query += " ORDER BY r.exam_date DESC, s.full_name"
        
        results_df = db.get_dataframe(query, params)
        
        if not results_df.empty:
            # Calculate statistics
            total_students = results_df['student_id'].nunique()
            avg_percentage = results_df['percentage'].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Students", total_students)
            with col2:
                st.metric("Average Percentage", f"{avg_percentage:.2f}%")
            
            st.dataframe(
                results_df[['student_name', 'student_id', 'class_name', 'subject_name',
                          'exam_type', 'marks_obtained', 'total_marks', 'percentage', 'grade']],
                use_container_width=True
            )
        else:
            st.info("No results found")
    
    with tab2:
        with st.form("add_result_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Student selection
                students = db.fetch_all('''
                    SELECT s.id, s.full_name, s.student_id, c.class_name
                    FROM students s
                    JOIN classes c ON s.class_id = c.id
                    WHERE s.status = 'Active'
                    ORDER BY s.full_name
                ''')
                student_options = {f"{s['full_name']} ({s['student_id']}) - {s['class_name']}": s['id'] for s in students}
                selected_student = st.selectbox("Select Student*", list(student_options.keys()))
                
                # Subject selection
                if selected_student:
                    student_id = student_options[selected_student]
                    # Get student's class
                    student_class = db.fetch_one(
                        "SELECT class_id FROM students WHERE id = ?",
                        (student_id,)
                    )
                    
                    if student_class:
                        subjects = db.fetch_all('''
                            SELECT id, subject_name FROM subjects
                            WHERE class_id = ?
                        ''', (student_class['class_id'],))
                        subject_options = {s['subject_name']: s['id'] for s in subjects}
                        selected_subject = st.selectbox("Select Subject*", list(subject_options.keys()))
            
            with col2:
                exam_type = st.selectbox(
                    "Exam Type*",
                    ["Midterm", "Final", "Quiz", "Assignment", "Project"]
                )
                exam_date = st.date_input("Exam Date*", value=date.today())
                marks_obtained = st.number_input("Marks Obtained*", min_value=0.0, max_value=200.0, value=0.0)
                total_marks = st.number_input("Total Marks*", min_value=1.0, max_value=200.0, value=100.0)
                remarks = st.text_area("Remarks")
            
            if st.form_submit_button("Add Result"):
                if all([selected_student, selected_subject, exam_type, marks_obtained, total_marks]):
                    percentage = (marks_obtained / total_marks) * 100
                    
                    # Determine grade based on percentage
                    grade = "F"
                    if percentage >= 90:
                        grade = "A+"
                    elif percentage >= 80:
                        grade = "A"
                    elif percentage >= 70:
                        grade = "B"
                    elif percentage >= 60:
                        grade = "C"
                    elif percentage >= 50:
                        grade = "D"
                    elif percentage >= 40:
                        grade = "E"
                    
                    query = '''
                        INSERT INTO results 
                        (student_id, class_id, subject_id, exam_type, marks_obtained,
                         total_marks, percentage, grade, remarks, exam_date, recorded_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    
                    student_id = student_options[selected_student]
                    subject_id = subject_options[selected_subject]
                    
                    # Get class_id from student
                    student_data = db.fetch_one(
                        "SELECT class_id FROM students WHERE id = ?",
                        (student_id,)
                    )
                    
                    db.execute_query(query, (
                        student_id, student_data['class_id'], subject_id, exam_type,
                        marks_obtained, total_marks, percentage, grade, remarks,
                        exam_date, auth.get_current_user()['id']
                    ))
                    
                    st.success("Result added successfully!")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab3:
        st.subheader("Bulk Results Upload")
        
        uploaded_file = st.file_uploader("Upload CSV file with results", type=['csv'])
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:", df.head())
            
            required_columns = ['student_id', 'subject_name', 'exam_type', 'marks_obtained', 'total_marks']
            
            if all(col in df.columns for col in required_columns):
                if st.button("Import Results"):
                    success_count = 0
                    errors = []
                    
                    for idx, row in df.iterrows():
                        try:
                            # Get student ID
                            student = db.fetch_one(
                                "SELECT id, class_id FROM students WHERE student_id = ?",
                                (row['student_id'],)
                            )
                            
                            if not student:
                                errors.append(f"Row {idx}: Student {row['student_id']} not found")
                                continue
                            
                            # Get subject ID
                            subject = db.fetch_one(
                                "SELECT id FROM subjects WHERE subject_name = ? AND class_id = ?",
                                (row['subject_name'], student['class_id'])
                            )
                            
                            if not subject:
                                errors.append(f"Row {idx}: Subject {row['subject_name']} not found for student's class")
                                continue
                            
                            percentage = (row['marks_obtained'] / row['total_marks']) * 100
                            
                            # Determine grade
                            grade = "F"
                            if percentage >= 90:
                                grade = "A+"
                            elif percentage >= 80:
                                grade = "A"
                            elif percentage >= 70:
                                grade = "B"
                            elif percentage >= 60:
                                grade = "C"
                            elif percentage >= 50:
                                grade = "D"
                            elif percentage >= 40:
                                grade = "E"
                            
                            query = '''
                                INSERT INTO results 
                                (student_id, class_id, subject_id, exam_type, marks_obtained,
                                 total_marks, percentage, grade, exam_date, recorded_by)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            '''
                            
                            db.execute_query(query, (
                                student['id'], student['class_id'], subject['id'],
                                row['exam_type'], row['marks_obtained'], row['total_marks'],
                                percentage, grade, date.today(), auth.get_current_user()['id']
                            ))
                            
                            success_count += 1
                            
                        except Exception as e:
                            errors.append(f"Row {idx}: {str(e)}")
                    
                    st.success(f"Successfully imported {success_count} results")
                    
                    if errors:
                        st.warning(f"Errors ({len(errors)}):")
                        for error in errors[:10]:  # Show first 10 errors
                            st.write(error)
            else:
                st.error(f"CSV must contain columns: {', '.join(required_columns)}")
    
    with tab4:
        st.subheader("Grading System Configuration")
        
        # View current grading system
        grading_df = db.get_dataframe("SELECT * FROM grading_system ORDER BY min_percentage DESC")
        
        if not grading_df.empty:
            st.dataframe(grading_df, use_container_width=True)
        
        # Add new grade
        with st.form("add_grade_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                grade = st.text_input("Grade*", placeholder="e.g., A+, A, B")
                min_percentage = st.number_input("Min Percentage*", min_value=0.0, max_value=100.0, value=90.0)
            
            with col2:
                max_percentage = st.number_input("Max Percentage*", min_value=0.0, max_value=100.0, value=100.0)
                grade_point = st.number_input("Grade Point", min_value=0.0, max_value=4.0, value=4.0)
            
            with col3:
                description = st.text_input("Description", placeholder="e.g., Excellent")
                academic_year = st.text_input("Academic Year", value="2024-2025")
            
            if st.form_submit_button("Add Grade"):
                if grade and min_percentage <= max_percentage:
                    query = '''
                        INSERT INTO grading_system 
                        (grade, min_percentage, max_percentage, grade_point, description, academic_year)
                        VALUES (?, ?, ?, ?, ?, ?)
                    '''
                    
                    db.execute_query(query, (
                        grade, min_percentage, max_percentage, grade_point,
                        description, academic_year
                    ))
                    
                    st.success("Grade added to grading system!")
                    st.rerun()
                else:
                    st.error("Please fill required fields correctly")