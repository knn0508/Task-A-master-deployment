# config.py
"""Application configuration"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Detect Vercel serverless environment
IS_VERCEL = os.getenv('VERCEL', '') == '1'

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Session Configuration - use 'null' on Vercel (no writable filesystem)
    SESSION_TYPE = 'null' if IS_VERCEL else 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_NAME = 'rag_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = IS_VERCEL  # True on Vercel (HTTPS)
    SESSION_COOKIE_SAMESITE = 'None' if IS_VERCEL else 'Lax'
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = IS_VERCEL  # True on Vercel (HTTPS)
    JWT_COOKIE_CSRF_PROTECT = False  # Simplify for development
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token_cookie'
    
    # Database - use /tmp on Vercel (only writable directory)
    DATABASE_FILE = os.getenv('DATABASE_FILE', '/tmp/rag_chatbot.db' if IS_VERCEL else 'rag_chatbot.db')
    
    # File Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/documents' if IS_VERCEL else 'documents')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB
    SUPPORTED_EXTENSIONS = (
        '.pdf', '.docx', '.txt', '.md', '.json', '.xlsx', '.xls'
    )
    
    # AI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-5.2')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    
    # Vector Database
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', '/tmp/chroma_db' if IS_VERCEL else 'chroma_db')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
    SEARCH_RESULTS_COUNT = int(os.getenv('SEARCH_RESULTS_COUNT', 5))
    
    # CORS - include Vercel URLs
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'None'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_COOKIE_SECURE = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)