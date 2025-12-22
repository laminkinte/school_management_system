import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import db
from auth import auth
from utils import lang_manager, validate_email, validate_phone
from config import ROLES
import random
import string

class AdmissionModule:
    """Student admission module"""
    
    def display(self):
        """Display admission interface"""
        text = lang_manager.get_text
        
        st.title(text('admission'))
        
        # Tabs for different operations
        tab1, tab2, tab3, tab4 = st.tabs([
            text('new_admission'),
            text('admission_records'),
            text('pending_applications'),
            text('admission_reports')
        ])
        
        with tab1:
            self.display_new_admission_form()
        
        with tab2:
            self.display_admission_records()
        
        with tab3:
            self.display_pending_applications()
        
        with tab4:
            self.display_admission_reports()
    
    def generate_admission_number(self, year=None):
        """Generate unique admission number"""
        if year is None:
            year = datetime.now().year
        
        # Try to generate unique number
        for _ in range(10):
            # Format: ADM-YYYY-XXXXX
            random_part = ''.join(random.choices(string.digits, k=5))
            admission_number = f"ADM-{year}-{random_part}"
            
            # Check if exists
            check_query = "SELECT student_id FROM students WHERE admission_number = %s"
            existing = db.execute_query(check_query, (admission_number,), fetch_one=True)
            
            if not existing:
                return admission_number
        
        # Fallback with timestamp
        timestamp = int(datetime.now().timestamp())
        return f"ADM-{year}-{timestamp % 100000:05d}"
    
    def display_new_admission_form(self):
        """Display form for new student admission"""
        text = lang_manager.get_text
        
        if not auth.has_permission(ROLES['ADMIN']):
            st.warning(text('no_permission'))
            return
        
        st.subheader(text('new_student_admission'))
        
        with st.form("admission_form"):
            # Student Information
            st.markdown(f"### {text('student_information')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(text('first_name'), key="admission_first_name")
                last_name = st.text_input(text('last_name'), key="admission_last_name")
                date_of_birth = st.date_input(
                    text('date_of_birth'),
                    min_value=date(1990, 1, 1),
                    max_value=date.today(),
                    key="admission_dob"
                )
                gender = st.selectbox(
                    text('gender'),
                    [text('male'), text('female'), text('other')],
                    key="admission_gender"
                )
            
            with col2:
                # Generate admission number
                admission_number = self.generate_admission_number()
                st.text_input(text('admission_number'), value=admission_number, disabled=True)
                
                nationality = st.text_input(text('nationality'), value="", key="admission_nationality")
                religion = st.text_input(text('religion'), value="", key="admission_religion")
                blood_group = st.selectbox(
                    text('blood_group'),
                    ['', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'],
                    key="admission_blood"
                )
            
            # Contact Information
            st.markdown(f"### {text('contact_information')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                address = st.text_area(text('address'), key="admission_address")
                city = st.text_input(text('city'), key="admission_city")
                state = st.text_input(text('state'), key="admission_state")
                zip_code = st.text_input(text('zip_code'), key="admission_zip")
            
            with col2:
                email = st.text_input("Email", key="admission_email")
                phone = st.text_input(text('phone'), key="admission_phone")
                emergency_contact = st.text_input(text('emergency_contact'), key="admission_emergency")
                emergency_phone = st.text_input(text('emergency_phone'), key="admission_emergency_phone")
            
            # Parent/Guardian Information
            st.markdown(f"### {text('parent_guardian_information')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                father_name = st.text_input(text('father_name'), key="admission_father")
                father_occupation = st.text_input(text('father_occupation'), key="admission_father_occ")
                father_phone = st.text_input(text('father_phone'), key="admission_father_phone")
                father_email = st.text_input(text('father_email'), key="admission_father_email")
            
            with col2:
                mother_name = st.text_input(text('mother_name'), key="admission_mother")
                mother_occupation = st.text_input(text('mother_occupation'), key="admission_mother_occ")
                mother_phone = st.text_input(text('mother_phone'), key="admission_mother_phone")
                mother_email = st.text_input(text('mother_email'), key="admission_mother_email")
            
            # Previous Education
            st.markdown(f"### {text('previous_education')}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                previous_school = st.text_input(text('previous_school'), key="admission_prev_school")
            
            with col2:
                previous_class = st.text_input(text('previous_class'), key="admission_prev_class")
            
            with col3:
                year_passed = st.number_input(
                    text('year_passed'),
                    min_value=1900,
                    max_value=datetime.now().year,
                    value=datetime.now().year - 1,
                    key="admission_year_passed"
                )
            
            # Admission Details
            st.markdown(f"### {text('admission_details')}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Get active classes
                classes = db.execute_query("""
                    SELECT class_id, class_name, grade_level 
                    FROM classes 
                    WHERE is_active = TRUE 
                    ORDER BY grade_level, class_name
                """, fetch_all=True)
                
                class_options = {f"{c['class_name']} ({c['grade_level']})": c['class_id'] for c in classes}
                admission_class = st.selectbox(
                    text('admission_class'),
                    options=list(class_options.keys()),
                    key="admission_class"
                )
            
            with col2:
                admission_date = st.date_input(
                    text('admission_date'),
                    value=date.today(),
                    key="admission_date"
                )
            
            with col3:
                academic_year = st.text_input(
                    text('academic_year'),
                    value=f"{datetime.now().year}-{datetime.now().year + 1}",
                    key="admission_academic_year"
                )
            
            # Documents upload
            st.markdown(f"### {text('required_documents')}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                birth_certificate = st.checkbox(text('birth_certificate'), key="doc_birth")
                previous_marksheet = st.checkbox(text('previous_marksheet'), key="doc_marksheet")
            
            with col2:
                transfer_certificate = st.checkbox(text('transfer_certificate'), key="doc_transfer")
                passport_photos = st.checkbox(text('passport_photos'), key="doc_photos")
            
            with col3:
                id_proof = st.checkbox(text('id_proof'), key="doc_id")
                address_proof = st.checkbox(text('address_proof'), key="doc_address")
            
            # Terms and conditions
            st.markdown(f"### {text('terms_conditions')}")
            
            terms_accepted = st.checkbox(
                text('accept_terms'),
                key="admission_terms"
            )
            
            # Submit button
            submitted = st.form_submit_button(text('submit_admission'), type="primary")
            
            if submitted:
                # Validation
                errors = []
                
                if not all([first_name, last_name, admission_date, admission_class]):
                    errors.append(text('required_fields_missing'))
                
                if email and not validate_email(email):
                    errors.append(text('invalid_email'))
                
                if phone and not validate_phone(phone):
                    errors.append(text('invalid_phone'))
                
                if father_email and not validate_email(father_email):
                    errors.append(text('invalid_father_email'))
                
                if mother_email and not validate_email(mother_email):
                    errors.append(text('invalid_mother_email'))
                
                if not terms_accepted:
                    errors.append(text('accept_terms_required'))
                
                if errors:
                    for error in errors:
                        st.error(error)
                    return
                
                # Prepare data
                class_id = class_options[admission_class]
                
                # Insert student record
                insert_query = """
                    INSERT INTO students (
                        admission_number, first_name, last_name, date_of_birth,
                        gender, address, parent_name, parent_phone, parent_email,
                        class_id, admission_date, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING student_id
                """
                
                try:
                    # Use father as primary parent if available, otherwise mother
                    primary_parent_name = father_name or mother_name
                    primary_parent_phone = father_phone or mother_phone
                    primary_parent_email = father_email or mother_email
                    
                    result = db.execute_query(
                        insert_query,
                        (
                            admission_number, first_name, last_name, date_of_birth,
                            gender, address, primary_parent_name, primary_parent_phone,
                            primary_parent_email, class_id, admission_date, True
                        ),
                        fetch_one=True
                    )
                    
                    if result:
                        student_id = result['student_id']
                        
                        # Insert additional information (in a real system, you'd have additional tables)
                        # For now, we'll store in session or log
                        
                        st.success(f"""
                        ### {text('admission_successful')}! 
                        
                        **{text('admission_number')}:** {admission_number}  
                        **{text('student_id')}:** {student_id}  
                        **{text('student_name')}:** {first_name} {last_name}  
                        **{text('admission_class')}:** {admission_class}  
                        **{text('admission_date')}:** {admission_date}
                        
                        {text('print_admission_form_message')}
                        """)
                        
                        # Print/Download button
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(text('print_admission_form')):
                                st.info(text('printing_admission_form'))
                        with col2:
                            if st.button(text('new_admission')):
                                st.rerun()
                        
                    else:
                        st.error(text('admission_failed'))
                        
                except Exception as e:
                    st.error(f"{text('error_processing_admission')}: {str(e)}")
    
    def display_admission_records(self):
        """Display admission records"""
        text = lang_manager.get_text
        
        st.subheader(text('admission_records'))
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            start_date = st.date_input(text('from_date'), value=date.today().replace(day=1))
        
        with col2:
            end_date = st.date_input(text('to_date'), value=date.today())
        
        with col3:
            class_filter = st.selectbox(
                text('filter_by_class'),
                ['All Classes'] + self.get_class_list()
            )
        
        with col4:
            status_filter = st.selectbox(
                text('filter_by_status'),
                [text('all'), text('active'), text('inactive')]
            )
        
        # Search
        search_term = st.text_input(text('search_student'), placeholder=text('search_by_name_or_id'))
        
        if st.button(text('search'), type="primary"):
            # Build query with filters
            query = """
                SELECT 
                    s.student_id,
                    s.admission_number,
                    s.first_name,
                    s.last_name,
                    s.date_of_birth,
                    s.gender,
                    s.admission_date,
                    s.is_active,
                    c.class_name,
                    c.grade_level,
                    u.full_name as class_teacher
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.class_id
                LEFT JOIN users u ON c.class_teacher_id = u.user_id
                WHERE s.admission_date BETWEEN %s AND %s
            """
            
            params = [start_date, end_date]
            
            if class_filter != 'All Classes':
                query += " AND c.class_name = %s"
                params.append(class_filter)
            
            if status_filter == text('active'):
                query += " AND s.is_active = TRUE"
            elif status_filter == text('inactive'):
                query += " AND s.is_active = FALSE"
            
            if search_term:
                query += " AND (s.first_name ILIKE %s OR s.last_name ILIKE %s OR s.admission_number ILIKE %s)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            query += " ORDER BY s.admission_date DESC"
            
            records = db.execute_query(query, tuple(params), fetch_all=True)
            
            if records:
                # Display summary
                total_students = len(records)
                active_students = len([r for r in records if r['is_active']])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(text('total_admissions'), total_students)
                with col2:
                    st.metric(text('active_students'), active_students)
                
                st.divider()
                
                # Display records
                df = pd.DataFrame(records)
                
                # Format columns
                df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.strftime('%Y-%m-%d')
                df['admission_date'] = pd.to_datetime(df['admission_date']).dt.strftime('%Y-%m-%d')
                df['status'] = df['is_active'].apply(lambda x: '✅ ' + text('active') if x else '❌ ' + text('inactive'))
                df['class_info'] = df['class_name'] + ' (' + df['grade_level'] + ')'
                
                # Select columns to display
                display_cols = [
                    'admission_number', 'first_name', 'last_name', 'date_of_birth',
                    'gender', 'class_info', 'class_teacher', 'admission_date', 'status'
                ]
                
                display_df = df[display_cols].copy()
                display_df.columns = [
                    text('admission_number'), text('first_name'), text('last_name'),
                    text('date_of_birth'), text('gender'), text('class'),
                    text('class_teacher'), text('admission_date'), text('status')
                ]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )
                
                # Export option
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=text('export_to_csv'),
                    data=csv,
                    file_name=f'admission_records_{start_date}_{end_date}.csv',
                    mime='text/csv'
                )
                
                # Individual student details
                st.subheader(text('student_details'))
                selected_student = st.selectbox(
                    text('select_student_for_details'),
                    options=[f"{r['first_name']} {r['last_name']} ({r['admission_number']})" for r in records]
                )
                
                if selected_student:
                    admission_number = selected_student.split('(')[-1].rstrip(')')
                    student_info = next(r for r in records if r['admission_number'] == admission_number)
                    self.display_student_details(student_info['student_id'])
            else:
                st.info(text('no_admission_records_found'))
    
    def get_class_list(self):
        """Get list of classes for filter"""
        query = "SELECT DISTINCT class_name FROM classes WHERE is_active = TRUE ORDER BY class_name"
        classes = db.execute_query(query, fetch_all=True)
        return [c['class_name'] for c in classes] if classes else []
    
    def display_student_details(self, student_id):
        """Display detailed student information"""
        text = lang_manager.get_text
        
        query = """
            SELECT 
                s.*,
                c.class_name,
                c.grade_level,
                c.section,
                u.full_name as class_teacher
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            LEFT JOIN users u ON c.class_teacher_id = u.user_id
            WHERE s.student_id = %s
        """
        
        student = db.execute_query(query, (student_id,), fetch_one=True)
        
        if student:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**{text('admission_number')}:** {student['admission_number']}")
                st.write(f"**{text('student_name')}:** {student['first_name']} {student['last_name']}")
                st.write(f"**{text('date_of_birth')}:** {student['date_of_birth']}")
                st.write(f"**{text('gender')}:** {student['gender']}")
                st.write(f"**{text('class')}:** {student['class_name']} ({student['grade_level']})")
            
            with col2:
                st.write(f"**{text('admission_date')}:** {student['admission_date']}")
                st.write(f"**{text('class_teacher')}:** {student['class_teacher'] or 'Not Assigned'}")
                st.write(f"**{text('parent_name')}:** {student['parent_name']}")
                st.write(f"**{text('parent_phone')}:** {student['parent_phone']}")
                st.write(f"**{text('status')}:** {'✅ ' + text('active') if student['is_active'] else '❌ ' + text('inactive')}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(text('edit_student'), key=f"edit_{student_id}"):
                    st.session_state['edit_student_id'] = student_id
                    st.rerun()
            with col2:
                if st.button(text('transfer_class'), key=f"transfer_{student_id}"):
                    st.session_state['transfer_student_id'] = student_id
                    st.rerun()
            with col3:
                new_status = not student['is_active']
                status_text = text('deactivate') if student['is_active'] else text('activate')
                if st.button(status_text, key=f"status_{student_id}"):
                    self.update_student_status(student_id, new_status)
    
    def update_student_status(self, student_id, is_active):
        """Update student active status"""
        query = "UPDATE students SET is_active = %s WHERE student_id = %s"
        try:
            db.execute_query(query, (is_active, student_id))
            st.success(text('student_status_updated'))
            st.rerun()
        except Exception as e:
            st.error(f"{text('error_updating_status')}: {str(e)}")
    
    def display_pending_applications(self):
        """Display pending admission applications"""
        text = lang_manager.get_text
        
        st.subheader(text('pending_applications'))
        
        # In a real system, you would have an applications table
        # For now, we'll simulate with a placeholder
        st.info(text('pending_applications_info'))
        
        # Simulated pending applications
        pending_apps = [
            {
                'id': 1,
                'name': 'John Smith',
                'applied_date': '2024-01-15',
                'applied_class': 'Grade 10',
                'status': 'Under Review'
            },
            {
                'id': 2,
                'name': 'Sarah Johnson',
                'applied_date': '2024-01-14',
                'applied_class': 'Grade 8',
                'status': 'Documents Pending'
            }
        ]
        
        for app in pending_apps:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{app['name']}**")
                
                with col2:
                    st.write(app['applied_date'])
                
                with col3:
                    st.write(app['applied_class'])
                
                with col4:
                    st.write(app['status'])
                    
                    # Action buttons
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(text('review'), key=f"review_{app['id']}"):
                            st.session_state['review_app_id'] = app['id']
                    with col_b:
                        if st.button(text('process'), key=f"process_{app['id']}"):
                            st.session_state['process_app_id'] = app['id']
                
                st.divider()
    
    def display_admission_reports(self):
        """Display admission reports and analytics"""
        text = lang_manager.get_text
        
        st.subheader(text('admission_reports'))
        
        # Report type selection
        report_type = st.selectbox(
            text('select_report_type'),
            [
                text('admission_trends'),
                text('class_wise_admissions'),
                text('monthly_admissions'),
                text('gender_distribution')
            ]
        )
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            report_start_date = st.date_input(
                text('report_start_date'),
                value=date(date.today().year, 1, 1)
            )
        with col2:
            report_end_date = st.date_input(
                text('report_end_date'),
                value=date.today()
            )
        
        if st.button(text('generate_report'), type="primary"):
            if report_type == text('admission_trends'):
                self.generate_admission_trends_report(report_start_date, report_end_date)
            elif report_type == text('class_wise_admissions'):
                self.generate_class_wise_report(report_start_date, report_end_date)
            elif report_type == text('monthly_admissions'):
                self.generate_monthly_admissions_report(report_start_date, report_end_date)
            elif report_type == text('gender_distribution'):
                self.generate_gender_distribution_report(report_start_date, report_end_date)
    
    def generate_admission_trends_report(self, start_date, end_date):
        """Generate admission trends report"""
        text = lang_manager.get_text
        
        query = """
            SELECT 
                DATE_TRUNC('month', admission_date) as month,
                COUNT(*) as admissions,
                COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male,
                COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female
            FROM students
            WHERE admission_date BETWEEN %s AND %s
            GROUP BY DATE_TRUNC('month', admission_date)
            ORDER BY month
        """
        
        data = db.execute_query(query, (start_date, end_date), fetch_all=True)
        
        if data:
            import plotly.express as px
            import plotly.graph_objects as go
            
            df = pd.DataFrame(data)
            df['month'] = pd.to_datetime(df['month']).dt.strftime('%b %Y')
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['admissions'],
                name=text('total_admissions'),
                marker_color='indigo'
            ))
            
            fig.update_layout(
                title=text('admission_trends'),
                xaxis_title=text('month'),
                yaxis_title=text('number_of_admissions'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display data table
            st.dataframe(df, use_container_width=True)
        else:
            st.info(text('no_data_for_period'))