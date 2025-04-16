"""Pomocné funkce pro práci s disciplínami."""

from models import Discipline, ReferenceScore, Performance, Zak
from sqlalchemy import and_, func
from db_config import db

def get_all_disciplines():
    """Vrátí seznam všech disciplín seřazený podle názvu."""
    return Discipline.query.order_by(Discipline.nazev).all()

def get_discipline_by_id(discipline_id):
    """Vrátí disciplínu podle ID."""
    return db.session.get(Discipline, discipline_id)

def get_discipline_name(discipline_id):
    """Vrátí název disciplíny podle ID."""
    discipline = db.session.get(Discipline, discipline_id)
    return discipline.nazev if discipline else None

def get_classes_with_performances(discipline_id, skolni_rok):
    """Vrátí třídy, které mají záznamy v dané disciplíně."""
    # Převod roku na int, pokud je ve formátu "2023/2024"
    rok_int = skolni_rok
    if isinstance(skolni_rok, str) and "/" in skolni_rok:
        rok_int = int(skolni_rok.split("/")[0])
    
    # Získání žáků, kteří mají záznam v dané disciplíně
    student_scores = Performance.query.filter_by(discipline_id=discipline_id, skolni_rok=rok_int).all()
    
    # Získání tříd, do kterých tito žáci patří
    classes = {}
    for ReferenceScore in student_scores:
        zak = db.session.get(Zak, ReferenceScore.zak_id)
        if zak:
            trida = zak.get_trida(rok_int)  # Použití převedené hodnoty rok_int
            if trida and "." in trida and not "Absolvent" in trida and not "Před nástupem" in trida:
                try:
                    cislo, pismeno = trida.split(".")
                    gender = zak.pohlavi
                    if trida not in classes:
                        classes[trida] = {"chlapec": 0, "divka": 0}
                    if gender.lower() == "chlapec":
                        classes[trida]["chlapec"] += 1
                    else:
                        classes[trida]["divka"] += 1
                except ValueError:
                    # Ignorujeme neplatné formáty tříd
                    continue
    
    return classes

def get_students_with_performances(discipline_id, class_name, gender, skolni_rok):
    """Vrátí žáky daného pohlaví z dané třídy a jejich výkony v disciplíně."""
    # Převod roku na int, pokud je ve formátu "2023/2024"
    rok_int = skolni_rok
    if isinstance(skolni_rok, str) and "/" in skolni_rok:
        rok_int = int(skolni_rok.split("/")[0])
    
    # Parsování čísla a písmene třídy
    try:
        cislo, pismeno = class_name.split(".")
        cislo = int(cislo)
    except ValueError:
        return []
    
    # Získání žáků z dané třídy daného pohlaví
    zaci = Zak.query.filter_by(pohlavi=gender).all()
    
    # Filtrování žáků podle třídy pro daný školní rok
    filtered_zaci = []
    for zak in zaci:
        trida = zak.get_trida(rok_int)  # Použití převedené hodnoty rok_int
        if trida and trida == class_name:
            filtered_zaci.append(zak)
    
    # Získání výkonů pro tyto žáky v dané disciplíně
    results = []
    for zak in filtered_zaci:
        performance = Performance.query.filter_by(
            zak_id=zak.id,
            discipline_id=discipline_id,
            rocnik=cislo,
            skolni_rok=rok_int  # Použití převedené hodnoty rok_int
        ).first()
        
        results.append({
            "zak_id": zak.id,
            "jmeno": zak.jmeno,
            "prijmeni": zak.prijmeni,
            "vykon": performance.vykon if performance else None,
            "body": performance.body if performance else None,
            "performance_id": performance.id if performance else None
        })
    
    # Seřazení podle bodů (sestupně), výkonu a příjmení
    results = sorted(results, key=lambda x: (
        -1 * (x["body"] or 0),  # Sestupně podle bodů
        x["prijmeni"],  # Vzestupně podle příjmení
        x["jmeno"]  # Vzestupně podle jména
    ))
    
    return results
