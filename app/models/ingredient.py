from app import db


class Ingredient(db.Model):
    __tablename__ = "ingredients"
    id_ingredient = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    unite = db.Column(db.String(20), nullable=True)  # Ex. "g", "L", "unités"
    prix_unitaire = db.Column(db.Float, nullable=True)  # Prix en euros

    def to_dict(self):
        return {
            "id_ingredient": self.id_ingredient,
            "nom": self.nom,
            "unite": self.unite,
            "prix_unitaire": self.prix_unitaire
        }
