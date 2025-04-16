"""Model pro ukládání výkonů studentů v disciplínách."""

from db_config import db

class Performance(db.Model):
    __tablename__ = 'performances'
    id = db.Column(db.Integer, primary_key=True)
    zak_id = db.Column(db.Integer, db.ForeignKey('zak.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    vykon = db.Column(db.String, nullable=False)
    body = db.Column(db.Integer, nullable=False)
    rocnik = db.Column(db.Integer, nullable=False)
    skolni_rok = db.Column(db.Integer, nullable=True)

    zak = db.relationship('Zak', backref=db.backref('performances', lazy=True))
    discipline = db.relationship('Discipline')

    def __repr__(self):
        return f"<Performance zak:{self.zak_id} dis:{self.discipline_id} rocnik:{self.rocnik}>"

