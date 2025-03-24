from app import db

class RecetteUtilisateur(db.Model):
    __tablename__ = "recette_utilisateur"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_recette = db.Column(db.Integer, db.ForeignKey("recettes.id_recette"), nullable=False)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    date_enregistrement = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations
    recette = db.relationship("Recette", back_populates="utilisateurs")
    utilisateur = db.relationship("Utilisateur", back_populates="recettes_enregistrees")

    def to_dict(self):
        return {
            "id": self.id,
            "id_recette": self.id_recette,
            "id_utilisateur": self.id_utilisateur,
            "date_enregistrement": self.date_enregistrement.isoformat() if self.date_enregistrement else None
        }