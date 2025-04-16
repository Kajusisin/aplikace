"""Pomocné funkce pro práci s výkony žáků."""

# Opravte tento řádek - zajistěte správný import modelu Discipline
from models import Performance, Zak  # Import ostatních modelů
from db_config import db
from import_bodovaci_databaze import FORMATY_DISCIPLIN, convert_value
from app_utils.grade_utils import vypocet_znamky, vypocet_rozmezi_bodu
from models.disciplines import Discipline, ReferenceScore



def ziskej_body_z_vykonu(discipline_id, vykon):
    """Získá počet bodů podle výkonu na základě typu disciplíny."""
    discipline = Discipline.query.get(discipline_id)
    if not discipline:
        raise ValueError("Disciplína nenalezena")

    format_type = FORMATY_DISCIPLIN.get(discipline.nazev, "float")
    vykon_formatovany = convert_value(vykon, format_type)

    reference_score = ReferenceScore.query.filter_by(
        discipline_id=discipline_id,
        vykon=str(vykon_formatovany)
    ).first()
    if not reference_score:
        raise ValueError(f"Výkon {vykon} nemá přiřazené body.")
    return reference_score.body

def get_student_performances(zak_id, discipline_id=None, rocnik=None, skolni_rok=None):
    """Vrátí výkony žáka pro daný ročník a disciplínu."""
    query = Performance.query.filter_by(zak_id=zak_id)
    
    if rocnik:
        query = query.filter_by(rocnik=rocnik)
    
    if discipline_id:
        query = query.filter_by(discipline_id=discipline_id)
    
    # Přidáme podporu pro filtrování podle školního roku
    if skolni_rok:
        query = query.filter_by(skolni_rok=skolni_rok)
    
    return query.all()

def save_student_performance(zak_id, discipline_id, rocnik, vykon, skolni_rok=None):
    """Uloží nebo aktualizuje výkon žáka."""
    # Ověření existence žáka a disciplíny
    zak = db.session.get(Zak, zak_id)  # Opraveno - chyběl druhý argument, model
    discipline = db.session.get(Discipline, discipline_id)
    
    if not zak or not discipline:
        raise ValueError("Žák nebo disciplína neexistuje")
    
    # Zbytek funkce beze změny...

def save_multiple_performances(performances_data, skolni_rok=None):
    """Hromadně uloží nebo aktualizuje výkony žáků."""
    results = []
    
    for perf in performances_data:
        zak_id = perf.get("zak_id")
        discipline_id = perf.get("discipline_id")
        rocnik = perf.get("rocnik")
        vykon = perf.get("vykon")
        performance_id = perf.get("performance_id")
        
        if not all([zak_id, discipline_id, rocnik]):
            continue
        
        # Pokračujeme pouze pokud byl zadán výkon
        if vykon:
            try:
                # Pokud máme ID výkonu, aktualizujeme přímo existující záznam
                if performance_id:
                    performance = db.session.get(Performance, performance_id)
                    if performance:
                        # Získáme disciplínu a zkontrolujeme, že není None
                        discipline = db.session.get(Discipline, discipline_id)
                        if discipline is None:
                            raise ValueError(f"Disciplína s ID {discipline_id} nebyla nalezena")
                        
                        # Formátování hodnoty výkonu - přidána kontrola None
                        format_type = FORMATY_DISCIPLIN.get(discipline.nazev, "float")
                        vykon_formatted = convert_value(vykon, format_type)
                        
                        # Výpočet bodů
                        body = None
                        # Zde je problém - ReferenceScore je samostatný model, není součástí Discipline
                        # Musíme použít query pro získání ReferenceScore pro danou disciplínu


                        reference_score = ReferenceScore.query.filter_by(  # ✅ OK
                            discipline_id=discipline_id, 
                        vykon=vykon_formatted
                        ).first()

                        if reference_score:
                            body = reference_score.body
                        
                        performance.vykon = vykon_formatted
                        performance.body = body
                        if skolni_rok:
                            performance.skolni_rok = skolni_rok
                        
                        results.append({
                            "zak_id": zak_id,
                            "discipline_id": discipline_id,
                            "body": body,
                            "success": True
                        })
                else:
                    # Jinak použijeme obecnou funkci
                    body = save_student_performance(zak_id, discipline_id, rocnik, vykon, skolni_rok)
                    results.append({
                        "zak_id": zak_id,
                        "discipline_id": discipline_id,
                        "body": body,
                        "success": True
                    })
            except Exception as e:
                results.append({
                    "zak_id": zak_id,
                    "discipline_id": discipline_id,
                    "error": str(e),
                    "success": False
                })
    
    # Commit změn až po zpracování všech výkonů
    db.session.commit()
    
    return results

