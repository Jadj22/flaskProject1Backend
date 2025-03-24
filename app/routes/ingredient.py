from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.ingredient import Ingredient
from app.routes.recettes import recettes_bp  # Importé mais non utilisé ici, à vérifier si nécessaire
import logging

logger = logging.getLogger(__name__)

ingredient_bp = Blueprint("ingredients", __name__)


@ingredient_bp.route("/ingredients", methods=["GET"])
@jwt_required()  # Gardé pour limiter l'accès aux utilisateurs authentifiés
def lister_ingredients():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "", type=str)

        query = Ingredient.query
        if search:
            query = query.filter(Ingredient.nom.ilike(f"%{search}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "ingredients": [ing.to_dict() for ing in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


@ingredient_bp.route("/ingredients", methods=["POST"])
@jwt_required()
def ajouter_ingredient():
    try:
        data = request.get_json()
        logger.info(f"Données reçues: {data}")
        if not data or not data.get("nom"):
            logger.warning("Nom manquant")
            return jsonify({"message": "Le nom est requis"}), 400
        nom = data["nom"].strip()
        if Ingredient.query.filter_by(nom=nom).first():
            logger.info(f"Ingrédient existant: {nom}")
            return jsonify({"message": "Cet ingrédient existe déjà"}), 400
        ingredient = Ingredient(
            nom=nom,
            unite=data.get("unite", "g"),
            prix_unitaire=data.get("prix_unitaire")
        )
        db.session.add(ingredient)
        db.session.commit()
        logger.info(f"Ingrédient ajouté: {nom}")
        return jsonify({"message": "Ingrédient ajouté", "ingredient": ingredient.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur serveur: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


@ingredient_bp.route("/ingredients/<int:id>", methods=["GET"])
@jwt_required()
def obtenir_ingredient(id):
    """
    Obtenir les détails d'un ingrédient spécifique
    ---
    tags:
      - Ingredients
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'ingrédient
    responses:
      '200':
        description: Détails de l'ingrédient récupérés avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                aliment:
                  type: object
                  description: Détails de l'ingrédient.
      '404':
        description: Ingrédient non trouvé.
      '401':
        description: Non autorisé.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        ingredient = Ingredient.query.get_or_404(id)
        return jsonify({"aliment": ingredient.to_dict()}), 200  # Changé de "ingredient" à "aliment"
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500


@ingredient_bp.route("/ingredients/<int:id>", methods=["PUT"])
@jwt_required()
def modifier_ingredient(id):
    """
    Mettre à jour un ingrédient
    ---
    tags:
      - Ingredients
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'ingrédient
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Tomates cerises"
            unite_par_defaut:
              type: string
              example: "g"
            prix_unitaire:
              type: number
              example: 2.0
    responses:
      '200':
        description: Ingrédient mis à jour avec succès.
      '400':
        description: Données invalides.
      '401':
        description: Non autorisé.
      '404':
        description: Ingrédient non trouvé.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        ingredient = Ingredient.query.get_or_404(id)
        data = request.get_json()

        if "nom" in data:
            nom = data["nom"].strip()
            if nom != ingredient.nom and Ingredient.query.filter_by(nom=nom).first():
                return jsonify({"message": "Cet ingrédient existe déjà"}), 400
            ingredient.nom = nom

        ingredient.unite = data.get("unite", ingredient.unite)  # Corrigé : 'unite' au lieu de 'unite_par_defaut'
        ingredient.prix_unitaire = data.get("prix_unitaire", ingredient.prix_unitaire)

        db.session.commit()
        return jsonify({"message": "Ingrédient mis à jour",
                        "aliment": ingredient.to_dict()}), 200  # Changé de "ingredient" à "aliment"
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la mise à jour", "details": str(e)}), 500


@ingredient_bp.route("/ingredients/<int:id>", methods=["DELETE"])
@jwt_required()
def supprimer_ingredient(id):
    """
    Supprimer un ingrédient
    ---
    tags:
      - Ingredients
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'ingrédient
    responses:
      '200':
        description: Ingrédient supprimé avec succès.
      '401':
        description: Non autorisé.
      '404':
        description: Ingrédient non trouvé.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        ingredient = Ingredient.query.get_or_404(id)
        db.session.delete(ingredient)
        db.session.commit()
        return jsonify({"message": "Ingrédient supprimé"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "details": str(e)}), 500
