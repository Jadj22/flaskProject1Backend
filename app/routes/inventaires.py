from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.ingredient import Ingredient
from app.models.inventaire import Inventaire
from app.models.inventaire_ingredient import InventaireIngredient
from app.models.liste_courses_item import ListeCoursesItem
from app.models.liste_courses import ListeCourses
from app.models.recette import Recette
import re
import logging

from app.models.recette_ingredient import RecetteIngredient
from app.models.recette_utilisateur import RecetteUtilisateur

inventaire_bp = Blueprint("inventaires", __name__)

logger = logging.getLogger(__name__)
UNITES_VALIDES = {"g", "kg", "L", "mL", "cl", "unités"}


# Fonction utilitaire pour convertir les unités
def convertir_unites(quantite, unite_source, unite_cible="g"):
    conversions = {"g": 1, "kg": 1000, "ml": 1, "l": 1000, "cl": 10, "unites": 1}
    unite_source = unite_source.lower()
    unite_cible = unite_cible.lower()

    # Vérification des unités valides
    if unite_source not in conversions or unite_cible not in conversions:
        raise ValueError(f"Unité invalide : {unite_source} ou {unite_cible}")

    # Conversion
    quantite_base = quantite * conversions[unite_source]
    return quantite_base / conversions[unite_cible]


