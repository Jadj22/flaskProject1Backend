from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"
    id_utilisateur = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)

    # Relations
    recettes = db.relationship("Recette", back_populates="createur")
    inventaires = db.relationship("Inventaire", back_populates="proprietaire")
    listes_courses = db.relationship("ListeCourses", back_populates="utilisateur")
    recettes_enregistrees = db.relationship("RecetteUtilisateur", back_populates="utilisateur")

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)

    def to_dict(self):
        return {
            "id_utilisateur": self.id_utilisateur,
            "email": self.email,
            "nom": self.nom
        }
