# modules/students.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import db

def show_students(translator, auth):
    """Display students management"""
    st.title(translator.t('students'))
    
    tab1, tab2, tab3 = st.tabs([
        "View Students",
        translator.t('add') + " Student",
        "Bulk Operations"
    ])
    
    with tab1:
        # Search and filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search by Name or ID", key="student_search")
        
        with col2:
            class_filter = st.selectbox(
                "Filter by Class",
                ["All"] + [c[0] for c in db.fetch_all("SELECT DISTINCT class_name FROM classes")]
            )
        
        with col3:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Active", "Inactive", "Graduated", "Transferred"]
            )
        
        # Build query
        query = '''
            SELECT s.*, c.class_name 
            FROM students s 
            LEFT JOIN classes c ON s.class_id = c.id 
            WHERE 1=1
        '''
        params = []
        
        if search_term:
            query += " AND (s.full_name LIKE ? OR s.student_id LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if class_filter != "All":
            query += " AND c.class_name = ?"
            params.append(class_filter)
        
        if status_filter != "All":
            query += " AND s.status = ?"
            params.append(status_filter)
        
        query += " ORDER BY s.created_at DESC"
        
        # Display students
        students_df = db.get_dataframe(query, params)
        
        if not students_df.empty:
            st.dataframe(
                students_df[['student_id', 'full_name', 'date_of_birth', 'gender', 
                           'class_name', 'status', 'admission_date']],
                use_container_width=True
            )
            
            # Export option
            if st.button("Export to CSV"):
                csv = students_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No students found")
    
    with tab2:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                student_id = st.text_input("Student ID*", value=f"STU{datetime.now().strftime('%Y%m%d%H%M%S')}")
                full_name = st.text_input("Full Name*")
                date_of_birth = st.date_input("Date of Birth*", min_value=date(2000, 1, 1))
                gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
                address = st.text_area("Address")
            
            with col2:
                parent_name = st.text_input("Parent/Guardian Name*")
                parent_phone = st.text_input("Parent Phone*")
                parent_email = st.text_input("Parent Email")
                
                # Get classes for selection
                classes = db.fetch_all("SELECT id, class_name FROM classes")
                class_options = {c['class_name']: c['id'] for c in classes}
                selected_class = st.selectbox("Class", list(class_options.keys()))
                
                admission_date = st.date_input("Admission Date*", value=date.today())
                status = st.selectbox("Status", ["Active", "Inactive", "Graduated", "Transferred"])
            
            if st.form_submit_button("Add Student"):
                if all([student_id, full_name, parent_name, parent_phone]):
                    query = '''
                        INSERT INTO students 
                        (student_id, full_name, date_of_birth, gender, address, 
                         parent_name, parent_phone, parent_email, class_id, admission_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    
                    class_id = class_options.get(selected_class)
                    
                    db.execute_query(query, (
                        student_id, full_name, date_of_birth, gender, address,
                        parent_name, parent_phone, parent_email, class_id, admission_date, status
                    ))
                    
                    st.success("Student added successfully!")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab3:
        st.subheader("Bulk Operations")
        
        # Bulk import
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:", df.head())
            
            if st.button("Import Students"):
                success_count = 0
                for _, row in df.iterrows():
                    try:
                        # Generate student ID if not provided
                        student_id = row.get('student_id', f"STU{datetime.now().strftime('%Y%m%d%H%M%S')}{success_count}")
                        
                        query = '''
                            INSERT INTO students 
                            (student_id, full_name, date_of_birth, gender, address, 
                             parent_name, parent_phone, parent_email, admission_date, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        '''
                        
                        db.execute_query(query, (
                            student_id,
                            row.get('full_name', ''),
                            row.get('date_of_birth', date.today()),
                            row.get('gender', 'Other'),
                            row.get('address', ''),
                            row.get('parent_name', ''),
                            row.get('parent_phone', ''),
                            row.get('parent_email', ''),
                            row.get('admission_date', date.today()),
                            row.get('status', 'Active')
                        ))
                        success_count += 1
                    except Exception as e:
                        st.error(f"Error importing row {_}: {e}")
                
                st.success(f"Successfully imported {success_count} students")