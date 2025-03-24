from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger
import logging
from .config import Config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialiser les extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Appliquer la configuration CORS
    CORS(app, resources=Config.CORS_RESOURCES, supports_credentials=True)

    # Configuration du logging
    if not app.config.get('TESTING'):
        if not hasattr(logging, "app_handler_configured"):
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler("app.log"),
                    logging.StreamHandler()
                ]
            )
            logging.app_handler_configured = True
    logger = logging.getLogger(__name__)

    # Configuration Swagger
    app.config["SWAGGER"] = {
        "title": "Mon API de Recettes",
        "description": "API pour gérer des recettes avec authentification",
        "version": "1.0.0",
        "uiversion": 3,
    }
    Swagger(app)

    # Importer et enregistrer les blueprints
    from .routes.auth import auth_bp
    from .routes.recettes import recettes_bp
    from .routes.inventaires import inventaire_bp
    from .routes.ingredient import ingredient_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(recettes_bp)
    app.register_blueprint(inventaire_bp)
    app.register_blueprint(ingredient_bp)

    # Gestion des erreurs JWT
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        logger.warning("Requête non autorisée : token manquant")
        return jsonify({"message": "Token manquant, veuillez vous connecter"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning(f"Token invalide : {str(error)}")
        return jsonify({"message": "Token invalide"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning(f"Token expiré pour utilisateur : {jwt_payload['sub']}")
        return jsonify({"message": "Token expiré, veuillez vous reconnecter"}), 401

    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            return "", 200

    return app