# Créer un inventaire
@inventaire_bp.route("/inventaires", methods=["POST"])
@jwt_required()
def creer_inventaire():
    try:
        data = request.get_json()
        if not data or not data.get("nom") or len(data["nom"].strip()) > 100:
            return jsonify({"message": "Le nom est requis et doit être ≤ 100 caractères"}), 400
        inventaire = Inventaire(
            nom=data["nom"].strip(),
            id_utilisateur=int(get_jwt_identity()),
            publique=data.get("publique", False)
        )
        db.session.add(inventaire)
        db.session.commit()
        return jsonify({"message": "Inventaire créé", "inventaire": inventaire.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


@inventaire_bp.route("/inventaires/<int:id>/ingredients", methods=["POST"])
@jwt_required()
def ajouter_ingredient_inventaire(id):
    """
    Ajouter un ingrédient à un inventaire
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            id_ingredient:
              type: integer
              example: 1
            quantite_disponible:
              type: number
              example: 150
            unite:
              type: string
              example: "g"
            prix_unitaire:
              type: number
              example: 2.5
    responses:
      '201':
        description: Ingrédient ajouté
      '400':
        description: Données invalides
      '403':
        description: Non autorisé
      '404':
        description: Ressource non trouvée
      '500':
        description: Erreur interne
    """
    # try:
    #     inventaire = Inventaire.query.get_or_404(id)
    #     if inventaire.id_utilisateur != int(get_jwt_identity()):
    #         return jsonify({"message": "Non autorisé"}), 403
    #
    #     data = request.get_json()
    #     if not data or "id_ingredient" not in data or "quantite_disponible" not in data or "unite" not in data:
    #         return jsonify({"message": "id_ingredient, quantite_disponible et unite sont requis"}), 400
    #
    #     ingredient = Ingredient.query.get_or_404(data["id_ingredient"])
    #     quantite = float(data["quantite_disponible"])  # Conversion en float
    #     if quantite <= 0:
    #         return jsonify({"message": "La quantité doit être positive"}), 400
    #
    #     nouvel_ingredient = InventaireIngredient(
    #         id_inventaire=inventaire.id_inventaire,
    #         id_ingredient=ingredient.id_ingredient,
    #         quantite_disponible=quantite,
    #         unite=data["unite"],
    #         prix_unitaire=data.get("prix_unitaire")
    #     )
    #     db.session.add(nouvel_ingredient)
    #     db.session.commit()
    #     return jsonify({"message": "Ingrédient ajouté", "ingredient": nouvel_ingredient.to_dict()}), 201
    # except ValueError:
    #     return jsonify({"message": "Quantité invalide (doit être un nombre)"}), 400
    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({"message": "Erreur lors de l'ajout", "details": str(e)}), 500

    try:
        data = request.get_json()
        inventaire = Inventaire.query.get_or_404(id)
        if inventaire.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Accès non autorisé"}), 403
        inv_ing = InventaireIngredient(
            id_inventaire=id,
            id_ingredient=data["id_ingredient"],
            quantite_disponible=data.get("quantite_disponible", 0),
            unite=data.get("unite", "g"),
            prix_unitaire=data.get("prix_unitaire")
        )
        db.session.add(inv_ing)
        db.session.commit()
        return jsonify(inv_ing.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de l'ajout", "details": str(e)}), 500


@inventaire_bp.route("/inventaires", methods=["GET"])
@jwt_required()
def lister_inventaires():
    """
    Lister les inventaires d'un utilisateur
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    responses:
      '200':
        description: Liste des inventaires récupérée avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                inventaires:
                  type: array
                  items:
                    type: object
                    description: Détails de l'inventaire.
      '401':
        description: Non autorisé. Jeton JWT manquant ou invalide.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        id_utilisateur = get_jwt_identity()
        inventaires = Inventaire.query.filter_by(id_utilisateur=int(id_utilisateur)).all()
        return jsonify({"inventaires": [inventaire.to_dict() for inventaire in inventaires]}), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des inventaires", "details": str(e)}), 500


@inventaire_bp.route("/inventaires/<int:id>", methods=["GET"])
@jwt_required()
def obtenir_inventaire(id):
    """
    Obtenir un inventaire
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'inventaire à obtenir.
    responses:
      '200':
        description: Inventaire récupéré avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                inventaire:
                  type: object
                  description: Détails de l'inventaire.
      '401':
        description: Non autorisé. Jeton JWT manquant ou invalide.
      '403':
        description: Non autorisé. L'utilisateur n'est pas le propriétaire de l'inventaire.
      '404':
        description: Inventaire non trouvé.
      '500':
        description: Erreur interne du serveur.
    """
    inventaire = Inventaire.query.get_or_404(id)
    if inventaire.id_utilisateur != int(get_jwt_identity()):
        return jsonify({"message": "Non autorisé"}), 403
    return jsonify({"inventaire": inventaire.to_dict()}), 200


@inventaire_bp.route("/inventaires/<int:id>", methods=["PUT"])
@jwt_required()
def modifier_inventaire(id):
    """
    Modifier un inventaire
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'inventaire à modifier.
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              description: Nouveau nom de l'inventaire.
              example: "Inventaire de la cuisine mis à jour"
    responses:
      '200':
        description: Inventaire mis à jour avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Inventaire mis à jour avec succès"
                inventaire:
                  type: object
                  description: Détails de l'inventaire mis à jour.
      '400':
        description: Données de requête invalides.
      '401':
        description: Non autorisé. Jeton JWT manquant ou invalide.
      '403':
        description: Non autorisé. L'utilisateur n'est pas le propriétaire de l'inventaire.
      '404':
        description: Inventaire non trouvé.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        inventaire = Inventaire.query.get_or_404(id)
        if inventaire.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403

        data = request.get_json()
        if not data or "nom" not in data or not data["nom"]:
            return jsonify({"message": "Le nom est requis"}), 400

        inventaire.nom = data["nom"]
        db.session.commit()
        return jsonify({"message": "Inventaire mis à jour avec succès", "inventaire": inventaire.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la mise à jour", "details": str(e)}), 500


# Générer une liste de courses
@inventaire_bp.route("/inventaires/<int:id>/courses", methods=["GET"])
@jwt_required()
def generer_liste_courses(id):
    try:
        id_utilisateur = int(get_jwt_identity())
        inventaire = Inventaire.query.get_or_404(id)
        if inventaire.id_utilisateur != id_utilisateur:
            return jsonify({"message": "Accès non autorisé à cet inventaire"}), 403

        id_recette = request.args.get("id_recette", type=int)
        if not id_recette:
            return jsonify({"message": "L'identifiant de la recette est requis"}), 400

        recette = Recette.query.get_or_404(id_recette)
        if recette.id_utilisateur != id_utilisateur and not RecetteUtilisateur.query.filter_by(
                id_recette=id_recette, id_utilisateur=id_utilisateur
        ).first():
            return jsonify({"message": "Accès non autorisé à cette recette"}), 403

        ingredients_recette = RecetteIngredient.query.filter_by(id_recette=id_recette).all()
        if not ingredients_recette:
            return jsonify({"message": "Aucun ingrédient dans cette recette"}), 400

        ingredients_inventaire = {
            ing.id_ingredient: ing for ing in InventaireIngredient.query.filter_by(id_inventaire=id).all()
        }

        liste_courses = []
        total_cout = 0.0
        for ing_recette in ingredients_recette:
            ing_inventaire = ingredients_inventaire.get(ing_recette.id_ingredient)
            quantite_requise = ing_recette.quantite
            unite_recette = ing_recette.unite.lower()
            quantite_manquante = quantite_requise

            if ing_inventaire:
                unite_inventaire = ing_inventaire.unite.lower()
                quantite_requise_base = convertir_unites(quantite_requise, unite_recette)
                quantite_disponible_base = convertir_unites(ing_inventaire.quantite_disponible, unite_inventaire)
                quantite_manquante_base = max(0, quantite_requise_base - quantite_disponible_base)
                quantite_manquante = convertir_unites(quantite_manquante_base, "g",
                                                      unite_recette) if quantite_manquante_base > 0 else 0

            if quantite_manquante > 0:
                prix_unitaire = ing_inventaire.prix_unitaire if ing_inventaire and ing_inventaire.prix_unitaire else 0.0
                cout = quantite_manquante * prix_unitaire
                total_cout += cout
                liste_courses.append({
                    "id_ingredient": ing_recette.id_ingredient,
                    "nom": ing_recette.ingredient.nom,
                    "quantite_manquante": quantite_manquante,
                    "unite": ing_recette.unite,
                    "prix_unitaire": prix_unitaire,
                    "cout": cout
                })

        # Persister la liste
        nouvelle_liste = ListeCourses(
            nom=f"Liste pour {recette.titre} (Inventaire {inventaire.nom})",
            id_utilisateur=id_utilisateur,
            id_recette=id_recette,
            id_inventaire=id
        )
        db.session.add(nouvelle_liste)
        db.session.flush()

        for item in liste_courses:
            liste_item = ListeCoursesItem(
                id_liste=nouvelle_liste.id_liste,
                id_ingredient=item["id_ingredient"],
                quantite=item["quantite_manquante"],
                unite=item["unite"]
            )
            db.session.add(liste_item)

        db.session.commit()

        logger.info(f"Liste de courses générée et sauvegardée : {nouvelle_liste.id_liste}")
        # return jsonify({
        #     "liste_courses": liste_courses,
        #     "total_cout": total_cout,
        #     "id_liste": nouvelle_liste.id_liste
        # }), 200
        return jsonify({
            "id_liste": nouvelle_liste.id_liste,
            "nom": nouvelle_liste.nom,
            "items": [
                {"id_ingredient": item["id_ingredient"], "nom": item["nom"], "quantite": item["quantite_manquante"],
                 "unite": item["unite"]} for item in liste_courses],
            "total_cout": total_cout
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur génération liste courses: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


@inventaire_bp.route("/courses", methods=["GET"])
@jwt_required()
def obtenir_liste_courses_pagination():
    """
    Lister les listes de courses d'un utilisateur avec pagination et recherche
    ---
    tags:
      - Courses
    security:
      - bearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Numéro de la page
      - name: per_page
        in: query
        type: integer
        required: false
        default: 10
        description: Nombre d'éléments par page
      - name: search
        in: query
        type: string
        required: false
        description: Terme de recherche dans le nom
    responses:
      '200':
        description: Liste des courses récupérée avec succès
        content:
          application/json:
            schema:
              type: object
              properties:
                courses:
                  type: array
                  items:
                    type: object
                    properties:
                      id_liste:
                        type: integer
                      nom:
                        type: string
                      date_creation:
                        type: string
                      id_utilisateur:
                        type: integer
                      id_recette:
                        type: integer
                      id_inventaire:
                        type: integer
                      items:
                        type: array
                        items:
                          type: object
                total:
                  type: integer
                pages:
                  type: integer
                current_page:
                  type: integer
      '401':
        description: Non autorisé
      '500':
        description: Erreur interne
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "", type=str)

        id_utilisateur = int(get_jwt_identity())
        query = ListeCourses.query.filter_by(id_utilisateur=id_utilisateur)

        if search:
            query = query.filter(ListeCourses.nom.ilike(f"%{search}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        courses = pagination.items
        total = pagination.total
        pages = pagination.pages

        return jsonify({
            "courses": [course.to_dict() for course in courses],
            "total": total,
            "pages": pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des listes de courses", "details": str(e)}), 500


@inventaire_bp.route("/inventaires/<int:id>", methods=["DELETE"])
@jwt_required()
def supprimer_inventaire(id):
    """
    Supprimer un inventaire
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'inventaire à supprimer.
    responses:
      '200':
        description: Inventaire supprimé avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Inventaire supprimé avec succès"
      '401':
        description: Non autorisé. Jeton JWT manquant ou invalide.
      '403':
        description: Non autorisé. L'utilisateur n'est pas le propriétaire de l'inventaire.
      '404':
        description: Inventaire non trouvé.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        inventaire = Inventaire.query.get_or_404(id)
        if inventaire.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403

        db.session.delete(inventaire)
        db.session.commit()
        return jsonify({"message": "Inventaire supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "details": str(e)}), 500


@inventaire_bp.route("/courses", methods=["GET"])
@jwt_required()
def lister_courses_generale():
    """
    Lister les courses générales
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    responses:
      '200':
        description: Liste de courses générale générée avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                liste_courses:
                  type: array
                  items:
                    type: object
                    properties:
                      nom:
                        type: string
                        description: Nom de l'ingrédient.
                      quantite_manquante:
                        type: string
                        description: Quantité manquante de l'ingrédient.
                      prix_unitaire:
                        type: number
                        description: Prix unitaire de l'ingrédient.
                      cout:
                        type: number
                        description: Coût total de l'ingrédient.
                total_cout:
                  type: number
                  description: Coût total de la liste de courses.
      '401':
        description: Non autorisé. Jeton JWT manquant ou invalide.
      '404':
        description: Aucune recette trouvée.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        id_utilisateur = int(get_jwt_identity())

        # Récupérer toutes les recettes de l'utilisateur
        recettes = Recette.query.filter_by(id_utilisateur=id_utilisateur).all()
        if not recettes:
            return jsonify({"message": "Aucune recette trouvée"}), 404

        # Récupérer tous les inventaires de l'utilisateur
        inventaires = Inventaire.query.filter_by(id_utilisateur=id_utilisateur).all()

        # Fonction pour convertir les quantités (réutilisée)
        def convertir_quantite(quantite, unite):
            quantite_num = float(quantite.split(unite)[0])
            conversions = {"g": 1, "kg": 1000, "cl": 10, "ml": 1, "unites": 1}
            return quantite_num * conversions.get(unite.lower(), 1)

        # Agréger les ingrédients nécessaires de toutes les recettes
        ingredients_requis = {}
        for recette in recettes:
            for ri in recette.ingredients:
                quantite = ri.quantite
                unite = quantite[-1] if quantite[-1] in "gklmu" else "g"
                quantite_num = convertir_quantite(quantite, unite)
                if ri.id_ingredient in ingredients_requis:
                    ingredients_requis[ri.id_ingredient]["quantite"] += quantite_num
                else:
                    ingredients_requis[ri.id_ingredient] = {"quantite": quantite_num, "unite": unite}

        # Agréger les ingrédients disponibles de tous les inventaires
        ingredients_disponibles = {}
        for inventaire in inventaires:
            for ii in inventaire.ingredients:
                quantite = ii.quantite_disponible
                unite = quantite[-1] if quantite[-1] in "gklmu" else "g"
                quantite_num = convertir_quantite(quantite, unite)
                if ii.id_ingredient in ingredients_disponibles:
                    ingredients_disponibles[ii.id_ingredient]["quantite"] += quantite_num
                else:
                    ingredients_disponibles[ii.id_ingredient] = {"quantite": quantite_num, "unite": unite}

        # Générer la liste de courses générale
        liste_courses = []
        total_cout = 0.0
        for id_ingredient, data_requis in ingredients_requis.items():
            data_dispo = ingredients_disponibles.get(id_ingredient, {"quantite": 0, "unite": "g"})
            quantite_manquante = max(0, data_requis["quantite"] - data_dispo["quantite"])
            if quantite_manquante > 0:
                ingredient = Ingredient.query.get(id_ingredient)
                # Utiliser un prix moyen ou par défaut
                prix = next((ii.prix_unitaire for inv in inventaires for ii in inv.ingredients
                             if ii.id_ingredient == id_ingredient), 0.0)
                cout = quantite_manquante * (prix / 1000) if data_requis["unite"] == "kg" else quantite_manquante * prix
                unite_sortie = data_requis["unite"] if data_requis["unite"] != "kg" else "g"
                quantite_manquante_str = f"{int(quantite_manquante)}{unite_sortie}"
                liste_courses.append({
                    "nom": ingredient.nom,
                    "quantite_manquante": quantite_manquante_str,
                    "prix_unitaire": prix,
                    "cout": cout
                })
                total_cout += cout

        return jsonify({
            "liste_courses": liste_courses,
            "total_cout": round(total_cout, 2)
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la génération", "details": str(e)}), 500


@inventaire_bp.route("/courses", methods=["POST"])
@jwt_required()
def creer_liste_courses():
    """
    Créer une liste de courses
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Courses de la semaine"
            id_recette:
              type: integer
              example: 1
            items:
              type: array
              items:
                type: object
                properties:
                  id_ingredient:
                    type: integer
                    example: 1
                  quantite:
                    type: number
                    example: 2
                  unite:
                    type: string
                    example: "unites"
    responses:
      '201':
        description: Liste créée
      '400':
        description: Données invalides
      '401':
        description: Non autorisé
      '500':
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not data or "nom" not in data or not isinstance(data["nom"], str):
            return jsonify({"message": "Le nom est requis et doit être une chaîne"}), 400

        id_utilisateur = int(get_jwt_identity())
        liste = ListeCourses(
            nom=data["nom"].strip(),
            id_utilisateur=id_utilisateur,
            id_recette=data.get("id_recette")
        )
        db.session.add(liste)
        db.session.flush()

        items = data.get("items", [])
        if not isinstance(items, list):
            return jsonify({"message": "Les items doivent être une liste"}), 400

        for item in items:
            if not all(k in item for k in ["id_ingredient", "quantite", "unite"]):
                return jsonify({"message": "Chaque item doit avoir id_ingredient, quantite et unite"}), 400
            try:
                quantite = float(item["quantite"])
                if quantite <= 0:
                    return jsonify({"message": "La quantité doit être positive"}), 400
            except (ValueError, TypeError):
                return jsonify({"message": f"Quantité invalide pour l'item {item}: doit être un nombre"}), 400

            liste_item = ListeCoursesItem(
                id_liste=liste.id_liste,
                id_ingredient=int(item["id_ingredient"]),
                quantite=quantite,
                unite=item["unite"]
            )
            db.session.add(liste_item)

        db.session.commit()
        return jsonify({"message": "Liste créée", "liste": liste.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la création", "details": str(e)}), 500


@inventaire_bp.route("/courses/<int:id>", methods=["GET"])
@jwt_required()
def obtenir_liste_courses(id):
    """
    Obtenir une liste de courses spécifique
    ---
    tags:
      - Courses
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la liste de courses à obtenir
    responses:
      '200':
        description: Liste de courses récupérée avec succès
        content:
          application/json:
            schema:
              type: object
              properties:
                id_liste:
                  type: integer
                nom:
                  type: string
                date_creation:
                  type: string
                id_utilisateur:
                  type: integer
                id_recette:
                  type: integer
                id_inventaire:
                  type: integer
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      id_item:
                        type: integer
                      id_ingredient:
                        type: integer
                      nom_ingredient:
                        type: string
                      quantite:
                        type: number
                      unite:
                        type: string
      '403':
        description: Non autorisé
      '404':
        description: Liste non trouvée
      '500':
        description: Erreur interne
    """
    try:
        id_utilisateur = int(get_jwt_identity())
        liste = ListeCourses.query.get_or_404(id)
        if liste.id_utilisateur != id_utilisateur:
            return jsonify({"message": "Accès non autorisé à cette liste"}), 403

        return jsonify(liste.to_dict()), 200
    except Exception as e:
        logger.error(f"Erreur récupération liste courses {id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


# app/routes/inventaires.py
@inventaire_bp.route("/inventaires/<int:id>/ingredients/<int:id_ingredient>", methods=["PUT"])
@jwt_required()
def modifier_ingredient_inventaire(id, id_ingredient):
    """
    Modifier un ingrédient dans un inventaire
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: id_ingredient
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            quantite_disponible:
              type: number
              example: 150
            unite:
              type: string
              example: "g"
            prix_unitaire:
              type: number
              example: 2.5
    responses:
      '200':
        description: Ingrédient mis à jour
      '400':
        description: Données invalides
      '403':
        description: Non autorisé
      '404':
        description: Ressource non trouvée
      '500':
        description: Erreur interne
    """
    try:
        inventaire = Inventaire.query.get_or_404(id)
        if inventaire.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403

        ingredient_inventaire = InventaireIngredient.query.filter_by(
            id_inventaire_ingredient=id_ingredient, id_inventaire=id
        ).first_or_404()

        data = request.get_json()
        if not data or "quantite_disponible" not in data or "unite" not in data:
            return jsonify({"message": "quantite_disponible et unite sont requis"}), 400

        quantite = float(data["quantite_disponible"])
        if quantite < 0:
            return jsonify({"message": "La quantité doit être positive ou zéro"}), 400

        ingredient_inventaire.quantite_disponible = quantite
        ingredient_inventaire.unite = data["unite"]
        ingredient_inventaire.prix_unitaire = data.get("prix_unitaire")

        db.session.commit()
        return jsonify({"message": "Ingrédient mis à jour", "ingredient": ingredient_inventaire.to_dict()}), 200
    except ValueError:
        return jsonify({"message": "Quantité invalide (doit être un nombre)"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la mise à jour", "details": str(e)}), 500


@inventaire_bp.route("/inventaires/<int:id>/ingredients/<int:id_ingredient>", methods=["DELETE"])
@jwt_required()
def supprimer_ingredient_inventaire(id, id_ingredient):
    """
    Supprimer un ingrédient d'un inventaire
    ---
    tags:
      - Inventaires
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: id_ingredient
        in: path
        type: integer
        required: true
    responses:
      '200':
        description: Ingrédient supprimé
      '403':
        description: Non autorisé
      '404':
        description: Ressource non trouvée
      '500':
        description: Erreur interne
    """
    try:
        inventaire = Inventaire.query.get_or_404(id)
        if inventaire.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403

        ingredient_inventaire = InventaireIngredient.query.filter_by(
            id_inventaire_ingredient=id_ingredient, id_inventaire=id
        ).first_or_404()

        db.session.delete(ingredient_inventaire)
        db.session.commit()
        return jsonify({"message": "Ingrédient supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "details": str(e)}), 500


def validate_quantite(quantite):
    pattern = r"^\d+\s*(g|kg|cl|ml|unité?s)?$"
    return bool(re.match(pattern, quantite))
