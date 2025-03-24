from app import db
import logging

logger = logging.getLogger(__name__)


class Recette(db.Model):
    __tablename__ = "recettes"
    id_recette = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_creation = db.Column(db.DateTime, default=db.func.current_timestamp())
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    publique = db.Column(db.Boolean, default=False)
    temps_preparation = db.Column(db.Integer, nullable=True)  # En minutes
    temps_cuisson = db.Column(db.Integer, nullable=True)  # En minutes

    # Relations
    ingredients = db.relationship("RecetteIngredient", back_populates="recette", cascade="all, delete-orphan")
    etapes = db.relationship("Etape", back_populates="recette", order_by="Etape.ordre", cascade="all, delete-orphan")
    utilisateurs = db.relationship("RecetteUtilisateur", back_populates="recette")
    listes_courses = db.relationship("ListeCourses", back_populates="recette")
    createur = db.relationship("Utilisateur", back_populates="recettes")

    def to_dict(self):
        try:
            return {
                "id_recette": self.id_recette,
                "titre": self.titre,
                "description": self.description,
                "date_creation": self.date_creation.isoformat() if self.date_creation else None,
                "id_utilisateur": self.id_utilisateur,
                "publique": self.publique,
                "temps_preparation": self.temps_preparation,
                "temps_cuisson": self.temps_cuisson,
                "ingredients": [ri.to_dict() for ri in self.ingredients],
                "etapes": [{"id_etape": e.id_etape, "ordre": e.ordre, "instruction": e.instruction} for e in
                           self.etapes],
                "createur": self.createur.nom if self.createur else "Inconnu"
            }
        except Exception as e:
            logger.error(f"Erreur dans Recette.to_dict() pour id {self.id_recette}: {str(e)}", exc_info=True)
            return {"id_recette": self.id_recette, "titre": self.titre, "error": "Erreur lors de la sérialisation"}
