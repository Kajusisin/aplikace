from db_config import db
from models.skolni_rok import SkolniRok
from typing import Optional

class Zak(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jmeno = db.Column(db.String(50), nullable=False)
    prijmeni = db.Column(db.String(50), nullable=False)
    cislo_tridy = db.Column(db.Integer, nullable=True)  # výchozí ročník při nástupu
    pismeno_tridy = db.Column(db.String(1), nullable=True)
    pohlavi = db.Column(db.String(10), nullable=False)
    rok_nastupu_2_stupen = db.Column(db.Integer, nullable=False)
    skolni_rok_odchodu_od = db.Column(db.Integer, nullable=True)
    skolni_rok_odchodu_do = db.Column(db.Integer, nullable=True)
    aktualni_skolni_rok_od = db.Column(db.Integer, nullable=True, default=None)
    aktualni_skolni_rok_do = db.Column(db.Integer, nullable=True, default=None)

    def get_trida(self, rok: int) -> Optional[str]:
        """Vrátí třídu žáka na základě školního roku."""
        try:
            if self.cislo_tridy is None or self.rok_nastupu_2_stupen is None:
                return None
            if not isinstance(rok, int):
                rok = int(str(rok).split("/")[0])  # Převod z "2025/2026"
            aktualni_cislo = self.cislo_tridy + (rok - self.rok_nastupu_2_stupen)
            
            # Zachování původní logiky pro ošetření maximální hodnoty
            if aktualni_cislo > 9:
                aktualni_cislo = 9
                
            # Zachování původní logiky pro absolventy
            if self.skolni_rok_odchodu_od is not None and rok >= self.skolni_rok_odchodu_od:
                return f"Absolvent 9.{self.pismeno_tridy} {self.skolni_rok_odchodu_od}" if self.pismeno_tridy else "Absolvent 9."
                
            return f"{aktualni_cislo}.{self.pismeno_tridy}" if self.pismeno_tridy else f"{aktualni_cislo}"
        except Exception as e:
            print(f"❌ Chyba při výpočtu třídy: {e}")
            return None

    def get_skolni_rok_odchodu(self):
        """Vrátí školní rok odchodu žáka, pokud je definován."""
        if self.skolni_rok_odchodu_od:
            return self.skolni_rok_odchodu_od
        return "Neznámý"

    def __repr__(self):
        try:
            aktualni_rok = SkolniRok.query.filter_by(aktualni=True).first()
            trida = self.get_trida(aktualni_rok.rok_od) if aktualni_rok else "Neznámý"
            return f"<Zak {self.prijmeni} {self.jmeno} - {trida}>"
        except Exception:
            return f"<Zak {self.prijmeni} {self.jmeno}>"
