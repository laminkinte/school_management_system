import os
import streamlit as st

# Application configuration
APP_CONFIG = {
    'title': 'Professional School Management System',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
    'database_path': 'school_management.db'
}

# User roles
ROLES = {
    'DEVELOPER': 'developer',
    'SUPER_ADMIN': 'super_admin',
    'ADMIN': 'admin',
    'TEACHER': 'teacher',
    'STUDENT': 'student'
}

# Supported languages
LANGUAGES = {
    'English': 'en',
    'العربية': 'ar'
}