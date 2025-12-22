# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import db

def show_attendance(translator, auth):
    """Display attendance management"""
    st.title(translator.t('attendance'))
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Student Attendance",
        "Teacher Attendance",
        "Mark Attendance",
        "Reports"
    ])
    
    with tab1:
        # Date selector
        selected_date = st.date_input("Select Date", value=date.today())
        
        # Class selector
        classes = db.fetch_all("SELECT id, class_name FROM classes")
        class_options = {c['class_name']: c['id'] for c in classes}
        selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
        
        if selected_class_name and selected_date:
            class_id = class_options[selected_class_name]
            
            # Get attendance for selected date and class
            attendance_df = db.get_dataframe('''
                SELECT s.full_name, s.student_id, a.status, a.remarks
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id 
                    AND a.date = ? 
                    AND a.class_id = ?
                WHERE s.class_id = ? AND s.status = 'Active'
                ORDER BY s.full_name
            ''', (selected_date, class_id, class_id))
            
            if not attendance_df.empty:
                st.dataframe(attendance_df, use_container_width=True)
            else:
                st.info(f"No attendance records found for {selected_date}")
    
    with tab2:
        selected_date = st.date_input("Select Date for Teacher Attendance", value=date.today())
        
        if selected_date:
            attendance_df = db.get_dataframe('''
                SELECT t.full_name, t.teacher_id, ta.status, ta.remarks
                FROM teachers t
                LEFT JOIN teacher_attendance ta ON t.id = ta.teacher_id 
                    AND ta.date = ?
                WHERE t.status = 'Active'
                ORDER BY t.full_name
            ''', (selected_date,))
            
            if not attendance_df.empty:
                st.dataframe(attendance_df, use_container_width=True)
            else:
                st.info(f"No teacher attendance records found for {selected_date}")
    
    with tab3:
        st.subheader(translator.t('mark_attendance'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            attendance_type = st.radio(
                "Attendance Type",
                ["Student", "Teacher"],
                horizontal=True
            )
            
            if attendance_type == "Student":
                classes = db.fetch_all("SELECT id, class_name FROM classes")
                class_options = {c['class_name']: c['id'] for c in classes}
                selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
                class_id = class_options[selected_class_name]
            
            selected_date = st.date_input("Attendance Date", value=date.today())
        
        with col2:
            st.write("**Status Options:**")
            status_options = ["Present", "Absent", "Late", "Excused"]
            default_status = st.selectbox("Default Status", status_options)
        
        if attendance_type == "Student" and selected_class_name:
            # Get students for the selected class
            students = db.fetch_all('''
                SELECT id, student_id, full_name 
                FROM students 
                WHERE class_id = ? AND status = 'Active'
                ORDER BY full_name
            ''', (class_id,))
            
            if students:
                st.markdown("---")
                st.write(f"**Mark Attendance for {selected_class_name} - {selected_date}**")
                
                attendance_data = []
                for student in students:
                    col1, col2, col3 = st.columns([3, 2, 3])
                    
                    with col1:
                        st.write(f"**{student['full_name']}** ({student['student_id']})")
                    
                    with col2:
                        status = st.selectbox(
                            "Status",
                            status_options,
                            index=status_options.index(default_status),
                            key=f"status_{student['id']}"
                        )
                    
                    with col3:
                        remarks = st.text_input("Remarks", key=f"remarks_{student['id']}")
                    
                    attendance_data.append({
                        'student_id': student['id'],
                        'status': status,
                        'remarks': remarks
                    })
                
                if st.button("Save Attendance", type="primary"):
                    success_count = 0
                    for data in attendance_data:
                        # Check if attendance already exists for this date
                        existing = db.fetch_one('''
                            SELECT id FROM attendance 
                            WHERE student_id = ? AND date = ?
                        ''', (data['student_id'], selected_date))
                        
                        if existing:
                            # Update existing record
                            query = '''
                                UPDATE attendance 
                                SET status = ?, remarks = ?, recorded_by = ?
                                WHERE id = ?
                            '''
                            db.execute_query(query, (
                                data['status'], data['remarks'], 
                                auth.get_current_user()['id'],
                                existing['id']
                            ))
                        else:
                            # Insert new record
                            query = '''
                                INSERT INTO attendance 
                                (student_id, class_id, date, status, remarks, recorded_by)
                                VALUES (?, ?, ?, ?, ?, ?)
                            '''
                            db.execute_query(query, (
                                data['student_id'], class_id, selected_date,
                                data['status'], data['remarks'],
                                auth.get_current_user()['id']
                            ))
                        success_count += 1
                    
                    st.success(f"Attendance saved for {success_count} students!")
    
    with tab4:
        st.subheader("Attendance Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            end_date = st.date_input("End Date", value=date.today())
        
        with col2:
            report_type = st.selectbox(
                "Report Type",
                ["Daily Summary", "Student-wise", "Class-wise", "Monthly Summary"]
            )
        
        if st.button("Generate Report"):
            if report_type == "Daily Summary":
                report_df = db.get_dataframe('''
                    SELECT date, 
                           COUNT(*) as total,
                           SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                           SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                           ROUND(SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as attendance_percentage
                    FROM attendance
                    WHERE date BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                ''', (start_date, end_date))
                
                if not report_df.empty:
                    st.dataframe(report_df, use_container_width=True)
                    
                    # Chart
                    import plotly.express as px
                    fig = px.line(report_df, x='date', y='attendance_percentage',
                                 title='Daily Attendance Percentage')
                    st.plotly_chart(fig, use_container_width=True)