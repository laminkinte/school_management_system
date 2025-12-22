# modules/classes.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database import db

def show_classes(translator, auth):
    """Display classes management"""
    st.title(translator.t('classes'))
    
    tab1, tab2 = st.tabs(["View Classes", "Add Class"])
    
    with tab1:
        classes_df = db.get_dataframe('''
            SELECT c.*, t.full_name as class_teacher_name,
                   COUNT(s.id) as student_count
            FROM classes c
            LEFT JOIN teachers t ON c.class_teacher_id = t.id
            LEFT JOIN students s ON s.class_id = c.id
            GROUP BY c.id
            ORDER BY c.class_name
        ''')
        
        if not classes_df.empty:
            for _, row in classes_df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.subheader(row['class_name'])
                    st.write(f"**Grade Level:** {row.get('grade_level', 'N/A')}")
                    st.write(f"**Section:** {row.get('section', 'N/A')}")
                    st.write(f"**Class Teacher:** {row.get('class_teacher_name', 'Not Assigned')}")
                    st.write(f"**Students:** {row['student_count']} / {row.get('capacity', 'Unlimited')}")
                    st.write(f"**Academic Year:** {row.get('academic_year', 'N/A')}")
                
                with col2:
                    if st.button("Edit", key=f"edit_class_{row['id']}"):
                        st.session_state.edit_class = row['id']
                
                with col3:
                    if st.button("Delete", key=f"delete_class_{row['id']}"):
                        if st.confirm("Are you sure you want to delete this class?"):
                            # Check if class has students
                            student_count = db.fetch_one(
                                "SELECT COUNT(*) FROM students WHERE class_id = ?",
                                (row['id'],)
                            )[0]
                            
                            if student_count == 0:
                                db.execute_query("DELETE FROM classes WHERE id = ?", (row['id'],))
                                st.success("Class deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Cannot delete class with {student_count} students. Transfer students first.")
                
                st.markdown("---")
        else:
            st.info("No classes found")
    
    with tab2:
        with st.form("add_class_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                class_name = st.text_input("Class Name*", placeholder="e.g., Grade 1 A")
                grade_level = st.selectbox(
                    "Grade Level",
                    ["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", 
                     "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", 
                     "Grade 10", "Grade 11", "Grade 12"]
                )
                section = st.text_input("Section", placeholder="e.g., A, B, C")
                capacity = st.number_input("Class Capacity", min_value=1, max_value=100, value=30)
            
            with col2:
                # Get available teachers
                teachers = db.fetch_all("SELECT id, full_name FROM teachers WHERE status = 'Active'")
                teacher_options = {t['full_name']: t['id'] for t in teachers}
                teacher_options["Not Assigned"] = None
                
                class_teacher = st.selectbox("Class Teacher", list(teacher_options.keys()))
                academic_year = st.text_input("Academic Year*", value="2024-2025")
                description = st.text_area("Description")
            
            if st.form_submit_button("Add Class"):
                if class_name and academic_year:
                    class_teacher_id = teacher_options.get(class_teacher)
                    
                    query = '''
                        INSERT INTO classes 
                        (class_name, grade_level, section, capacity, class_teacher_id, academic_year)
                        VALUES (?, ?, ?, ?, ?, ?)
                    '''
                    
                    db.execute_query(query, (
                        class_name, grade_level, section, capacity,
                        class_teacher_id, academic_year
                    ))
                    
                    st.success("Class added successfully!")
                else:
                    st.error("Please fill all required fields (*)")