from app import db


class Etape(db.Model):
    __tablename__ = "etapes"
    id_etape = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_recette = db.Column(db.Integer, db.ForeignKey("recettes.id_recette"), nullable=False)
    ordre = db.Column(db.Integer, nullable=False)
    instruction = db.Column(db.Text, nullable=False)

    # Relations
    recette = db.relationship("Recette", back_populates="etapes")

    def to_dict(self):
        return {
            "id_etape": self.id_etape,
            "ordre": self.ordre,
            "instruction": self.instruction
        }
