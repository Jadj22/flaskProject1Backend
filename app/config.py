from datetime import timedelta
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Config:
    # Récupération des variables d'environnement
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Vérifier que les clés secrètes et la base de données sont définies
    if not SECRET_KEY or not JWT_SECRET_KEY:
        raise ValueError("SECRET_KEY et JWT_SECRET_KEY doivent être définis dans les variables d'environnement")
    
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL doit être défini dans les variables d'environnement")

    # Correction de l'URL PostgreSQL pour Render
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # Configuration CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_RESOURCES = {
        r"/*": {
            "origins": CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization"]
        }
    }
