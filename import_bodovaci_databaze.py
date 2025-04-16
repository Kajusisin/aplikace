import pandas as pd
import os
from flask import current_app as app  # ✅ Použití správného kontextu aplikace
from sqlalchemy import text  # ✅ Nutné pro správné spouštění SQL příkazů
from db_config import db
from models import Discipline, ReferenceScore

# 🔹 Formátovací pravidla pro disciplíny - ponecháme je, ale změníme způsob použití
FORMATY_DISCIPLIN = {
    "Shyby na šikmé lavici za 2 min.": "int",
    "Kliky za 2 min.": "int",
    "Švihadlo za 2 min.": "int",
    "Jacík za 2 min.": "int",
    "Člunkový běh": "float",
    "Šplh": "float",
    "Skok z místa": "int",
    "Trojskok z místa": "int",
    "Hod medicinbalem": "float",
    "Hod kriketovým míčkem": "float",
    "Hod oštěpem": "float",
    "Vrh koulí": "float",
    "Skok daleký": "int",
    "Skok vysoký": "int",
    "Běh 60 m": "float",
    "Běh 100 m": "float",
    "Běh 150 m": "float",
    "Běh 300 m": "str",
    "Běh 600 m": "str",
    "Běh 800 m": "str",
    "Běh 1000 m": "str",
    "Běh 1500 m": "str",
    "Referát": "int",
    "Reprezentace školy": "int",
    "Nošení cvičebního úboru": "int",
    "Vedení rozcvičky": "int",
    "Mimoškolní aktivita (např. screenshot aplikace sledující aktivitu)": "int",
    "Aktivní přístup, snaha": "int",
    "Zlepšení výkonu od posledního měření": "int",
    "Pomoc s organizací": "int",
    "Ostatní plusové body": "int",
    "Nenošení cvičebního úboru": "int",
    "Bezpečnostní riziko (gumička, boty, …)": "int",
    "Nekázeň (rušení, neperespektování pokynů, …)": "int",
    "Ostatní mínusové body": "int"
}

def convert_value(value, format_type):
    """
    Jednoduchá příprava hodnoty bez přetypování - čistí a formátuje hodnotu.
    Výstupem je vždy řetězec nebo None.
    """
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
        
    # Základní čištění hodnoty bez převodu na jiný typ
    result = str(value).strip().replace(",", ".")
    
    # Kontrola, zda se jedná o časový formát (obsahuje :)
    if ":" in result:
        parts = result.split(":")
        if len(parts) == 2:  # MM:SS
            try:
                minutes = int(parts[0])
                seconds = int(parts[1])
                result = f"{minutes}:{seconds:02d}"
            except ValueError:
                pass  # Pokud nelze převést, necháme původní hodnotu
        elif len(parts) == 3:  # H:MM:SS
            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                total_min = hours * 60 + minutes
                result = f"{total_min}:{seconds:02d}"
            except ValueError:
                pass  # Pokud nelze převést, necháme původní hodnotu
    
    return result

def import_excel(file_path):
    """Načte bodovací databázi z Excelu a uloží do SQL databáze."""
    try:
        with app.app_context():
            print(f"🚀 Spouštím import bodovací databáze z {file_path}...")

            if not os.path.exists(file_path):
                print(f"❌ Chyba: Soubor {file_path} neexistuje!")
                return False

            # Načtení dat z Excelu - všechny sloupce jako řetězce
            df = pd.read_excel(file_path, dtype=str)  # Načítáme vše jako text
            print(f"✅ Načteno {len(df)} řádků z Excelu.")

            # Smazání starých skóre před importem
            with db.session.begin():
                db.session.execute(text("DELETE FROM reference_scores"))

            # Počítadla pro statistiku
            processed_rows = 0
            skipped_rows = 0
            error_rows = 0

            # Zpracování po řádcích
            for _, row in df.iterrows():
                processed_rows += 1
                
                # Vytvoříme transakci pro každý řádek
                with db.session.begin():
                    try:
                        # Extrakce hodnot z řádku bez přetypování
                        nazev_discipliny = row.iloc[0].strip() if pd.notna(row.iloc[0]) else None
                        body = row.iloc[2].strip() if len(row) > 2 and pd.notna(row.iloc[2]) else None
                        jednotka = row.iloc[3].strip() if len(row) > 3 and pd.notna(row.iloc[3]) else "NEZADÁNO"
                        napoveda = row.iloc[4].strip() if len(row) > 4 and pd.notna(row.iloc[4]) else "NEZADÁNO"

                        # Validace povinných hodnot
                        if not nazev_discipliny or body is None:
                            print(f"⚠️ Přeskakuji řádek {processed_rows}: Chybějící povinná data")
                            skipped_rows += 1
                            continue

                        # Kontrola, zda disciplína existuje v seznamu
                        if nazev_discipliny not in FORMATY_DISCIPLIN:
                            print(f"⚠️ Přeskakuji řádek {processed_rows}: Neznámá disciplína '{nazev_discipliny}'")
                            skipped_rows += 1
                            continue
                            
                        # Získání formátu a konverze výkonu
                        format_type = FORMATY_DISCIPLIN.get(nazev_discipliny, "str")  # ✅ přidat TADY
                        vykon_hodnota = convert_value(row.iloc[1], format_type)       # ✅ použít

                        # Validace výkonu
                        if vykon_hodnota is None:
                            print(f"⚠️ Přeskakuji řádek {processed_rows}: Chybějící nebo neplatná hodnota výkonu")
                            skipped_rows += 1
                            continue

                        # Najdeme nebo vytvoříme disciplínu
                        discipline = Discipline.query.filter_by(nazev=nazev_discipliny).first()
                        if not discipline:
                            discipline = Discipline()
                            discipline.nazev = nazev_discipliny
                            discipline.jednotka = jednotka
                            discipline.napoveda = napoveda
                            db.session.add(discipline)
                            db.session.flush()  # Abychom získali ID

                        # Vytvoříme nový záznam skóre - ukládáme vše jako string
                        new_score = ReferenceScore()
                        new_score.discipline_id = discipline.id
                        new_score.vykon = vykon_hodnota  # Uložíme připravenou hodnotu jako string
                        new_score.body = body  # Uložíme body jako string
                        db.session.add(new_score)

                    except Exception as e:
                        error_rows += 1
                        print(f"❌ Chyba při zpracování řádku {processed_rows}: {str(e)}")
                        # Transakce se automaticky rollbackne díky with db.session.begin()
                        
            # Statistika importu        
            successful_rows = processed_rows - skipped_rows - error_rows
            print(f"📊 Import dokončen: Zpracováno {processed_rows} řádků, Úspěšně {successful_rows}, "
                  f"Přeskočeno {skipped_rows}, Chyb {error_rows}")
                  
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Chyba při importu bodovací databáze: {str(e)}")
        return False

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    
    # 🔹 Připojení k databázi
    from db_config import db, DATABASE_URI
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        import_excel("bodovaci_databaze.xlsx")
