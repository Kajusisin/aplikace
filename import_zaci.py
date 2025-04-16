import pandas as pd
from flask import Flask
from db_config import db, DATABASE_URI
from models.zak import Zak

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def import_zaci(soubor):
    try:
        with app.app_context():
            with db.session.no_autoflush:
                print(f"🚀 Spouštím import žáků z {soubor}...")
                df = pd.read_excel(soubor)

                # Ověření požadovaných sloupců
                required_columns = [
                    'Jméno', 'Příjmení', 'Pohlaví',
                    'Číslo třídy', 'Písmeno třídy',
                    'Rok nástupu na 2. stupeň',
                    'Školní rok odchodu z 2. stupně od',
                    'Školní rok odchodu z 2. stupně do'
                ]
                missing = [col for col in required_columns if col not in df.columns]
                if missing:
                    print(f"❌ Chybí sloupce: {', '.join(missing)}")
                    return False

                for idx, row in df.iterrows():
                    try:
                        jmeno = str(row.get("Jméno", "")).strip()
                        prijmeni = str(row.get("Příjmení", "")).strip()
                        pohlavi = str(row.get("Pohlaví", "neuvedeno")).strip().lower()
                        try:
                            cislo_tridy = int(str(row.get("Číslo třídy")).strip())
                        except (ValueError, TypeError):
                            cislo_tridy = None
                        if cislo_tridy is None:
                            print(f"⚠️ U žáka {prijmeni} {jmeno} nebylo načteno číslo třídy")
                        pismeno_tridy = str(row.get("Písmeno třídy", "")).strip()
                        if pismeno_tridy.startswith("."):
                            pismeno_tridy = pismeno_tridy[1:]
                        rok_nastupu = int(row["Rok nástupu na 2. stupeň"]) if pd.notna(row.get("Rok nástupu na 2. stupeň")) else None
                        odchod_od = int(row["Školní rok odchodu z 2. stupně od"]) if pd.notna(row.get("Školní rok odchodu z 2. stupně od")) else None
                        odchod_do = int(row["Školní rok odchodu z 2. stupně do"]) if pd.notna(row.get("Školní rok odchodu z 2. stupně do")) else None

                        if not jmeno or not prijmeni:
                            print(f"⚠️ Přeskakuji řádek {idx}: Chybí jméno nebo příjmení")
                            continue

                        existing = Zak.query.filter_by(jmeno=jmeno, prijmeni=prijmeni).first()
                        if existing:
                            existing.pohlavi = pohlavi
                            existing.cislo_tridy = cislo_tridy
                            existing.pismeno_tridy = pismeno_tridy
                            existing.rok_nastupu_2_stupen = rok_nastupu
                            existing.skolni_rok_odchodu_od = odchod_od
                            existing.skolni_rok_odchodu_do = odchod_do
                        else:
                            # Vytvoření nového objektu Zak bez pojmenovaných parametrů
                            novy = Zak()
                            # Nastavení jednotlivých atributů
                            novy.jmeno = jmeno
                            novy.prijmeni = prijmeni
                            novy.pohlavi = pohlavi
                            novy.cislo_tridy = cislo_tridy
                            novy.pismeno_tridy = pismeno_tridy
                            novy.rok_nastupu_2_stupen = rok_nastupu
                            novy.skolni_rok_odchodu_od = odchod_od
                            novy.skolni_rok_odchodu_do = odchod_do
                            db.session.add(novy)

                    except Exception as e:
                        print(f"❌ Chyba na řádku {idx}: {e}")
                        continue

                db.session.commit()
                print("✅ Import žáků dokončen!")
                return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Kritická chyba při importu žáků: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        import_zaci("zaci.xlsx")
