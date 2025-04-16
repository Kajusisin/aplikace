"""Model pro školní rok."""

from db_config import db

class SkolniRok(db.Model):
    __tablename__ = 'skolni_rok'  # Explicitně definován název tabulky
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rok_od = db.Column(db.Integer, nullable=False, unique=True)
    rok_do = db.Column(db.Integer, nullable=False, unique=True)
    aktualni = db.Column(db.Boolean, default=False)

    @staticmethod
    def nastav_aktualni_rok(rok_od):
        """Nastaví daný rok jako aktuální a ostatní deaktivuje."""
        try:
            db.session.query(SkolniRok).update({SkolniRok.aktualni: False})
            rok = SkolniRok.query.filter_by(rok_od=rok_od).first()
            if rok:
                rok.aktualni = True
                db.session.commit()
            else:
                print(f"❌ Chyba: Školní rok {rok_od} nebyl nalezen!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Chyba při aktualizaci školního roku: {e}")

    def __repr__(self):
        return f"<Školní rok {self.rok_od}/{self.rok_do} {'(aktuální)' if self.aktualni else ''}>"
