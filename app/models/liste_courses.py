from app import db


class ListeCourses(db.Model):
    __tablename__ = "liste_courses"
    id_liste = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(100), nullable=False)
    date_creation = db.Column(db.DateTime, default=db.func.current_timestamp())
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    id_recette = db.Column(db.Integer, db.ForeignKey("recettes.id_recette"), nullable=True)
    id_inventaire = db.Column(db.Integer, db.ForeignKey("inventaires.id_inventaire"), nullable=True)  # Nouveau

    # Relations
    items = db.relationship("ListeCoursesItem", back_populates="liste", cascade="all, delete-orphan")
    recette = db.relationship("Recette", back_populates="listes_courses")
    inventaire = db.relationship("Inventaire")
    utilisateur = db.relationship("Utilisateur", back_populates="listes_courses")

    def to_dict(self):
        return {
            "id_liste": self.id_liste,
            "nom": self.nom,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "id_utilisateur": self.id_utilisateur,
            "id_recette": self.id_recette,
            "id_inventaire": self.id_inventaire,
            "items": [item.to_dict() for item in self.items]
        }
