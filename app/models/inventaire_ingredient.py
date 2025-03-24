from app import db


class InventaireIngredient(db.Model):
    __tablename__ = "inventaire_ingredients"
    id_inventaire_ingredient = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_inventaire = db.Column(db.Integer, db.ForeignKey("inventaires.id_inventaire"), nullable=False)
    id_ingredient = db.Column(db.Integer, db.ForeignKey("ingredients.id_ingredient"), nullable=False)
    quantite_disponible = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(20), nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=True)  # Optionnel, pour suivi des coûts

    # Relations
    inventaire = db.relationship("Inventaire", back_populates="ingredients")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id_inventaire_ingredient": self.id_inventaire_ingredient,
            "id_ingredient": self.id_ingredient,
            "nom_ingredient": self.ingredient.nom if self.ingredient else "Inconnu",
            "quantite_disponible": self.quantite_disponible,
            "unite": self.unite,
            "prix_unitaire": self.prix_unitaire
        }
