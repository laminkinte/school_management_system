# modules/fees.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from database import db

def show_fees(translator, auth):
    """Display fees management"""
    st.title(translator.t('fees'))
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "View Fees",
        "Collect Fees",
        "Fee Structure",
        "Reports"
    ])
    
    with tab1:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Fee Status",
                ["All", "Paid", "Unpaid", "Partial", "Overdue"]
            )
        
        with col2:
            fee_type_filter = st.selectbox(
                "Fee Type",
                ["All"] + [f[0] for f in db.fetch_all("SELECT DISTINCT fee_type FROM fees") if f[0]]
            )
        
        with col3:
            due_date_filter = st.date_input("Due Date Before", value=date.today() + timedelta(days=30))
        
        # Build query
        query = '''
            SELECT f.*, s.full_name, s.student_id, c.class_name
            FROM fees f
            JOIN students s ON f.student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if status_filter != "All":
            if status_filter == "Overdue":
                query += " AND f.status IN ('Unpaid', 'Partial') AND f.due_date < ?"
                params.append(date.today())
            else:
                query += " AND f.status = ?"
                params.append(status_filter)
        
        if fee_type_filter != "All":
            query += " AND f.fee_type = ?"
            params.append(fee_type_filter)
        
        query += " AND f.due_date <= ?"
        params.append(due_date_filter)
        
        query += " ORDER BY f.due_date"
        
        fees_df = db.get_dataframe(query, params)
        
        if not fees_df.empty:
            # Calculate totals
            total_amount = fees_df['amount'].sum()
            total_paid = fees_df['paid_amount'].sum()
            total_due = total_amount - total_paid
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Amount", f"${total_amount:,.2f}")
            col2.metric("Total Paid", f"${total_paid:,.2f}")
            col3.metric("Total Due", f"${total_due:,.2f}")
            
            # Display fees
            st.dataframe(
                fees_df[['student_name', 'student_id', 'class_name', 'fee_type',
                        'amount', 'paid_amount', 'due_date', 'status']],
                use_container_width=True
            )
            
            # Export option
            csv = fees_df.to_csv(index=False)
            st.download_button(
                label="Export to CSV",
                data=csv,
                file_name=f"fees_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No fees records found")
    
    with tab2:
        st.subheader("Collect Fees")
        
        with st.form("collect_fees_form"):
            # Student selection
            students = db.fetch_all('''
                SELECT s.id, s.full_name, s.student_id, 
                       SUM(f.amount - f.paid_amount) as pending_amount
                FROM students s
                LEFT JOIN fees f ON s.id = f.student_id AND f.status IN ('Unpaid', 'Partial')
                WHERE s.status = 'Active'
                GROUP BY s.id
                HAVING pending_amount > 0 OR pending_amount IS NULL
                ORDER BY s.full_name
            ''')
            
            student_options = {}
            for s in students:
                pending = s['pending_amount'] if s['pending_amount'] else 0
                student_options[f"{s['full_name']} ({s['student_id']}) - Pending: ${pending:.2f}"] = s['id']
            
            if student_options:
                selected_student = st.selectbox("Select Student*", list(student_options.keys()))
                
                if selected_student:
                    student_id = student_options[selected_student]
                    
                    # Get pending fees for this student
                    pending_fees = db.fetch_all('''
                        SELECT * FROM fees 
                        WHERE student_id = ? AND status IN ('Unpaid', 'Partial')
                        ORDER BY due_date
                    ''', (student_id,))
                    
                    if pending_fees:
                        st.write("**Pending Fees:**")
                        
                        selected_fees = []
                        for fee in pending_fees:
                            col1, col2, col3 = st.columns([3, 2, 2])
                            
                            with col1:
                                st.write(f"{fee['fee_type']} - Due: {fee['due_date']}")
                                st.write(f"Amount: ${fee['amount']:.2f}, Paid: ${fee['paid_amount']:.2f}")
                                st.write(f"Balance: ${fee['amount'] - fee['paid_amount']:.2f}")
                            
                            with col2:
                                pay_amount = st.number_input(
                                    "Amount to Pay",
                                    min_value=0.0,
                                    max_value=float(fee['amount'] - fee['paid_amount']),
                                    value=float(fee['amount'] - fee['paid_amount']),
                                    key=f"pay_{fee['id']}"
                                )
                            
                            with col3:
                                if st.checkbox("Select", key=f"select_{fee['id']}"):
                                    selected_fees.append({
                                        'fee_id': fee['id'],
                                        'pay_amount': pay_amount
                                    })
                        
                        # Payment details
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            total_pay = sum(f['pay_amount'] for f in selected_fees)
                            st.write(f"**Total Payment: ${total_pay:.2f}**")
                            
                            payment_method = st.selectbox(
                                "Payment Method",
                                ["Cash", "Bank Transfer", "Check", "Credit Card", "Online"]
                            )
                        
                        with col2:
                            payment_date = st.date_input("Payment Date", value=date.today())
                            transaction_id = st.text_input("Transaction ID (Optional)")
                            remarks = st.text_area("Remarks")
                        
                        if st.form_submit_button("Process Payment"):
                            if selected_fees and total_pay > 0:
                                for fee in selected_fees:
                                    # Update fee record
                                    current_fee = db.fetch_one(
                                        "SELECT amount, paid_amount FROM fees WHERE id = ?",
                                        (fee['fee_id'],)
                                    )
                                    
                                    new_paid = current_fee['paid_amount'] + fee['pay_amount']
                                    new_status = "Paid" if new_paid >= current_fee['amount'] else "Partial"
                                    
                                    db.execute_query('''
                                        UPDATE fees 
                                        SET paid_amount = ?, status = ?, 
                                            payment_date = ?, payment_method = ?,
                                            transaction_id = ?, remarks = ?,
                                            collected_by = ?
                                        WHERE id = ?
                                    ''', (
                                        new_paid, new_status, payment_date,
                                        payment_method, transaction_id, remarks,
                                        auth.get_current_user()['id'], fee['fee_id']
                                    ))
                                
                                st.success(f"Payment of ${total_pay:.2f} processed successfully!")
                            else:
                                st.error("Please select fees to pay")
                    else:
                        st.info("No pending fees for this student")
            else:
                st.info("No students with pending fees")
    
    with tab3:
        st.subheader("Fee Structure Management")
        
        # View current fee structure
        fee_structure = db.get_dataframe('''
            SELECT config_key, config_value, description 
            FROM system_config 
            WHERE config_key LIKE 'fee_%'
            ORDER BY config_key
        ''')
        
        if not fee_structure.empty:
            st.dataframe(fee_structure, use_container_width=True)
        
        # Add/Edit fee structure
        with st.form("fee_structure_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                fee_type = st.text_input("Fee Type*", placeholder="e.g., tuition_fee, admission_fee")
                amount = st.number_input("Amount*", min_value=0.0, value=1000.0)
            
            with col2:
                description = st.text_input("Description", placeholder="e.g., Annual Tuition Fee")
                academic_year = st.text_input("Academic Year", value="2024-2025")
            
            if st.form_submit_button("Save Fee Structure"):
                if fee_type and amount > 0:
                    config_key = f"fee_{fee_type}_{academic_year}"
                    
                    # Check if exists
                    existing = db.fetch_one(
                        "SELECT id FROM system_config WHERE config_key = ?",
                        (config_key,)
                    )
                    
                    if existing:
                        db.execute_query('''
                            UPDATE system_config 
                            SET config_value = ?, description = ?
                            WHERE id = ?
                        ''', (str(amount), description, existing['id']))
                    else:
                        db.execute_query('''
                            INSERT INTO system_config (config_key, config_value, config_type, description)
                            VALUES (?, ?, 'fee_structure', ?)
                        ''', (config_key, str(amount), description))
                    
                    st.success("Fee structure saved!")
                else:
                    st.error("Please fill required fields")
    
    with tab4:
        st.subheader("Fees Reports & Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            end_date = st.date_input("End Date", value=date.today())
        
        with col2:
            report_type = st.selectbox(
                "Report Type",
                ["Collection Summary", "Fee Type Analysis", "Class-wise Collection", "Overdue Report"]
            )
        
        if st.button("Generate Report"):
            if report_type == "Collection Summary":
                report_df = db.get_dataframe('''
                    SELECT 
                        DATE(payment_date) as payment_date,
                        COUNT(*) as transactions,
                        SUM(paid_amount) as total_collected,
                        AVG(paid_amount) as avg_payment
                    FROM fees
                    WHERE payment_date BETWEEN ? AND ?
                        AND status IN ('Paid', 'Partial')
                    GROUP BY DATE(payment_date)
                    ORDER BY payment_date
                ''', (start_date, end_date))
                
                if not report_df.empty:
                    st.dataframe(report_df, use_container_width=True)
                    
                    # Chart
                    fig = px.line(report_df, x='payment_date', y='total_collected',
                                 title='Daily Fee Collection')
                    st.plotly_chart(fig, use_container_width=True)
            
            elif report_type == "Fee Type Analysis":
                report_df = db.get_dataframe('''
                    SELECT 
                        fee_type,
                        COUNT(*) as count,
                        SUM(amount) as total_amount,
                        SUM(paid_amount) as total_paid,
                        SUM(amount - paid_amount) as total_due
                    FROM fees
                    WHERE due_date BETWEEN ? AND ?
                    GROUP BY fee_type
                    ORDER BY total_amount DESC
                ''', (start_date, end_date))
                
                if not report_df.empty:
                    st.dataframe(report_df, use_container_width=True)
                    
                    fig = px.pie(report_df, values='total_amount', names='fee_type',
                                title='Fee Distribution by Type')
                    st.plotly_chart(fig, use_container_width=True)