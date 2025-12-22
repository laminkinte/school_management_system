# modules/teachers.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import db

def show_teachers(translator, auth):
    """Display teachers management"""
    st.title(translator.t('teachers'))
    
    tab1, tab2 = st.tabs(["View Teachers", "Add Teacher"])
    
    with tab1:
        # Search and filter
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search by Name or ID", key="teacher_search")
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Active", "Inactive", "Retired", "Resigned"]
            )
        
        # Build query
        query = "SELECT * FROM teachers WHERE 1=1"
        params = []
        
        if search_term:
            query += " AND (full_name LIKE ? OR teacher_id LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)
        
        query += " ORDER BY created_at DESC"
        
        # Display teachers
        teachers_df = db.get_dataframe(query, params)
        
        if not teachers_df.empty:
            # Add action buttons
            teachers_df['Actions'] = ""
            
            for idx, row in teachers_df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{row['full_name']}** ({row['teacher_id']})")
                    st.write(f"📧 {row.get('email', 'N/A')} | 📱 {row.get('phone', 'N/A')}")
                    st.write(f"Specialization: {row.get('specialization', 'N/A')}")
                    st.write(f"Status: {row['status']}")
                
                with col2:
                    if st.button("Edit", key=f"edit_{row['id']}"):
                        st.session_state.edit_teacher = row['id']
                
                with col3:
                    if st.button("Delete", key=f"delete_{row['id']}"):
                        if st.confirm("Are you sure you want to delete this teacher?"):
                            db.execute_query("DELETE FROM teachers WHERE id = ?", (row['id'],))
                            st.success("Teacher deleted successfully!")
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info("No teachers found")
    
    with tab2:
        with st.form("add_teacher_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                teacher_id = st.text_input("Teacher ID*", value=f"TCH{datetime.now().strftime('%Y%m%d%H%M%S')}")
                full_name = st.text_input("Full Name*")
                date_of_birth = st.date_input("Date of Birth", min_value=date(1950, 1, 1))
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                address = st.text_area("Address")
            
            with col2:
                phone = st.text_input("Phone*")
                email = st.text_input("Email*")
                qualification = st.text_input("Qualification*")
                specialization = st.text_input("Specialization*")
                hire_date = st.date_input("Hire Date*", value=date.today())
                status = st.selectbox("Status", ["Active", "Inactive", "Retired", "Resigned"])
            
            if st.form_submit_button("Add Teacher"):
                if all([teacher_id, full_name, phone, email, qualification, specialization]):
                    query = '''
                        INSERT INTO teachers 
                        (teacher_id, full_name, date_of_birth, gender, address, 
                         phone, email, qualification, specialization, hire_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    
                    db.execute_query(query, (
                        teacher_id, full_name, date_of_birth, gender, address,
                        phone, email, qualification, specialization, hire_date, status
                    ))
                    
                    st.success("Teacher added successfully!")
                else:
                    st.error("Please fill all required fields (*)")