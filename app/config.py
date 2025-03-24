from datetime import timedelta
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "b3e3b0e4-8180-4b27-8f26-bb9173c2fa45")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/data_recettes")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "f4c5a682-d96b-4c24-bcdb-4fe6d927ff58")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # Configuration CORS simplifiée
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://192.168.110.1:3000').split(',')
    CORS_RESOURCES = {
        r"/*": {
            "origins": CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization"]
        }
    }