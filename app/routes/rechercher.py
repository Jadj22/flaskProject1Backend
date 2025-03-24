# app/routes/rechercher.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.recette import Recette
from app.models.ingredient import Ingredient
from app.models.liste_courses import ListeCourses
from app.models.inventaire import Inventaire
from app import db

rechercher_bp = Blueprint("rechercher", __name__)


@rechercher_bp.route("/rechercher", methods=["GET"])
def rechercher():
    try:
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"message": "Requête de recherche vide", "results": []}), 400

        results = []

        # Recherche dans les recettes
        recettes = Recette.query.filter(
            (Recette.titre.ilike(f"%{query}%")) | (Recette.description.ilike(f"%{query}%"))
        ).all()
        for recette in recettes:
            results.append({
                "type": "recette",
                "id": recette.id_recette,
                "nom": recette.titre,
                "description": recette.description,
            })

        # Recherche dans les ingrédients
        ingredients = Ingredient.query.filter(Ingredient.nom.ilike(f"%{query}%")).all()
        for ingredient in ingredients:
            results.append({
                "type": "ingredient",
                "id": ingredient.id_ingredient,
                "nom": ingredient.nom,
            })

        # Recherche dans les listes de courses
        courses = ListeCourses.query.filter(ListeCourses.nom.ilike(f"%{query}%")).all()
        for course in courses:
            results.append({
                "type": "course",
                "id": course.id_liste,
                "nom": course.nom,
            })

        # Recherche dans les inventaires
        inventaires = Inventaire.query.filter(Inventaire.nom.ilike(f"%{query}%")).all()
        for inventaire in inventaires:
            results.append({
                "type": "inventaire",
                "id": inventaire.id_inventaire,
                "nom": inventaire.nom,
            })

        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la recherche", "details": str(e)}), 500
