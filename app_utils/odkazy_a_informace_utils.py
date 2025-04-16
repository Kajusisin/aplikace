"""Pomocné funkce pro práci s odkazy a informacemi."""

import os
from models import Odkaz, Informace, Soubor
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app
from db_config import db

def get_all_odkazy():
    """Vrátí seznam všech odkazů seřazený podle kategorie a názvu."""
    return Odkaz.query.order_by(Odkaz.kategorie, Odkaz.nazev).all()

def group_odkazy_by_category(odkazy):
    """Seskupí odkazy podle kategorií."""
    odkazy_podle_kategorii = {}
    for odkaz in odkazy:
        kategorie = odkaz.kategorie
        if kategorie not in odkazy_podle_kategorii:
            odkazy_podle_kategorii[kategorie] = []
        odkazy_podle_kategorii[kategorie].append(odkaz)
    return odkazy_podle_kategorii

def get_all_informace():
    """Vrátí seznam všech informací seřazený podle data (nejnovější první)."""
    return Informace.query.order_by(Informace.datum.desc()).all()

def get_all_soubory():
    """Vrátí seznam všech souborů seřazený podle data nahrání (nejnovější první)."""
    return Soubor.query.order_by(Soubor.datum_nahrani.desc()).all()

def create_odkaz(nazev, url, kategorie):
    """Vytvoří nový odkaz."""
    # Varianta 1: Pokud konstruktor neakceptuje nazvané parametry
    new_odkaz = Odkaz()
    new_odkaz.nazev = nazev
    new_odkaz.url = url
    new_odkaz.kategorie = kategorie
    db.session.add(new_odkaz)
    return new_odkaz

def create_informace(nadpis, text, datum=None):
    """Vytvoří novou informaci."""
    if datum is None:
        datum = datetime.now().strftime('%d.%m.%Y')  # Formát podle modelu
    
    new_info = Informace()
    # V modelu není nadpis, pouze text - použijeme text jako obsah
    new_info.text = text  # nebo případně: f"{nadpis}\n\n{text}" 
    new_info.datum = datum
    db.session.add(new_info)
    return new_info

def create_soubor(file, filename, popis):
    """Vytvoří nový záznam souboru a uloží soubor do systému."""
    # Získání cesty pro uložení souboru
    app = current_app
    secure_name = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
    
    # Uložení souboru
    file.save(os.path.join(app.root_path, file_path))
    
    # Zjištění velikosti souboru
    file_size = os.path.getsize(os.path.join(app.root_path, file_path))
    
    # Zjištění typu souboru
    file_extension = os.path.splitext(filename)[1][1:].lower()
    
    # Vytvoření záznamu v databázi podle skutečného modelu
    new_file = Soubor()
    new_file.nazev = filename  # Název souboru pro zobrazení
    new_file.filename = secure_name  # Skutečné jméno souboru na disku
    new_file.velikost = file_size
    new_file.typ_souboru = file_extension
    new_file.datum_nahrani = datetime.now()
    db.session.add(new_file)
    return new_file

def delete_odkaz(odkaz_id):
    """Smaže odkaz z databáze."""
    odkaz = db.session.get(Odkaz, odkaz_id)
    if odkaz:
        db.session.delete(odkaz)
        db.session.commit()
        return True
    return False

def delete_informace(informace_id):
    """Smaže informaci z databáze."""
    informace = db.session.get(Informace, informace_id)
    if informace:
        db.session.delete(informace)
        db.session.commit()
        return True
    return False

def delete_soubor(soubor_id):
    """Smaže soubor z databáze a z disku."""
    app = current_app
    soubor = db.session.get(Soubor, soubor_id)
    if soubor:
        # Pokus o smazání fyzického souboru
        try:
            # Použijeme atribut filename místo cesta
            file_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], soubor.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Varování: Nepodařilo se smazat soubor {soubor.filename}: {e}")
        
        # Smazání záznamu z databáze
        db.session.delete(soubor)
        db.session.commit()
        return True
    return False

def vytvorit_vychozi_odkazy():
    """Vytvoří výchozí odkazy pro prázdnou databázi."""
    vychozi_odkazy = [
        {"nazev": "Web školy", "url": "https://www.example.cz", "kategorie": "Škola"},
        {"nazev": "Bakaláři", "url": "https://www.bakalari.cz", "kategorie": "Škola"},
        {"nazev": "Ministerstvo školství", "url": "https://www.msmt.cz", "kategorie": "Oficiální zdroje"}
    ]
    
    for odkaz_data in vychozi_odkazy:
        existing = Odkaz.query.filter_by(nazev=odkaz_data["nazev"]).first()
        if not existing:
            new_odkaz = Odkaz(**odkaz_data)
            db.session.add(new_odkaz)
    
    db.session.commit()
