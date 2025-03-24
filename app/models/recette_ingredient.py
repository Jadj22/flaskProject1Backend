from app import db
import logging

logger = logging.getLogger(__name__)


class RecetteIngredient(db.Model):
    __tablename__ = "recette_ingredients"
    id_recette_ingredient = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_recette = db.Column(db.Integer, db.ForeignKey("recettes.id_recette"), nullable=False)
    id_ingredient = db.Column(db.Integer, db.ForeignKey("ingredients.id_ingredient"), nullable=False)
    quantite = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(20), nullable=False)

    # Relations
    recette = db.relationship("Recette", back_populates="ingredients")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        try:
            return {
                "id_recette_ingredient": self.id_recette_ingredient,
                "id_ingredient": self.id_ingredient,
                "nom": self.ingredient.nom if self.ingredient else "Inconnu",
                "quantite": self.quantite,
                "unite": self.unite,
                "prix_unitaire": self.ingredient.prix_unitaire if self.ingredient else None
            }
        except Exception as e:
            logger.error(f"Erreur dans RecetteIngredient.to_dict() pour id {self.id_recette_ingredient}: {str(e)}",
                         exc_info=True)
            return {"id_ingredient": self.id_ingredient, "nom": "Inconnu", "quantite": self.quantite,
                    "unite": self.unite}
