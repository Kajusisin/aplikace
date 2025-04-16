from db_config import db

class Discipline(db.Model):
    __tablename__ = 'discipline'
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(100), nullable=False)
    jednotka = db.Column(db.String(50))
    napoveda = db.Column(db.String(255))
    typ = db.Column(db.String(20))  # Nový sloupec pro typ disciplíny: 'regular', 'bonus', 'penalty'

    def __repr__(self):
        return f"<Disciplína {self.nazev}>"

"""Model pro ukládání výkonů studentů v disciplínách."""

from db_config import db

class ReferenceScore(db.Model):
    __tablename__ = 'reference_scores'
    id = db.Column(db.Integer, primary_key=True)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    vykon = db.Column(db.String(50), nullable=False)
    body = db.Column(db.Integer, nullable=False)

    discipline = db.relationship("Discipline", backref="reference_scores")

    def __repr__(self):
        discipline_name = self.discipline.nazev if self.discipline else "Neznámá"
        return f"<Výkon {self.vykon} ({self.body} bodů) - {discipline_name}>"
    



