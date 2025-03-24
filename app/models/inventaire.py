from app import db


class Inventaire(db.Model):
    __tablename__ = "inventaires"
    id_inventaire = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(100), nullable=False)
    publique = db.Column(db.Boolean, default=False)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id_utilisateur"), nullable=False)

    # Relations
    ingredients = db.relationship("InventaireIngredient", back_populates="inventaire", cascade="all, delete-orphan")
    proprietaire = db.relationship("Utilisateur", back_populates="inventaires")

    def to_dict(self):
        return {
            "id_inventaire": self.id_inventaire,
            "nom": self.nom,
            "publique": self.publique,
            "id_utilisateur": self.id_utilisateur,
            "ingredients": [ing.to_dict() for ing in self.ingredients]
        }
