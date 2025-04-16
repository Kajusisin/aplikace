import pandas as pd
from flask import Flask
from db_config import db, DATABASE_URI
from models import SkolniRok

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def import_skolni_roky(file_path):
    """Importuje školní roky z Excelu do databáze."""
    with app.app_context():
        try:
            data = pd.read_excel(file_path, dtype=str)
            required_columns = ['Školní rok od', 'Školní rok do']

            if not all(col in data.columns for col in required_columns):
                print("❌ Chybí požadované sloupce v Excelu!")
                return
            
            for _, row in data.iterrows():
                rok_od = int(row['Školní rok od'])
                rok_do = int(row['Školní rok do'])

                existing_rok = SkolniRok.query.filter_by(rok_od=rok_od, rok_do=rok_do).first()
                if not existing_rok:
                    # OPRAVA - správná inicializace objektu bez pojmenovaných parametrů
                    new_rok = SkolniRok()
                    new_rok.rok_od = rok_od
                    new_rok.rok_do = rok_do
                    db.session.add(new_rok)

            db.session.commit()
            print("✅ Import školních roků dokončen!")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Chyba při importu školních roků: {e}")

def set_default_skolni_rok(rok_od=2025, rok_do=2026):
    """Nastaví výchozí školní rok jako aktuální."""
    with app.app_context():
        try:
            SkolniRok.query.update({SkolniRok.aktualni: False})  # Reset všech aktuálních roků
            skolni_rok = SkolniRok.query.filter_by(rok_od=rok_od, rok_do=rok_do).first()
            if skolni_rok:
                skolni_rok.aktualni = True
                db.session.commit()
                print(f"✅ Výchozí školní rok {rok_od}/{rok_do} nastaven jako aktuální.")
            else:
                print(f"❌ Školní rok {rok_od}/{rok_do} neexistuje v databázi.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Chyba při nastavování výchozího školního roku: {e}")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        import_skolni_roky("skolni_roky.xlsx")
        # Nastavení výchozího školního roku po importu
        set_default_skolni_rok()
