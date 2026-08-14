# config.py
import os
from urllib.parse import urlparse

# Safely try loading python-dotenv if installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aquaguru-production-secret-key-2024-shrimp-farm')
    
    # DB Engine: 'auto' (tries MySQL first, falls back to SQLite), 'mysql', or 'sqlite'
    DB_ENGINE = os.environ.get('DB_ENGINE', 'auto')
    SQLITE_PATH = os.environ.get('SQLITE_PATH', 'aquaguru.db')
    
    # Cloud Database URL support (Render / Railway / Aiven / Heroku style)
    DATABASE_URL = (
        os.environ.get('DATABASE_URL') or 
        os.environ.get('MYSQL_URL') or 
        os.environ.get('CLEARDB_DATABASE_URL') or 
        os.environ.get('JAWSDB_URL')
    )
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'aquaguru')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_SSL_MODE = os.environ.get('MYSQL_SSL_MODE', '')  # 'REQUIRED', 'DISABLED', etc.
    MYSQL_SSL_CA = os.environ.get('MYSQL_SSL_CA', '')
    
    # Parse DATABASE_URL if provided
    if DATABASE_URL:
        if DATABASE_URL.startswith('mysql://') or DATABASE_URL.startswith('mysql+pymysql://'):
            url = urlparse(DATABASE_URL)
            MYSQL_HOST = url.hostname or MYSQL_HOST
            MYSQL_PORT = url.port or MYSQL_PORT
            MYSQL_USER = url.username or MYSQL_USER
            MYSQL_PASSWORD = url.password or MYSQL_PASSWORD
            MYSQL_DATABASE = url.path.lstrip('/') or MYSQL_DATABASE
        elif DATABASE_URL.startswith('sqlite://'):
            DB_ENGINE = 'sqlite'
            SQLITE_PATH = DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
    
    # ==================== GOOGLE FIREBASE / FIRESTORE CONFIG ====================
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'AIzaSyBQsl2HCcf_RLEFkyooSQCKZvdjgzC5XWs')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', 'aquaguru-f35c0.firebaseapp.com')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'aquaguru-f35c0')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'aquaguru-f35c0.firebasestorage.app')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '632009597255')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '1:632009597255:web:a9a708852a4c5817772c62')
    FIREBASE_MEASUREMENT_ID = os.environ.get('FIREBASE_MEASUREMENT_ID', 'G-FBVB1F0CJ9')
    FIREBASE_ENABLED = os.environ.get('FIREBASE_ENABLED', 'True').lower() in ('true', '1', 't')
    
    FIREBASE_CONFIG = {
        "apiKey": FIREBASE_API_KEY,
        "authDomain": FIREBASE_AUTH_DOMAIN,
        "projectId": FIREBASE_PROJECT_ID,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": FIREBASE_MESSAGING_SENDER_ID,
        "appId": FIREBASE_APP_ID,
        "measurementId": FIREBASE_MEASUREMENT_ID
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 3600
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')