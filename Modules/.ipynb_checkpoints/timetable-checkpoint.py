# modules/timetable.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database import db

def show_timetable(translator, auth):
    """Display timetable management"""
    st.title(translator.t('timetable'))
    
    tab1, tab2, tab3 = st.tabs(["View Timetable", "Manage Timetable", "Generate Timetable"])
    
    with tab1:
        # Class selector
        classes = db.fetch_all("SELECT id, class_name FROM classes")
        class_options = {c['class_name']: c['id'] for c in classes}
        selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
        
        if selected_class_name:
            class_id = class_options[selected_class_name]
            
            # Get timetable for selected class
            timetable_df = db.get_dataframe('''
                SELECT tt.day_of_week, tt.period, tt.start_time, tt.end_time,
                       s.subject_name, t.full_name as teacher_name, tt.room
                FROM timetable tt
                LEFT JOIN subjects s ON tt.subject_id = s.id
                LEFT JOIN teachers t ON tt.teacher_id = t.id
                WHERE tt.class_id = ?
                ORDER BY 
                    CASE tt.day_of_week
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    tt.period
            ''', (class_id,))
            
            if not timetable_df.empty:
                # Pivot table for better display
                pivot_df = timetable_df.pivot_table(
                    index='period',
                    columns='day_of_week',
                    values=['subject_name', 'teacher_name', 'room'],
                    aggfunc='first'
                )
                
                # Display as table
                st.dataframe(pivot_df, use_container_width=True)
            else:
                st.info(f"No timetable found for {selected_class_name}")
    
    with tab2:
        st.subheader("Add/Edit Timetable Entry")
        
        with st.form("timetable_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Class selection
                classes = db.fetch_all("SELECT id, class_name FROM classes")
                class_options = {c['class_name']: c['id'] for c in classes}
                selected_class_name = st.selectbox("Class*", list(class_options.keys()))
                
                # Day selection
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                day_of_week = st.selectbox("Day of Week*", days)
                
                # Period selection
                period = st.number_input("Period Number*", min_value=1, max_value=10, value=1)
                
                # Time selection
                col_time1, col_time2 = st.columns(2)
                with col_time1:
                    start_time = st.text_input("Start Time*", value="08:00")
                with col_time2:
                    end_time = st.text_input("End Time*", value="08:45")
            
            with col2:
                # Subject selection
                subjects = db.fetch_all("SELECT id, subject_name FROM subjects")
                subject_options = {s['subject_name']: s['id'] for s in subjects}
                selected_subject_name = st.selectbox("Subject*", list(subject_options.keys()))
                
                # Teacher selection
                teachers = db.fetch_all("SELECT id, full_name FROM teachers WHERE status = 'Active'")
                teacher_options = {t['full_name']: t['id'] for t in teachers}
                selected_teacher_name = st.selectbox("Teacher*", list(teacher_options.keys()))
                
                room = st.text_input("Room Number", placeholder="e.g., Room 101")
                academic_year = st.text_input("Academic Year", value="2024-2025")
            
            if st.form_submit_button("Save Timetable Entry"):
                if all([selected_class_name, day_of_week, period, start_time, end_time, 
                       selected_subject_name, selected_teacher_name]):
                    
                    class_id = class_options[selected_class_name]
                    subject_id = subject_options[selected_subject_name]
                    teacher_id = teacher_options[selected_teacher_name]
                    
                    # Check if entry already exists
                    existing = db.fetch_one('''
                        SELECT id FROM timetable 
                        WHERE class_id = ? AND day_of_week = ? AND period = ?
                    ''', (class_id, day_of_week, period))
                    
                    if existing:
                        # Update existing entry
                        query = '''
                            UPDATE timetable 
                            SET subject_id = ?, teacher_id = ?, start_time = ?, 
                                end_time = ?, room = ?, academic_year = ?
                            WHERE id = ?
                        '''
                        db.execute_query(query, (
                            subject_id, teacher_id, start_time, end_time,
                            room, academic_year, existing['id']
                        ))
                        st.success("Timetable entry updated!")
                    else:
                        # Insert new entry
                        query = '''
                            INSERT INTO timetable 
                            (class_id, day_of_week, period, subject_id, teacher_id, 
                             start_time, end_time, room, academic_year)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        '''
                        db.execute_query(query, (
                            class_id, day_of_week, period, subject_id, teacher_id,
                            start_time, end_time, room, academic_year
                        ))
                        st.success("Timetable entry added!")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab3:
        st.subheader("Generate Timetable")
        
        # Class selector for generation
        classes = db.fetch_all("SELECT id, class_name FROM classes")
        class_options = {c['class_name']: c['id'] for c in classes}
        selected_class_name = st.selectbox("Select Class for Generation", list(class_options.keys()))
        
        if selected_class_name and st.button("Generate Timetable Template"):
            class_id = class_options[selected_class_name]
            
            # Get subjects for this class
            subjects = db.fetch_all('''
                SELECT s.id, s.subject_name 
                FROM subjects s
                WHERE s.class_id = ?
            ''', (class_id,))
            
            if subjects:
                # Create a template dataframe
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                periods = range(1, 9)  # 8 periods per day
                
                template_data = []
                for day in days:
                    for period in periods:
                        template_data.append({
                            'Class': selected_class_name,
                            'Day': day,
                            'Period': period,
                            'Subject': '',
                            'Teacher': '',
                            'Start Time': f"{8 + period - 1}:00",
                            'End Time': f"{8 + period}:00",
                            'Room': ''
                        })
                
                template_df = pd.DataFrame(template_data)
                
                # Display and offer download
                st.dataframe(template_df, use_container_width=True)
                
                csv = template_df.to_csv(index=False)
                st.download_button(
                    label="Download Template",
                    data=csv,
                    file_name=f"timetable_template_{selected_class_name}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No subjects found for {selected_class_name}. Please add subjects first.")