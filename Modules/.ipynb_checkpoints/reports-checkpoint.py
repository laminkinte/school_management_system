# modules/reports.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import db

def show_reports(translator, auth):
    """Display reports and analytics"""
    st.title(translator.t('reports'))
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Dashboard Analytics",
        "Student Reports",
        "Financial Reports",
        "Custom Reports"
    ])
    
    with tab1:
        st.subheader("System Analytics")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=date.today())
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Total students
            total_students = db.fetch_one("SELECT COUNT(*) FROM students")[0]
            new_students = db.fetch_one(
                "SELECT COUNT(*) FROM students WHERE admission_date BETWEEN ? AND ?",
                (start_date, end_date)
            )[0]
            st.metric("Total Students", total_students, f"+{new_students}")
        
        with col2:
            # Attendance rate
            attendance_data = db.fetch_one('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
                FROM attendance 
                WHERE date BETWEEN ? AND ?
            ''', (start_date, end_date))
            
            if attendance_data['total'] > 0:
                attendance_rate = (attendance_data['present'] / attendance_data['total']) * 100
                st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
            else:
                st.metric("Attendance Rate", "N/A")
        
        with col3:
            # Fee collection rate
            fees_data = db.fetch_one('''
                SELECT 
                    SUM(amount) as total_amount,
                    SUM(paid_amount) as total_paid
                FROM fees 
                WHERE due_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            
            if fees_data['total_amount'] and fees_data['total_amount'] > 0:
                collection_rate = (fees_data['total_paid'] / fees_data['total_amount']) * 100
                st.metric("Fee Collection", f"{collection_rate:.1f}%")
            else:
                st.metric("Fee Collection", "N/A")
        
        with col4:
            # Pass percentage
            results_data = db.fetch_one('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) as passed
                FROM results 
                WHERE exam_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            
            if results_data['total'] > 0:
                pass_percentage = (results_data['passed'] / results_data['total']) * 100
                st.metric("Pass Percentage", f"{pass_percentage:.1f}%")
            else:
                st.metric("Pass Percentage", "N/A")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly attendance trend
            monthly_attendance = db.get_dataframe('''
                SELECT 
                    strftime('%Y-%m', date) as month,
                    COUNT(*) as total_attendance,
                    AVG(CASE WHEN status = 'Present' THEN 100.0 ELSE 0 END) as attendance_rate
                FROM attendance
                WHERE date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month
            ''', (start_date, end_date))
            
            if not monthly_attendance.empty:
                fig = px.line(monthly_attendance, x='month', y='attendance_rate',
                             title='Monthly Attendance Rate')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Fee collection trend
            monthly_fees = db.get_dataframe('''
                SELECT 
                    strftime('%Y-%m', payment_date) as month,
                    SUM(paid_amount) as total_collected,
                    COUNT(*) as transactions
                FROM fees
                WHERE payment_date BETWEEN ? AND ?
                    AND status IN ('Paid', 'Partial')
                GROUP BY strftime('%Y-%m', payment_date)
                ORDER BY month
            ''', (start_date, end_date))
            
            if not monthly_fees.empty:
                fig = px.bar(monthly_fees, x='month', y='total_collected',
                            title='Monthly Fee Collection')
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Student Reports")
        
        report_type = st.selectbox(
            "Select Report",
            ["Student Performance", "Attendance Summary", "Fee Status", "Student Profile"]
        )
        
        if report_type == "Student Performance":
            # Class-wise performance
            performance_df = db.get_dataframe('''
                SELECT 
                    c.class_name,
                    COUNT(DISTINCT r.student_id) as student_count,
                    AVG(r.percentage) as avg_percentage,
                    SUM(CASE WHEN r.percentage >= 40 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pass_percentage
                FROM results r
                JOIN students s ON r.student_id = s.id
                JOIN classes c ON s.class_id = c.id
                GROUP BY c.class_name
                ORDER BY avg_percentage DESC
            ''')
            
            if not performance_df.empty:
                st.dataframe(performance_df, use_container_width=True)
                
                fig = px.bar(performance_df, x='class_name', y='avg_percentage',
                            title='Class-wise Average Performance')
                st.plotly_chart(fig, use_container_width=True)
        
        elif report_type == "Attendance Summary":
            # Student-wise attendance
            attendance_summary = db.get_dataframe('''
                SELECT 
                    s.full_name,
                    s.student_id,
                    c.class_name,
                    COUNT(a.id) as total_days,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
                    ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.id), 2) as attendance_percentage
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date BETWEEN ? AND ?
                LEFT JOIN classes c ON s.class_id = c.id
                WHERE s.status = 'Active'
                GROUP BY s.id
                HAVING total_days > 0
                ORDER BY attendance_percentage DESC
            ''', (date.today() - timedelta(days=30), date.today()))
            
            if not attendance_summary.empty:
                st.dataframe(attendance_summary, use_container_width=True)
    
    with tab3:
        st.subheader("Financial Reports")
        
        financial_report = db.get_dataframe('''
            SELECT 
                strftime('%Y-%m', f.due_date) as month,
                f.fee_type,
                SUM(f.amount) as total_amount,
                SUM(f.paid_amount) as total_paid,
                SUM(f.amount - f.paid_amount) as total_due,
                COUNT(DISTINCT f.student_id) as students
            FROM fees f
            WHERE f.due_date BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', f.due_date), f.fee_type
            ORDER BY month, fee_type
        ''', (date.today() - timedelta(days=90), date.today()))
        
        if not financial_report.empty:
            st.dataframe(financial_report, use_container_width=True)
            
            # Pivot for better visualization
            pivot_df = financial_report.pivot_table(
                index='month',
                columns='fee_type',
                values='total_paid',
                aggfunc='sum',
                fill_value=0
            )
            
            fig = px.line(pivot_df, title='Monthly Fee Collection by Type')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Custom Reports Generator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tables = ["students", "teachers", "attendance", "fees", "results", "classes"]
            selected_table = st.selectbox("Select Table", tables)
            
            if selected_table:
                # Get columns for selected table
                columns = db.get_dataframe(f"PRAGMA table_info({selected_table})")
                column_names = columns['name'].tolist()
                
                selected_columns = st.multiselect(
                    "Select Columns",
                    column_names,
                    default=column_names[:5] if len(column_names) > 5 else column_names
                )
        
        with col2:
            filter_column = st.selectbox("Filter Column (Optional)", [""] + column_names)
            filter_value = st.text_input("Filter Value")
            
            sort_column = st.selectbox("Sort By (Optional)", [""] + column_names)
            sort_order = st.radio("Sort Order", ["ASC", "DESC"], horizontal=True)
        
        if st.button("Generate Report"):
            if selected_columns:
                # Build query
                query = f"SELECT {', '.join(selected_columns)} FROM {selected_table}"
                params = []
                
                if filter_column and filter_value:
                    query += f" WHERE {filter_column} LIKE ?"
                    params.append(f"%{filter_value}%")
                
                if sort_column:
                    query += f" ORDER BY {sort_column} {sort_order}"
                
                report_df = db.get_dataframe(query, params)
                
                if not report_df.empty:
                    st.dataframe(report_df, use_container_width=True)
                    
                    # Export options
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv = report_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"report_{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            report_df.to_excel(writer, index=False, sheet_name='Report')
                        
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer.getvalue(),
                            file_name=f"report_{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("No data found for the selected criteria")