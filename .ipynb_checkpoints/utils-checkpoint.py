import json
import streamlit as st
from typing import Dict, Any
import arabic_reshaper
from bidi.algorithm import get_display
from config import LANGUAGES
import os
from datetime import datetime, date

class LanguageManager:
    """Manage multi-language support"""
    
    def __init__(self):
        self.locales_dir = "locales"
        self.current_language = "en"
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files"""
        for lang_code in LANGUAGES.values():
            file_path = os.path.join(self.locales_dir, f"{lang_code}.json")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except FileNotFoundError:
                st.error(f"Translation file not found: {file_path}")
                self.translations[lang_code] = {}
            except json.JSONDecodeError:
                st.error(f"Invalid JSON in translation file: {file_path}")
                self.translations[lang_code] = {}
    
    def set_language(self, language_code: str):
        """Set current language"""
        if language_code in self.translations:
            self.current_language = language_code
            st.session_state['language'] = language_code
    
    def get_text(self, key: str) -> str:
        """Get translated text for key"""
        lang = st.session_state.get('language', self.current_language)
        text = self.translations.get(lang, {}).get(key, key)
        
        # Handle Arabic text shaping
        if lang == 'ar':
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        
        return text
    
    def get_rtl(self) -> bool:
        """Check if current language is RTL (Arabic)"""
        return st.session_state.get('language', self.current_language) == 'ar'

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'language' not in st.session_state:
        st.session_state['language'] = 'en'
    if 'page' not in st.session_state:
        st.session_state['page'] = 'dashboard'
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'light'

def format_date(date_obj, format_str="%Y-%m-%d"):
    """Format date object to string"""
    if date_obj:
        if isinstance(date_obj, str):
            # Try to parse string date
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
            except:
                return date_obj
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime(format_str)
    return ""

def format_currency(amount):
    """Format currency amount"""
    if amount is None:
        return "$0.00"
    try:
        return f"${float(amount):,.2f}"
    except:
        return f"${amount}"

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return 0
    
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except:
            return 0
    
    today = date.today()
    try:
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        return 0

def validate_email(email):
    """Validate email address"""
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number"""
    import re
    if not phone:
        return True  # Phone is optional
    pattern = r'^[\+]?[1-9][\d]{0,15}$'
    return re.match(pattern, phone) is not None

def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        return int(value)
    except:
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except:
        return default

def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

lang_manager = LanguageManager()