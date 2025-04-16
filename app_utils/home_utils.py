"""Pomocné funkce pro domovskou stránku."""

from models import SkolniRok

def get_all_skolni_roky():
    """Vrátí seznam všech školních roků, seřazený podle začátku roku."""
    return SkolniRok.query.order_by(SkolniRok.rok_od.asc()).all()

def ensure_skolni_rok_session(session):
    """Zajistí, že session obsahuje vybraný školní rok."""
    if 'vybrany_skolni_rok_od' not in session:
        from models import SkolniRok
        aktualni = SkolniRok.query.filter_by(aktualni=True).first()
        if not aktualni:
            aktualni = SkolniRok.query.order_by(SkolniRok.rok_od.desc()).first()
        if aktualni:
            session['vybrany_skolni_rok_od'] = aktualni.rok_od
            session['vybrany_skolni_rok_do'] = aktualni.rok_do
