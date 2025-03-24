from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.ingredient import Ingredient
from app.models.recette import Recette
from app.models.recette_ingredient import RecetteIngredient
from app.models.etape import Etape
import logging
from random import sample, random

from app.models.recette_utilisateur import RecetteUtilisateur

recettes_bp = Blueprint("recettes", __name__)

logger = logging.getLogger(__name__)
UNITES_VALIDES = {"g", "kg", "L", "mL", "cl", "unités"}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("recettes.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Créer une recette
@recettes_bp.route("/recettes", methods=["POST"])
@jwt_required()
def creer_recette():
    try:
        data = request.get_json()
        if not data or "titre" not in data or not data["titre"]:
            return jsonify({"message": "Le titre est requis"}), 400

        id_utilisateur = int(get_jwt_identity())
        nouvelle_recette = Recette(
            titre=data["titre"].strip(),
            description=data.get("description"),
            id_utilisateur=id_utilisateur,
            publique=data.get("publique", False),
            temps_preparation=data.get("temps_preparation"),
            temps_cuisson=data.get("temps_cuisson")
        )
        db.session.add(nouvelle_recette)
        db.session.flush()

        ingredients_vus = set()
        for ing in data.get("ingredients", []):
            if "nom" not in ing or "quantite" not in ing or "unite" not in ing:
                return jsonify({"message": "Chaque ingrédient doit avoir nom, quantite et unite"}), 400
            if ing["unite"] not in UNITES_VALIDES:
                return jsonify({"message": f"Unité invalide: {ing['unite']}"}), 400
            nom = ing["nom"].strip()
            if nom in ingredients_vus:
                return jsonify({"message": f"Ingrédient en doublon: {nom}"}), 400
            ingredients_vus.add(nom)

            ingredient = Ingredient.query.filter_by(nom=nom).first() or Ingredient(nom=nom)
            if not ingredient.id_ingredient:
                db.session.add(ingredient)
                db.session.flush()

            recette_ingredient = RecetteIngredient(
                id_recette=nouvelle_recette.id_recette,
                id_ingredient=ingredient.id_ingredient,
                quantite=float(ing["quantite"]),
                unite=ing["unite"]
            )
            db.session.add(recette_ingredient)

        if "etapes" in data:
            for i, etape_data in enumerate(data["etapes"], 1):
                if "instruction" not in etape_data:
                    return jsonify({"message": "Chaque étape doit avoir une instruction"}), 400
                etape = Etape(
                    id_recette=nouvelle_recette.id_recette,
                    ordre=etape_data.get("ordre", i),
                    instruction=etape_data["instruction"]
                )
                db.session.add(etape)

        db.session.commit()
        logger.info(f"Recette créée: {nouvelle_recette.titre} par utilisateur {id_utilisateur}")
        return jsonify({"message": "Recette créée", "recette": nouvelle_recette.to_dict()}), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": f"Valeur invalide: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur création recette: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


# Obtenir une recette
@recettes_bp.route("/recettes/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def obtenir_recette(id):
    try:
        recette = Recette.query.get_or_404(id)
        user_id = get_jwt_identity()
        logger.debug(f"Tentative accès recette {id} - Publique: {recette.publique}, User: {user_id}")
        if not recette.publique and (not user_id or recette.id_utilisateur != int(user_id)):
            return jsonify({"message": "Accès non autorisé"}), 403
        return jsonify({"recette": recette.to_dict()}), 200
    except Exception as e:
        logger.error(f"Erreur récupération recette {id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


# Route modifiée : Lister les recettes de l'utilisateur connecté (avec filtre publique/privée)
@recettes_bp.route("/recettes/", methods=["GET"])
@jwt_required()
def lister_recettes():
    """
    Lister les recettes créées par l'utilisateur connecté (publiques ou privées)
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        description: Numéro de la page (par défaut 1).
      - name: per_page
        in: query
        type: integer
        description: Nombre de recettes par page (par défaut 10).
      - name: titre
        in: query
        type: string
        description: Filtrer les recettes par titre.
      - name: publique
        in: query
        type: boolean
        description: Filtrer par statut public (true pour publiques, false pour privées, absent pour toutes).
    responses:
      '200':
        description: Liste des recettes de l'utilisateur récupérée avec succès.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        titre_filter = request.args.get("titre", "")
        publique_filter = request.args.get("publique", type=lambda v: v.lower() == "true" if v is not None else None)
        id_utilisateur = int(get_jwt_identity())

        query = Recette.query.filter_by(id_utilisateur=id_utilisateur)
        if titre_filter:
            query = query.filter(Recette.titre.ilike(f"%{titre_filter}%"))
        if publique_filter is not None:
            query = query.filter_by(publique=publique_filter)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "recettes": [recette.to_dict() for recette in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500


# Route : Lister les recettes privées
@recettes_bp.route("/recettes/privees", methods=["GET"])
@jwt_required()
def lister_recettes_privees():
    """
    Lister les recettes privées de l'utilisateur
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    responses:
      '200':
        description: Liste des recettes privées récupérée avec succès.
      '401':
        description: Non autorisé.
      '500':
        description: Erreur interne du serveur.
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        titre_filter = request.args.get("titre", "")
        id_utilisateur = int(get_jwt_identity())

        query = Recette.query.filter_by(id_utilisateur=id_utilisateur, publique=False)
        if titre_filter:
            query = query.filter(Recette.titre.ilike(f"%{titre_filter}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "recettes": [recette.to_dict() for recette in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500


# Route : Supprimer une recette
@recettes_bp.route("/recettes/<int:id>", methods=["DELETE"])
@jwt_required()
def supprimer_recette(id):
    """
    Supprimer une recette
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      '200':
        description: Recette supprimée avec succès.
      '401':
        description: Non autorisé.
      '403':
        description: Non autorisé.
      '404':
        description: Recette non trouvée.
      '500':
        description: Erreur interne.
    """
    try:
        recette = Recette.query.get_or_404(id)
        if recette.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403

        for etape in recette.etapes:
            db.session.delete(etape)
        db.session.delete(recette)
        db.session.commit()
        return jsonify({"message": "Recette supprimée avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "details": str(e)}), 500


# Modifier une recette
@recettes_bp.route("/recettes/<int:id>", methods=["PUT"])
@jwt_required()
def modifier_recette(id):
    try:
        recette = Recette.query.get_or_404(id)
        if recette.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403

        data = request.get_json()
        if not data or "titre" not in data or not data["titre"]:
            return jsonify({"message": "Le titre est requis"}), 400

        recette.titre = data["titre"].strip()
        recette.description = data.get("description", recette.description)
        recette.publique = data.get("publique", recette.publique)
        recette.temps_preparation = data.get("temps_preparation", recette.temps_preparation)
        recette.temps_cuisson = data.get("temps_cuisson", recette.temps_cuisson)

        # Mise à jour des ingrédients
        if "ingredients" in data:
            existing_ings = {ri.id_ingredient: ri for ri in recette.ingredients}
            for ing in data["ingredients"]:
                if "nom" not in ing or "quantite" not in ing or "unite" not in ing:
                    return jsonify({"message": "Chaque ingrédient doit avoir nom, quantite et unite"}), 400
                if ing["unite"] not in UNITES_VALIDES:
                    return jsonify({"message": f"Unité invalide: {ing['unite']}"}), 400
                ingredient = Ingredient.query.filter_by(nom=ing["nom"].strip()).first() or Ingredient(nom=ing["nom"].strip())
                if not ingredient.id_ingredient:
                    db.session.add(ingredient)
                    db.session.flush()

                if ingredient.id_ingredient in existing_ings:
                    ri = existing_ings[ingredient.id_ingredient]
                    ri.quantite = float(ing["quantite"])
                    ri.unite = ing["unite"]
                    del existing_ings[ingredient.id_ingredient]
                else:
                    db.session.add(RecetteIngredient(
                        id_recette=id,
                        id_ingredient=ingredient.id_ingredient,
                        quantite=float(ing["quantite"]),
                        unite=ing["unite"]
                    ))
            for ri in existing_ings.values():
                db.session.delete(ri)

        # Mise à jour des étapes
        if "etapes" in data:
            existing_etapes = {e.ordre: e for e in recette.etapes}
            for i, etape_data in enumerate(data["etapes"], 1):
                if "instruction" not in etape_data:
                    return jsonify({"message": "Chaque étape doit avoir une instruction"}), 400
                ordre = etape_data.get("ordre", i)
                if ordre in existing_etapes:
                    e = existing_etapes[ordre]
                    e.instruction = etape_data["instruction"]
                    del existing_etapes[ordre]
                else:
                    db.session.add(Etape(
                        id_recette=id,
                        ordre=ordre,
                        instruction=etape_data["instruction"]
                    ))
            for e in existing_etapes.values():
                db.session.delete(e)

        db.session.commit()
        return jsonify({"message": "Recette mise à jour", "recette": recette.to_dict()}), 200
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": f"Valeur invalide: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur mise à jour recette {id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur serveur", "details": str(e)}), 500


# Route : Mettre à jour le statut public
@recettes_bp.route("/recettes/<int:id>/partager", methods=["PUT"])
@jwt_required()
def partager_recette(id):
    """
    Mettre à jour le statut public d'une recette
    ---
    tags:
      - Recettes
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
            publique:
              type: boolean
              example: true
    responses:
      '200':
        description: Statut mis à jour avec succès.
      '400':
        description: Données invalides.
      '401':
        description: Non autorisé.
      '403':
        description: Non autorisé.
      '404':
        description: Recette non trouvée.
      '500':
        description: Erreur interne.
    """
    try:
        recette = Recette.query.get_or_404(id)
        if recette.id_utilisateur != int(get_jwt_identity()):
            return jsonify({"message": "Non autorisé"}), 403
        data = request.get_json()
        if "publique" not in data or not isinstance(data["publique"], bool):
            return jsonify({"message": "Le champ publique doit être un booléen"}), 400
        recette.publique = data["publique"]
        db.session.commit()
        return jsonify({"message": "Statut mis à jour", "recette": recette.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la mise à jour", "details": str(e)}), 500


# Route inchangée : Lister toutes les recettes publiques
@recettes_bp.route("/recettes/public", methods=["GET"])
def lister_recettes_publiques():
    """
    Lister toutes les recettes publiques, en excluant celles de l'utilisateur connecté si authentifié
    ---
    tags:
      - Recettes
    parameters:
      - name: page
        in: query
        type: integer
        description: Numéro de la page (par défaut 1)
      - name: per_page
        in: query
        type: integer
        description: Nombre de recettes par page (par défaut 10)
      - name: titre
        in: query
        type: string
        description: Filtrer par titre
    responses:
      '200':
        description: Liste des recettes publiques récupérée avec succès
      '500':
        description: Erreur interne
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        titre_filter = request.args.get("titre", "")
        query = Recette.query.filter_by(publique=True)

        if titre_filter:
            query = query.filter(Recette.titre.ilike(f"%{titre_filter}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "recettes": [recette.to_dict() for recette in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500


# Route : Lister toutes les recettes publiques de tous les utilisateurs
@recettes_bp.route("/recettes/publiques", methods=["GET"])
@jwt_required()
def lister_recettes_publiques_utilisateur():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        titre_filter = request.args.get("titre", "")
        id_utilisateur = int(get_jwt_identity())

        query = Recette.query.filter_by(id_utilisateur=id_utilisateur, publique=True)
        if titre_filter:
            query = query.filter(Recette.titre.ilike(f"%{titre_filter}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "recettes": [recette.to_dict() for recette in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500


# Route : Enregistrer une recette publique
@recettes_bp.route("/recettes/<int:id>/enregistrer", methods=["POST"])
@jwt_required()
def enregistrer_recette(id):
    """
    Enregistrer une recette publique
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      '201':
        description: Recette enregistrée avec succès.
      '400':
        description: Recette déjà enregistrée ou non publique.
      '401':
        description: Non autorisé.
      '404':
        description: Recette non trouvée.
      '500':
        description: Erreur interne.
    """
    try:
        recette = Recette.query.get_or_404(id)
        if not recette.publique:
            return jsonify({"message": "Cette recette n’est pas publique"}), 403

        id_utilisateur = get_jwt_identity()
        if RecetteUtilisateur.query.filter_by(id_recette=id, id_utilisateur=id_utilisateur).first():
            return jsonify({"message": "Recette déjà enregistrée"}), 400

        enregistrement = RecetteUtilisateur(id_recette=id, id_utilisateur=id_utilisateur)
        db.session.add(enregistrement)
        db.session.commit()
        return jsonify({"message": "Recette enregistrée avec succès"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de l’enregistrement", "details": str(e)}), 500


# Route : Supprimer une recette enregistrée
@recettes_bp.route("/recettes/<int:id>/enregistrer", methods=["DELETE"])
@jwt_required()
def supprimer_enregistrement_recette(id):
    """
    Supprimer une recette enregistrée
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      '200':
        description: Recette supprimée des enregistrées avec succès.
      '401':
        description: Non autorisé.
      '404':
        description: Recette non enregistrée.
      '500':
        description: Erreur interne.
    """
    try:
        id_utilisateur = get_jwt_identity()
        enregistrement = RecetteUtilisateur.query.filter_by(id_recette=id, id_utilisateur=id_utilisateur).first()
        if not enregistrement:
            return jsonify({"message": "Recette non enregistrée par cet utilisateur"}), 404

        db.session.delete(enregistrement)
        db.session.commit()
        return jsonify({"message": "Recette supprimée des enregistrées"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Erreur lors de la suppression", "details": str(e)}), 500


# Route : Lister les recettes enregistrées
@recettes_bp.route("/recettes/enregistrées", methods=["GET"])
@jwt_required()
def lister_recettes_enregistrees():
    """
    Lister les recettes enregistrées
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    responses:
      '200':
        description: Liste des recettes enregistrées récupérée avec succès.
      '401':
        description: Non autorisé.
      '500':
        description: Erreur interne.
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        titre_filter = request.args.get("titre", "")
        id_utilisateur = int(get_jwt_identity())

        query = Recette.query.join(RecetteUtilisateur, Recette.id_recette == RecetteUtilisateur.id_recette) \
            .filter(RecetteUtilisateur.id_utilisateur == id_utilisateur)

        if titre_filter:
            query = query.filter(Recette.titre.ilike(f"%{titre_filter}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "recettes": [recette.to_dict() for recette in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500


@recettes_bp.route("/recettes/verifier-enregistrement/<int:id>", methods=["GET"])
@jwt_required()
def verifier_enregistrement(id):
    """
    Vérifier si une recette est déjà enregistrée par l'utilisateur
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      '200':
        description: Résultat de la vérification.
        schema:
          type: object
          properties:
            isSaved:
              type: boolean
              description: Indique si la recette est déjà enregistrée.
      '401':
        description: Non autorisé.
      '404':
        description: Recette non trouvée.
      '500':
        description: Erreur interne.
    """
    try:
        id_utilisateur = get_jwt_identity()
        recette = Recette.query.get_or_404(id)

        existing_save = RecetteUtilisateur.query.filter_by(
            id_recette=id, id_utilisateur=id_utilisateur
        ).first()

        return jsonify({"isSaved": bool(existing_save)}), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la vérification", "details": str(e)}), 500


@recettes_bp.route("/recettes/suggestions", methods=["GET"])
def obtenir_recettes_suggestions():
    """
    Récupérer un échantillon de recettes publiques pour affichage sous forme de cartes
    ---
    tags:
      - Recettes
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        description: Nombre maximum de recettes à renvoyer (défaut : 4)
    responses:
      '200':
        description: Liste des recettes publiques récupérées avec succès.
        content:
          application/json:
            schema:
              type: object
              properties:
                recettes:
                  type: array
                  items:
                    type: object
                    properties:
                      id_recette:
                        type: integer
                      titre:
                        type: string
                      createur:
                        type: string
                      imageUrl:
                        type: string
                      ingredients:
                        type: array
                        items:
                          type: object
                          properties:
                            id_ingredient:
                              type: integer
                            nom:
                              type: string
                            quantite:
                              type: number
                            unite:
                              type: string
      '500':
        description: Erreur interne du serveur.
    """
    logger.debug("Début de la route /recettes/suggestions")
    try:
        limit = request.args.get("limit", default=4, type=int)
        limit = max(1, min(limit, 10))

        logger.debug("Récupération des recettes publiques")
        recettes_publiques = Recette.query.filter_by(publique=True).all()
        if not recettes_publiques:
            logger.warning("Aucune recette publique disponible")
            return jsonify({"recettes": []}), 200

        suggestions = random.sample(recettes_publiques, min(limit, len(recettes_publiques)))
        logger.debug(f"Nombre de suggestions sélectionnées : {len(suggestions)}")

        # Sérialisation avec 'ingredients' pour correspondre au backend
        suggestions_data = []
        for recette in suggestions:
            try:
                ingredients = [
                    {
                        "id_ingredient": ri.ingredient.id_ingredient,
                        "nom": ri.ingredient.nom,
                        "quantite": ri.quantite,
                        "unite": ri.unite
                    }
                    for ri in getattr(recette, "ingredients", [])
                ]
                suggestions_data.append({
                    "id_recette": recette.id_recette,
                    "titre": recette.titre or "Sans titre",
                    "createur": getattr(recette.createur, "nom", "Inconnu") if recette.createur else "Inconnu",
                    "imageUrl": getattr(recette, "image_url", None),
                    "ingredients": ingredients
                })
            except Exception as e:
                logger.error(f"Erreur lors de la sérialisation de la recette {recette.id_recette} : {str(e)}",
                             exc_info=True)
                continue

        logger.debug(f"Nombre de suggestions sérialisées : {len(suggestions_data)}")
        return jsonify({"recettes": suggestions_data}), 200
    except Exception as e:
        logger.error(f"Erreur inattendue dans /recettes/suggestions : {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500


# Nouvelle route : Lister toutes les recettes disponibles pour les listes de courses
@recettes_bp.route("/recettes/courses", methods=["GET"])
@jwt_required()
def lister_recettes_pour_courses():
    """
    Lister les recettes personnelles et enregistrées de l'utilisateur pour les listes de courses
    ---
    tags:
      - Recettes
    security:
      - bearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        description: Numéro de la page (par défaut 1)
      - name: per_page
        in: query
        type: integer
        description: Nombre de recettes par page (par défaut 10)
    responses:
      '200':
        description: Liste des recettes personnelles et enregistrées
      '401':
        description: Non autorisé
      '500':
        description: Erreur interne
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        id_utilisateur = int(get_jwt_identity())

        # Recettes personnelles
        own_query = Recette.query.filter_by(id_utilisateur=id_utilisateur)
        own_pagination = own_query.paginate(page=page, per_page=per_page, error_out=False)
        own_recettes = [{"type": "personnelle", **recette.to_dict()} for recette in own_pagination.items]

        # Recettes enregistrées
        saved_query = Recette.query.join(RecetteUtilisateur, Recette.id_recette == RecetteUtilisateur.id_recette) \
            .filter(RecetteUtilisateur.id_utilisateur == id_utilisateur)
        saved_pagination = saved_query.paginate(page=page, per_page=per_page, error_out=False)
        saved_recettes = [{"type": "enregistrée", **recette.to_dict()} for recette in saved_pagination.items]

        # Combinaison des deux
        all_recettes = own_recettes + saved_recettes
        total = own_pagination.total + saved_pagination.total

        return jsonify({
            "recettes": all_recettes,
            "total": total,
            "pages": max(own_pagination.pages, saved_pagination.pages),
            "current_page": page
        }), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des recettes pour courses: {str(e)}", exc_info=True)
        return jsonify({"message": "Erreur lors de la récupération", "details": str(e)}), 500