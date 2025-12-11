import os
from datetime import timedelta

# Database configuration
class Config:
    # PostgreSQL connection string
    # Format: postgresql://username:password@localhost:port/database_name
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:2005@localhost:5432/ar_shop'
    
    # Disable modification tracking (saves memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Key for encoding JWT tokens (used for authorization)
    JWT_SECRET_KEY = 'secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # For development
    DEBUG = True
    TESTING = False
