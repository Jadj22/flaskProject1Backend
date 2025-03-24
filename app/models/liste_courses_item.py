from app import db


class ListeCoursesItem(db.Model):
    __tablename__ = "liste_courses_items"
    id_item = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_liste = db.Column(db.Integer, db.ForeignKey("liste_courses.id_liste"), nullable=False)
    id_ingredient = db.Column(db.Integer, db.ForeignKey("ingredients.id_ingredient"), nullable=False)
    quantite = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(20), nullable=False)

    # Relations
    liste = db.relationship("ListeCourses", back_populates="items")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id_item": self.id_item,
            "id_ingredient": self.id_ingredient,
            "nom_ingredient": self.ingredient.nom if self.ingredient else "Inconnu",
            "quantite": self.quantite,
            "unite": self.unite
        }
