import streamlit as st
import pandas as pd
from database import db
from auth import auth
from utils import lang_manager, validate_email, validate_phone
from config import ROLES

class UserManagementModule:
    """User management module"""
    
    def display(self):
        """Display user management interface"""
        text = lang_manager.get_text
        
        if not auth.has_permission(ROLES['ADMIN']):
            st.warning(text('no_permission'))
            return
        
        st.title(text('user_management'))
        
        # Tabs for different operations
        tab1, tab2, tab3 = st.tabs([
            text('view_users'),
            text('add_user'),
            text('edit_user')
        ])
        
        with tab1:
            self.display_users_list()
        
        with tab2:
            self.display_add_user_form()
        
        with tab3:
            self.display_edit_user_form()
    
    def display_users_list(self):
        """Display list of all users"""
        text = lang_manager.get_text
        
        users = auth.get_all_users()
        
        if users:
            # Convert to DataFrame for display
            df = pd.DataFrame(users)
            if 'last_login' in df.columns:
                df['last_login'] = pd.to_datetime(df['last_login'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Rename columns for display
            display_cols = ['username', 'email', 'full_name', 'role', 'phone', 'is_active']
            if 'last_login' in df.columns:
                display_cols.append('last_login')
            if 'created_at' in df.columns:
                display_cols.append('created_at')
            
            df_display = df[display_cols]
            df_display.columns = [
                text('username'), text('email'), text('full_name'), text('role'),
                text('phone'), text('status')
            ]
            
            # Add last_login and created_at if they exist
            if 'last_login' in df.columns:
                df_display[text('last_login')] = df['last_login']
            if 'created_at' in df.columns:
                df_display[text('created_at')] = df['created_at']
            
            st.dataframe(df_display, use_container_width=True)
            
            # Export option
            if st.button(text('export')):
                csv = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=text('download_csv'),
                    data=csv,
                    file_name='users.csv',
                    mime='text/csv'
                )
        else:
            st.info(text('no_data'))
    
    def display_add_user_form(self):
        """Display form to add new user"""
        text = lang_manager.get_text
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input(text('username'), key="add_username")
                email = st.text_input("Email", key="add_email")
                password = st.text_input(text('password'), type="password", key="add_password")
                confirm_password = st.text_input(text('confirm_password'), type="password", key="add_confirm_password")
            
            with col2:
                full_name = st.text_input(text('full_name'), key="add_full_name")
                phone = st.text_input(text('phone'), key="add_phone")
                role = st.selectbox(
                    text('role'),
                    options=list(ROLES.values()),
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                is_active = st.checkbox(text('active'), value=True, key="add_is_active")
            
            submitted = st.form_submit_button(text('save'))
            
            if submitted:
                # Validation
                if not all([username, email, password, confirm_password, full_name, role]):
                    st.error(text('all_fields_required'))
                    return
                
                if password != confirm_password:
                    st.error(text('password_mismatch'))
                    return
                
                if not validate_email(email):
                    st.error(text('invalid_email'))
                    return
                
                if phone and not validate_phone(phone):
                    st.error(text('invalid_phone'))
                    return
                
                # Create user
                success, message = auth.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    full_name=full_name,
                    phone=phone if phone else None
                )
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    def display_edit_user_form(self):
        """Display form to edit user"""
        text = lang_manager.get_text
        
        # Get users for selection
        users = auth.get_all_users()
        if not users:
            st.info(text('no_users_found'))
            return
        
        user_options = {f"{u['full_name']} ({u['username']})": u['user_id'] for u in users}
        
        selected_user = st.selectbox(
            text('select_user'),
            options=list(user_options.keys()),
            key="edit_user_select"
        )
        
        if selected_user:
            user_id = user_options[selected_user]
            user = next((u for u in users if u['user_id'] == user_id), None)
            
            if user:
                with st.form("edit_user_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        username = st.text_input(text('username'), value=user['username'])
                        email = st.text_input("Email", value=user['email'])
                        full_name = st.text_input(text('full_name'), value=user['full_name'])
                    
                    with col2:
                        phone = st.text_input(text('phone'), value=user['phone'] or '')
                        role = st.selectbox(
                            text('role'),
                            options=list(ROLES.values()),
                            index=list(ROLES.values()).index(user['role']) if user['role'] in ROLES.values() else 0,
                            format_func=lambda x: x.replace('_', ' ').title()
                        )
                        is_active = st.checkbox(text('active'), value=bool(user['is_active']))
                    
                    submitted = st.form_submit_button(text('save'))
                    
                    if submitted:
                        # Validation
                        if not all([username, email, full_name, role]):
                            st.error(text('all_fields_required'))
                            return
                        
                        if not validate_email(email):
                            st.error(text('invalid_email'))
                            return
                        
                        if phone and not validate_phone(phone):
                            st.error(text('invalid_phone'))
                            return
                        
                        # Update user
                        success, message = auth.update_user(
                            user_id=user_id,
                            username=username,
                            email=email,
                            role=role,
                            full_name=full_name,
                            phone=phone if phone else None,
                            is_active=is_active
                        )
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)