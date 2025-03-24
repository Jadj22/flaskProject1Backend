import re
from flask import Blueprint, request, jsonify
from ..models.utilisateur import Utilisateur
from .. import db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import logging
from flask_jwt_extended import jwt_optional, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

# Configurer le logging uniquement si pas en mode test
if not hasattr(logging, "auth_handler_configured"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("auth.log"),
            logging.StreamHandler()
        ]
    )
    logging.auth_handler_configured = True
logger = logging.getLogger(__name__)


# Fonctions de validation (inchangées)
def validate_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email)), "Format d'email invalide" if not re.match(pattern, email) else ""


def validate_password(password):
    if not password:
        return True, ""  # Allow empty password for optional updates
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    return True, ""


def validate_nom(nom):
    if not nom:
        return False, "Le nom est requis"
    if len(nom) > 100:
        return False, "Le nom ne doit pas dépasser 100 caractères"
    return True, ""


@auth_bp.route("/inscription", methods=["POST"])
def inscription():
    try:
        data = request.get_json()
        email, mot_de_passe, nom = data.get("email", "").strip(), data.get("mot_de_passe", ""), data.get("nom",
                                                                                                         "").strip()

        email_valid, email_msg = validate_email(email)
        if not email_valid:
            return jsonify({"message": email_msg}), 400
        if len(mot_de_passe) < 8:
            return jsonify({"message": "Mot de passe trop court (min 8 caractères)"}), 400
        if not nom or len(nom) > 100:
            return jsonify({"message": "Nom requis (max 100 caractères)"}), 400

        if Utilisateur.query.filter_by(email=email).first():
            return jsonify({"message": "Email déjà utilisé"}), 400

        utilisateur = Utilisateur(email=email, nom=nom)
        utilisateur.set_password(mot_de_passe)
        db.session.add(utilisateur)
        db.session.commit()
        return jsonify({"message": "Inscription réussie", "utilisateur": utilisateur.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur inscription: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


@auth_bp.route("/connexion", methods=["POST"])
def connexion():
    """
        Connexion d'un utilisateur
        ---
        tags:
          - Authentification
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                email:
                  type: string
                  description: L'email de l'utilisateur
                  example: dodo@gmail.com
                mot_de_passe:
                  type: string
                  description: Le mot de passe de l'utilisateur
                  example: "12345678"
              required:
                - email
                - mot_de_passe
        responses:
          200:
            description: Connexion réussie
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  description: Token d'accès JWT
                refresh_token:
                  type: string
                  description: Token de rafraîchissement JWT
                utilisateur:
                  type: object
                  properties:
                    id_utilisateur:
                      type: integer
                    email:
                      type: string
                    nom:
                      type: string
          400:
            description: Données manquantes ou invalides
          401:
            description: Email ou mot de passe incorrect
          500:
            description: Erreur interne du serveur
        """
    if request.method == "OPTIONS":
        return "", 204
    try:
        data = request.get_json()
        if not data:
            logger.warning("Requête de connexion sans données")
            return jsonify({"message": "Données manquantes"}), 400

        email = data.get("email", "").strip()
        mot_de_passe = data.get("mot_de_passe", "")

        email_valid, email_message = validate_email(email)
        if not email_valid:
            logger.warning(f"Échec de validation email : {email_message} - Email: {email}")
            return jsonify({"message": email_message}), 400

        if not mot_de_passe:
            logger.warning(f"Mot de passe manquant - Email: {email}")
            return jsonify({"message": "Le mot de passe est requis"}), 400

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or not utilisateur.check_password(mot_de_passe):
            logger.warning(f"Échec de connexion - Identifiants incorrects pour : {email}")
            return jsonify({"message": "Email ou mot de passe incorrect"}), 401

        access_token = create_access_token(identity=str(utilisateur.id_utilisateur))
        refresh_token = create_refresh_token(identity=str(utilisateur.id_utilisateur))
        logger.info(f"Connexion réussie pour : {email}")
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "utilisateur": utilisateur.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la connexion : {str(e)}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
        Rafraîchir un token d'accès
        ---
        tags:
          - Authentification
        security:
          - Bearer: []
        responses:
          200:
            description: Nouveau token d'accès généré
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  description: Nouveau token d'accès JWT
          401:
            description: Refresh token invalide ou manquant
          500:
            description: Erreur interne du serveur
        """
    if request.method == "OPTIONS":
        return "", 204
    try:
        utilisateur_id = get_jwt_identity()
        nouveau_access_token = create_access_token(identity=utilisateur_id)
        logger.info(f"Token rafraîchi pour utilisateur ID : {utilisateur_id}")
        return jsonify({"access_token": nouveau_access_token}), 200
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement : {str(e)}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500


@auth_bp.route("/profil", methods=["GET", "PUT"])
@jwt_required()
def profil():
    """
    Récupérer ou mettre à jour le profil de l'utilisateur connecté
    ---
    tags:
      - Authentification
    responses:
      '200':
        description: Profil récupéré ou mis à jour avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                utilisateur:
                  type: object
                  properties:
                    id_utilisateur:
                      type: integer
                    email:
                      type: string
                    nom:
                      type: string
      '400':
        description: Données invalides.
      '401':
        description: Non autorisé.
      '500':
        description: Erreur interne du serveur.
    security:
      - bearerAuth: []
    """
    if request.method == "OPTIONS":
        return "", 204
    try:
        utilisateur_id = get_jwt_identity()
        utilisateur = Utilisateur.query.get_or_404(utilisateur_id)
        logger.info(f"Accès au profil pour : {utilisateur.email} (Méthode: {request.method}, Path: {request.path})")

        if request.method == "GET":
            return jsonify({"utilisateur": utilisateur.to_dict()}), 200
        elif request.method == "PUT":
            data = request.get_json()
            nom = data.get("nom", "").strip()
            mot_de_passe = data.get("mot_de_passe", "").strip()

            nom_valid, nom_msg = validate_nom(nom)
            if not nom_valid:
                return jsonify({"message": nom_msg}), 400

            password_valid, password_msg = validate_password(mot_de_passe)
            if not password_valid:
                return jsonify({"message": password_msg}), 400

            utilisateur.nom = nom
            if mot_de_passe:
                utilisateur.set_password(mot_de_passe)

            db.session.commit()
            logger.info(f"Profil mis à jour pour : {utilisateur.email}")
            return jsonify({
                "message": "Profil mis à jour avec succès",
                "utilisateur": utilisateur.to_dict()
            }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'accès/mise à jour du profil : {str(e)}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500


@auth_bp.route("/deconnexion", methods=["POST"])
def deconnexion():
    """
              Déconnecter l'utilisateur
    ---
    tags:
      - Authentification
    responses:
      '200':
        description: Déconnexion réussie.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Message de confirmation de déconnexion.
      '401':
        description: Non autorisé. Jeton JWT manquant ou invalide.
      '404':
        description: Utilisateur non trouvé.
      '500':
        description: Erreur interne du serveur.
    security:
      - bearerAuth: []
    """
    if request.method == "OPTIONS":
        return "", 204
    try:
        # Vérifier si un token est présent et valide sans lever d'erreur
        verify_jwt_in_request(optional=True)
        utilisateur_id = get_jwt_identity()  # Retourne None si pas de token valide
        if utilisateur_id:
            utilisateur = Utilisateur.query.get_or_404(utilisateur_id)
            logger.info(f"Déconnexion réussie pour : {utilisateur.email}")
        else:
            logger.info("Déconnexion sans token fourni ou token invalide")
        return jsonify({"message": "Déconnexion réussie"}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion : {str(e)}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500