def get_student_summary(zak_id, rocnik=None, skolni_rok=None):
    """Vrátí souhrnné statistiky žáka pro daný ročník a školní rok."""
    if not zak_id:
        return {
            "total_points": 0,
            "bonus_points": 0,
            "penalty_points": 0,
            "total_with_bonus": 0,
            "average": 0,
            "completed_disciplines": 0,
            "grade": None,
            "bodove_rozmezi": None,
            "warning": "Nebyl zadán žák"
        }

    query = Performance.query.filter_by(zak_id=zak_id)
    if rocnik:
        query = query.filter_by(rocnik=rocnik)
    if skolni_rok:
        query = query.filter_by(skolni_rok=skolni_rok)
    performances = query.all()

    total_points = 0
    total_for_average = 0
    completed_disciplines = 0
    bonus_points = 0
    penalty_points = 0
    warnings = []

    bonus_disciplines = Discipline.query.filter_by(typ='bonus').all()
    penalty_disciplines = Discipline.query.filter_by(typ='penalty').all()

    bonus_categories = [d.nazev for d in bonus_disciplines] if bonus_disciplines else []
    penalty_categories = [d.nazev for d in penalty_disciplines] if penalty_disciplines else []

    if not bonus_categories:
        warnings.append("Bonusové kategorie disciplín nejsou definovány v databázi")
    if not penalty_categories:
        warnings.append("Penalizační kategorie disciplín nejsou definovány v databázi")

    for perf in performances:
        if perf.body is None:
            continue

        discipline = db.session.get(Discipline, perf.discipline_id)
        if discipline:
            if discipline.typ == 'bonus':
                bonus_points += perf.body or 0
            elif discipline.typ == 'penalty':
                penalty_points += perf.body or 0
            else:
                total_points += perf.body or 0
                total_for_average += perf.body or 0
                completed_disciplines += 1

    average = total_for_average / completed_disciplines if completed_disciplines > 0 else 0
    total_with_bonus = (total_points or 0) + (bonus_points or 0) + (penalty_points or 0)

    zak = db.session.get(Zak, zak_id)
    znamka = vypocet_znamky(average, zak.pohlavi, rocnik) if zak and rocnik else None
    bodove_rozmezi = vypocet_rozmezi_bodu(zak.pohlavi, rocnik) if zak and rocnik else None

    result = {
        "total_points": total_points,
        "bonus_points": bonus_points,
        "penalty_points": penalty_points,
        "total_with_bonus": total_with_bonus,
        "average": round(average, 1),
        "completed_disciplines": completed_disciplines,
        "grade": znamka,
        "bodove_rozmezi": bodove_rozmezi
    }

    if warnings:
        result["warnings"] = warnings

    return result

def initialize_discipline_types():
    """Inicializuje typy disciplín v databázi. Spouští se pouze jednou při prvním nastavení."""
    # Nejprve zkontrolujeme, zda sloupec 'typ' již existuje v tabulce
    try:
        # Import pro text()
        from sqlalchemy import text
        
        # Pokus o získání disciplíny s neprázdným typem
        existing_with_type = Discipline.query.filter(Discipline.typ.isnot(None)).first()
        
        # Pokud existuje disciplína s typem, přeskočíme inicializaci
        if existing_with_type:
            print("Typy disciplín jsou již nastaveny.")
            return False
            
        # Kontrola existence sloupce
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('discipline')]
        
        # Přidáme sloupec, pokud neexistuje
        if 'typ' not in columns:
            db.session.execute(text("ALTER TABLE discipline ADD COLUMN typ VARCHAR(20);"))
            print("Sloupec 'typ' byl přidán do tabulky 'discipline'.")
        
        # Oprava SQL dotazů - obalení do text()
        db.session.execute(text("""
        UPDATE discipline SET typ = 'bonus' 
        WHERE nazev IN ('Referát', 'Reprezentace školy', 'Nošení cvičebního úboru', 
                      'Vedení rozcvičky', 'Mimoškolní aktivita (např. screenshot aplikace sledující aktivitu)', 
                      'Aktivní přístup, snaha', 'Zlepšení výkonu od posledního měření', 
                      'Pomoc s organizací', 'Ostatní plusové body');
        """))
        
        db.session.execute(text("""
        UPDATE discipline SET typ = 'penalty' 
        WHERE nazev IN ('Nenošení cvičebního úboru', 'Bezpečnostní riziko (gumička, boty, …)', 
                      'Nekázeň (rušení, neperespektování pokynů, …)', 'Ostatní mínusové body');
        """))
        
        # Nastavení běžných disciplín jako 'regular'
        db.session.execute(text("""
        UPDATE discipline SET typ = 'regular' 
        WHERE typ IS NULL;
        """))
        
        db.session.commit()
        print("Typy disciplín byly úspěšně nastaveny.")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Chyba při inicializaci typů disciplín: {e}")
        return False
