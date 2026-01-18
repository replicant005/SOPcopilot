# configuration management for flask app 
# the logic will load the env variables from .env file 

import os
from dotenv import load_dotenv
load_dotenv()

# base config class, all settings are loaded from 
class Config:
    # Flask secret key (used for sessions, cookies, etc.)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Cohere API key (if backend needs it, otherwise AI team handles)
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY') or None
    
    # Flask settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
    
    # JSON settings
    JSON_AS_ASCII = False  # Allow non-ASCII characters in JSON
    JSON_SORT_KEYS = False  # Keep JSON key order (don't sort alphabetically) 
