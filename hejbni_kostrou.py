import os
import pandas as pd
import re
import logging
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from db_config import db, DATABASE_URI
# Importujeme z models a app_utils
from models.zak import Zak
from models.disciplines import Discipline, ReferenceScore
from models.performance import Performance
from models.skolni_rok import SkolniRok
from models.odkazy_info import Odkaz, Informace, Soubor
from app_utils import (
    vypocet_rozmezi_bodu, vypocet_znamky, allowed_file,
    get_all_zaci, vyhledat_zaky, get_zak_by_id,
    get_aktivni_tridy, get_absolventi_tridy,
    ziskej_body_z_vykonu, get_student_performances, 
    save_student_performance, save_multiple_performances,
    get_student_summary, initialize_discipline_types,
    get_all_odkazy, group_odkazy_by_category, get_all_informace, 
    get_all_soubory, create_odkaz, create_informace, 
    create_soubor, delete_odkaz, delete_informace, delete_soubor,
    vytvorit_vychozi_odkazy,
    get_all_skolni_roky, ensure_skolni_rok_session,
    get_all_disciplines, get_discipline_by_id, 
    get_discipline_name, get_classes_with_performances,
    get_students_with_performances
)
from import_zaci import import_zaci
from import_skolni_roky import import_skolni_roky
from import_bodovaci_databaze import import_excel, FORMATY_DISCIPLIN, convert_value
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, and_, or_
from logging.handlers import RotatingFileHandler
from typing import Any, Optional, Union, Tuple, Literal
from flask import Response

# ✅ Načtení bezpečných proměnných
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'pptx', 'txt', 'csv', 'zip', 'rar', 'mp4', 'mp3'}
app.secret_key = os.getenv("SECRET_KEY", "hejbni_kostrou_secret_key")

# Přidejte toto po inicializaci aplikace (před app.config['UPLOAD_FOLDER'])
app.config['SESSION_TYPE'] = 'filesystem'

# Vytvoření adresáře pro uploady, pokud neexistuje
uploads_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
    print(f"✅ Vytvořena složka pro nahrávání souborů: {uploads_dir}")

# Inicializace databáze a migrací
db.init_app(app)
migrate = Migrate(app, db)

# V setup_logger funkci nastavit UTF-8 kódování
def setup_logger():
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'app.log')
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5, encoding='utf-8')
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('Aplikace spuštěna')

# Zavolat tuto funkci po vytvoření aplikace
setup_logger()

@app.before_request
def nastav_globalni_skolni_rok():
    """Připraví objekt i string reprezentaci školního roku pro globální použití."""
    g.vybrany_rok = None

    if 'vybrany_skolni_rok_od' in session and 'vybrany_skolni_rok_do' in session:
        # String reprezentace pro šablony (např. v base.html)
        session['vybrany_skolni_rok'] = f"{session['vybrany_skolni_rok_od']}/{session['vybrany_skolni_rok_do']}"
        
        # Objekt reprezentace – využitelný v každé route jako g.vybrany_rok
        g.vybrany_rok = SkolniRok.query.filter_by(rok_od=session['vybrany_skolni_rok_od']).first()

@app.route("/")
def home():
    """Domovská stránka aplikace."""
    skolni_roky = get_all_skolni_roky()  # Použití utility funkce
    app.logger.info(f"Načteno {len(skolni_roky)} školních roků")
    
    if not skolni_roky:
        flash("Databáze školních roků je prázdná! Importujte školní roky.", "warning")
        return render_template("home.html", skolni_roky=[])
    
    # Nastavení aktuálního školního roku do session, pokud není
    if 'vybrany_skolni_rok_od' not in session:
        aktualni_rok = next((r for r in skolni_roky if r.aktualni), skolni_roky[-1])
        session['vybrany_skolni_rok_od'] = aktualni_rok.rok_od
        session['vybrany_skolni_rok_do'] = aktualni_rok.rok_do
    
    return render_template("home.html", skolni_roky=skolni_roky)

@app.route('/tridy')
def zobraz_tridy():
    """Zobrazení seznamu všech tříd."""
    try:
        # Získání aktuálního školního roku ze session
        vybrany_rok = session.get('vybrany_skolni_rok_od')
        
        # Pokud není v session, použijeme aktuální rok
        if not vybrany_rok:
            aktualni_rok = SkolniRok.query.filter_by(aktualni=True).first()
            if aktualni_rok:
                vybrany_rok = aktualni_rok.rok_od
            else:
                # Pokud není ani jeden rok nastaven jako aktuální
                aktualni_rok = SkolniRok.query.order_by(SkolniRok.rok_od.desc()).first()
                if aktualni_rok:
                    vybrany_rok = aktualni_rok.rok_od
                else:
                    flash("Nejsou definovány žádné školní roky.", "warning")
                    return redirect(url_for("home"))
        
        # Získání seznamu tříd
        tridni_seznam = get_aktivni_tridy(vybrany_rok)
        absolventi_tridy = get_absolventi_tridy(vybrany_rok)
        
        return render_template('trida.html', 
                             tridni_seznam=tridni_seznam,
                             absolventi_tridy=absolventi_tridy,
                             vybrany_rok=vybrany_rok)
    except Exception as e:
        app.logger.error(f"Chyba při zobrazení seznamu tříd: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/zobraz_tridy")
def zobraz_tridy_alt():
    """Alternativní cesta pro zobrazení tříd."""
    return redirect(url_for("zobraz_tridy"))

@app.route("/detail_tridy/<int:cislo>/<string:pismeno>")
@app.route("/detail_tridy/<int:cislo>/<string:pismeno>/<int:rok>")
@app.route("/detail_tridy/<int:cislo>/<string:pismeno>/<int:rok>/<int:absolvent_rok>")
def detail_tridy(cislo, pismeno, rok=None, absolvent_rok=None):
    """Zobrazí detail třídy."""
    try:
        # Kontrola, zda je vybrán školní rok
        if 'vybrany_skolni_rok_od' not in session:
            flash("Nejprve vyberte školní rok", "warning")
            return redirect(url_for('home'))
        
        vybrany_rok = rok or session.get('vybrany_skolni_rok_od')
        
        # Název třídy
        trida_nazev = f"{cislo}.{pismeno}"
        if absolvent_rok:
            trida_nazev = f"{trida_nazev} (absolventi {absolvent_rok})"
        
        # Získání žáků v dané třídě
        vsichni_zaci = get_all_zaci()  # Použití utility funkce místo přímého dotazu
        chlapci = []
        divky = []
        
        for zak in vsichni_zaci:
            trida = zak.get_trida(vybrany_rok)
            
            # Pro absolventy kontrolujeme rok odchodu
            if absolvent_rok:
                if zak.skolni_rok_odchodu_od == absolvent_rok and f"{zak.cislo_tridy}.{zak.pismeno_tridy}" == f"{cislo}.{pismeno}":
                    if zak.pohlavi.lower() == "chlapec":
                        chlapci.append(zak)
                    else:
                        divky.append(zak)
            # Pro běžné třídy
            elif trida == trida_nazev:
                if zak.pohlavi.lower() == "chlapec":
                    chlapci.append(zak)
                else:
                    divky.append(zak)
        
        # Seřazení podle příjmení
        chlapci.sort(key=lambda x: x.prijmeni)
        divky.sort(key=lambda x: x.prijmeni)
        
        return render_template(
            'detail_tridy.html',
            trida_nazev=trida_nazev,
            chlapci=chlapci,
            divky=divky,
            vybrany_rok=vybrany_rok
        )
    except Exception as e:
        app.logger.error(f"Chyba při zobrazení detailu třídy: {e}")
        flash(f"Při načítání detailu třídy došlo k chybě: {e}", "error")
        return redirect(url_for('home'))

@app.route('/detail_tridy_alt/<int:cislo>/<string:pismeno>/<int:rok>', methods=['GET'])
def detail_tridy_alt(cislo, pismeno, rok=None):
    try:
        return redirect(url_for("detail_tridy", cislo=cislo, pismeno=pismeno, rok=rok))
    except Exception as e:
        app.logger.error(f"Chyba při přesměrování: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("zobraz_tridy"))

@app.route("/detail_tridy")
def seznam_trid():
    """Tento endpoint pouze přesměruje na správnou stránku tříd."""
    return redirect(url_for("zobraz_tridy"))

@app.route("/nastav_aktivni_rok", methods=["POST"])
def nastav_aktivni_rok():
    """Nastaví zvolený školní rok jako aktivní bez posunu žáků."""
    try:
        data = request.get_json()
        rok_id = data.get("rok_id")
        
        if not rok_id:
            return jsonify({"success": False, "error": "Nebyl zadán žádný rok!"}), 400
            
        # Najít vybraný rok
        skolni_rok = SkolniRok.query.get(rok_id)
        if not skolni_rok:
            return jsonify({"success": False, "error": "Vybraný školní rok neexistuje!"}), 404
            
        # Nastavení nové hodnoty aktuální roku v databázi
        SkolniRok.nastav_aktualni_rok(skolni_rok.rok_od)
        
        # Aktualizace session
        session['vybrany_skolni_rok_od'] = skolni_rok.rok_od
        session['vybrany_skolni_rok_do'] = skolni_rok.rok_do
        
        app.logger.info(f"✅ Školní rok změněn na {skolni_rok.rok_od}/{skolni_rok.rok_do}!")
        return jsonify({
            "success": True, 
            "message": f"Školní rok změněn na {skolni_rok.rok_od}/{skolni_rok.rok_do}!"
        })
            
    except Exception as e:
        app.logger.error(f"❌ Chyba při změně školního roku: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def posunout_zaky_podle_skolniho_roku(rok_od):
    """Posune žáky do správného ročníku podle vybraného školního roku."""
    try:
        vsichni_zaci = get_all_zaci()  # Použití utility funkce místo přímého dotazu
        for zak in vsichni_zaci:
            if zak.rok_nastupu_2_stupen and zak.cislo_tridy:
                # Výpočet nového ročníku
                novy_rocnik = zak.cislo_tridy + (rok_od - zak.rok_nastupu_2_stupen)
                if novy_rocnik > 9:
                    novy_rocnik = 9  # Maximální ročník je 9
                zak.cislo_tridy = novy_rocnik
        db.session.commit()
    except Exception as e:
        app.logger.error(f"❌ Chyba při posunu žáků: {e}")

def aktualizovat_tridy(skolni_rok):
    """Aktualizuje třídy žáků na základě školního roku."""
    try:
        zaci = get_all_zaci()  # Použití utility funkce místo přímého dotazu
        for zak in zaci:
            if zak.cislo_tridy and zak.cislo_tridy < 9:
                zak.cislo_tridy += 1
            elif zak.cislo_tridy == 9:
                zak.cislo_tridy = None  # Přesun do absolventů
                zak.pismeno_tridy = f"Absolvent {zak.pismeno_tridy}"
                zak.skolni_rok_odchodu_od = skolni_rok.split("/")[0]
                zak.skolni_rok_odchodu_do = skolni_rok.split("/")[1]
        db.session.commit()
    except Exception as e:
        app.logger.error(f"❌ Chyba při aktualizaci tříd: {e}")

@app.context_processor
def inject_skolni_rok():
    """Vloží vybraný školní rok do kontextu šablon."""
    skolni_rok = None
    
    if 'vybrany_skolni_rok_od' in session and 'vybrany_skolni_rok_do' in session:
        skolni_rok = f"{session['vybrany_skolni_rok_od']}/{session['vybrany_skolni_rok_do']}"
    
    return {
        'vybrany_skolni_rok': skolni_rok,
        'vybrany_skolni_rok_od': session.get('vybrany_skolni_rok_od'),
        'vybrany_rok': session.get('vybrany_skolni_rok_od')
    }

@app.route("/zaci")
def zobraz_zaky():
    """Zobrazení seznamu všech žáků."""
    try:
        # Získání všech žáků
        zaky = get_all_zaci()
        
        # Kontrola, zda funkce vrátila platná data
        if zaky is None:
            zaky = []  # Prevence chyby při iteraci, pokud je výsledek None
            flash("Nepodařilo se načíst seznam žáků.", "warning")
        
        # Získání vybraného školního roku z session
        vybrany_skolni_rok = session.get('vybrany_skolni_rok_od')
        
        if not vybrany_skolni_rok:
            aktualni_rok = SkolniRok.query.filter_by(aktualni=True).first()
            if aktualni_rok:
                vybrany_skolni_rok = aktualni_rok.rok_od
                session['vybrany_skolni_rok_od'] = aktualni_rok.rok_od
                session['vybrany_skolni_rok_do'] = aktualni_rok.rok_do
            else:
                flash("Není nastaven aktuální školní rok!", "warning")
                return redirect(url_for("home"))
        
        return render_template("zaci.html", zaky=zaky, vybrany_skolni_rok=vybrany_skolni_rok)
    except Exception as e:
        app.logger.error(f"Chyba při zobrazení seznamu žáků: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/discipliny")
def discipliny():
    """Zobrazení seznamu všech disciplín s možností procházení tříd."""
    try:
        discipliny_list = get_all_disciplines()
        vybrany_skolni_rok = request.args.get("skolni_rok", "")
        
        if not vybrany_skolni_rok:
            aktualni_rok = SkolniRok.query.filter_by(aktualni=True).first()
            if aktualni_rok:
                vybrany_skolni_rok = f"{aktualni_rok.rok_od}/{aktualni_rok.rok_do}"
        
        return render_template(
            "discipliny.html", 
            discipliny=discipliny_list, 
            vybrany_skolni_rok=vybrany_skolni_rok
        )
        
    except Exception as e:
        app.logger.error(f"Chyba při zobrazení disciplín: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/get_classes_for_discipline")
def get_classes_for_discipline():
    """API koncový bod pro získání tříd s žáky, kteří mají záznamy v dané disciplíně."""
    discipline_id = request.args.get("discipline_id", type=int)
    skolni_rok = request.args.get("skolni_rok", "")
    
    if not discipline_id:
        return jsonify({"error": "Chybí ID disciplíny"}), 400
    
    try:
        # Použití již importované funkce
        classes = get_classes_with_performances(discipline_id, skolni_rok)
        return jsonify(classes)
    
    except Exception as e:
        app.logger.error(f"Chyba při získávání tříd pro disciplínu: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_discipline_name")
def get_discipline_name_route():
    """API koncový bod pro získání názvu disciplíny podle ID."""
    discipline_id = request.args.get("discipline_id", type=int)
    
    if not discipline_id:
        return jsonify({"error": "Chybí ID disciplíny"}), 400
    
    try:
        # Použití utility funkce - upraveno volání podle skutečných parametrů
        name = get_discipline_name(discipline_id)  # Opraveno - použití bez named parametru
        if name:
            return jsonify({"name": name})
        return jsonify({"error": "Disciplína nenalezena"}), 404
    except Exception as e:
        app.logger.error(f"Chyba při získávání názvu disciplíny: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_students_performances")
def get_students_performances():
    """API koncový bod pro získání žáků a jejich výkonů pro danou třídu, pohlaví a disciplínu."""
    discipline_id = request.args.get("discipline_id", type=int)
    class_name = request.args.get("class", "")
    gender = request.args.get("gender", "")
    skolni_rok = request.args.get("skolni_rok", "")
    
    if not discipline_id or not class_name or not gender or not skolni_rok:
        return jsonify({"error": "Chybí povinné parametry"}), 400
    
    try:
        # Použití již importované funkce
        students_data = get_students_with_performances(discipline_id, class_name, gender, skolni_rok)
        return jsonify(students_data)
    
    except Exception as e:
        app.logger.error(f"Chyba při získávání výkonů žáků: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/ulozit_vykony_hromadne", methods=["POST"])
def ulozit_vykony_hromadne():
    """API koncový bod pro hromadné uložení výkonů žáků."""
    data = request.get_json()
    
    if not data or "performances" not in data:
        return jsonify({"error": "Chybí povinná data"}), 400
    
    performances = data["performances"]
    
    try:
        # Extrakce školního roku z dat
        skolni_rok = data.get("skolni_rok", None)
        if isinstance(skolni_rok, str) and "/" in skolni_rok:
            skolni_rok = int(skolni_rok.split("/")[0])
        
        # Použití utility funkce
        results = save_multiple_performances(performances, skolni_rok)
        
        return jsonify({
            "success": True,
            "count": len(results),
            "message": f"✅ {len(results)} výkonů bylo úspěšně uloženo!"
        })
    except Exception as e:
        app.logger.error(f"Chyba při ukládání výkonů: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_student_performance")
def get_student_performance():
    """API koncový bod pro získání výkonu žáka."""
    try:
        zak_id = request.args.get("zak_id", type=int)
        discipline_id = request.args.get("discipline_id", type=int)
        rocnik = request.args.get("rocnik", type=int)
        skolni_rok = request.args.get("skolni_rok", type=int)
        
        if not all([zak_id, discipline_id, rocnik]):
            return jsonify({"error": "Chybí povinné parametry"}), 400
            
        # Získání existujícího záznamu
        reference_score = Performance.query.filter_by(
            zak_id=zak_id, 
            discipline_id=discipline_id, 
            rocnik=rocnik,
            skolni_rok=skolni_rok
        ).first()
        
        if reference_score:
            return jsonify({
                "id": reference_score.id,
                "vykon": reference_score.vykon,
                "body": reference_score.body
            })
        else:
            return jsonify({"message": "Žádný výkon nenalezen"})
            
    except Exception as e:
        app.logger.error(f"Chyba při získávání výkonu žáka: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/ulozit_vykon", methods=["POST"])
def ulozit_vykon():
    """API koncový bod pro uložení výkonu jednoho žáka."""
    try:
        data = request.get_json()
        app.logger.info(f"🔍 DEBUG: Přijata data pro uložení výkonu: {data}")
        
        if not data:
            return jsonify({"error": "Žádná data nebyla poskytnuta"}), 400
        
        zak_id = data.get("zak_id")
        discipline_id = data.get("discipline_id")
        rocnik = data.get("rocnik")
        vykon = data.get("vykon")
        skolni_rok = data.get("skolni_rok")
        
        if not zak_id or not discipline_id or not rocnik:
            return jsonify({"error": "Chybí povinné parametry"}), 400

        body = ziskej_body_z_vykonu(discipline_id, vykon)
        save_student_performance(zak_id, discipline_id, rocnik, vykon, skolni_rok)

        return jsonify({
            "message": "Výkon úspěšně uložen",
            "body": body
        })
    except ValueError as e:
        app.logger.error(f"Chybný formát výkonu: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Chyba při ukládání výkonu: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/ziskat_tridu")
def ziskat_tridu():
    """API koncový bod pro získání třídy žáka."""
    try:
        zak_id = request.args.get("zak_id", type=int)
        rok = request.args.get("rok", type=int)
        
        if not zak_id:
            return jsonify({"error": "Chybí ID žáka"}), 400
            
        zak = get_zak_by_id(zak_id)
        if not rok:
            aktualni_rok = SkolniRok.query.filter_by(aktualni=True).first()
            rok = aktualni_rok.rok_od if aktualni_rok else None
        
        trida = zak.get_trida(rok) if rok else None
        return jsonify({"trida": trida})
    except Exception as e:
        app.logger.error(f"Chyba při získávání třídy žáka: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/vyhledat")
def vyhledat_zaka():
    """API koncový bod pro vyhledávání žáků."""
    try:
        query = request.args.get("q", "")
        if not query or len(query) < 2:
            return jsonify([])
            
        zaci = vyhledat_zaky(query)
        
        # Formátování výsledků pro frontend
        results = []
        for zak in zaci:
            # Získání aktuální třídy
            aktualni_rok = SkolniRok.query.filter_by(aktualni=True).first()
            trida = zak.get_trida(aktualni_rok.rok_od) if aktualni_rok else "Neznámá třída"
            
            results.append({
                "id": zak.id,
                "text": f"{zak.jmeno} {zak.prijmeni} ({trida})"
            })
            
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Chyba při vyhledávání žáka: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/vyhledani")
def vyhledani_stranka():
    query = request.args.get("query", "").strip()
    zaky = vyhledat_zaky(query) if len(query) >= 2 else []

    vybrany_rok_od = session.get("vybrany_skolni_rok_od")
    
    return render_template(
        "vyhledani.html",
        query=query,
        zaky=zaky,
        vybrany_skolni_rok=vybrany_rok_od  # přidání pro {{ zak.get_trida(...) }}
    )

@app.route("/zak/<int:zak_id>")
def detail_zaka(zak_id):
    try:
        # Získání vybraného školního roku
        vybrany_skolni_rok = None
        if 'vybrany_skolni_rok_od' in session:
            vybrany_skolni_rok = session['vybrany_skolni_rok_od']
        
        # Získání žáka
        zak = get_zak_by_id(zak_id)
        if not zak:
            flash("Žák nebyl nalezen", "error")
            return redirect(url_for('zobraz_zaky'))
        
        # Diagnostika: Kontrola povinných údajů u žáka
        if zak.cislo_tridy is None or zak.rok_nastupu_2_stupen is None:
            app.logger.warning(f"❌ Chybí údaje pro výpočet ročníku u žáka {zak.jmeno} {zak.prijmeni} (ID: {zak.id})")
            flash("Chybí údaje pro výpočet ročníku žáka.", "danger")
            return redirect(url_for("zobraz_zaky"))
            
        # Získání všech disciplín a zajištění, že mají nastavený typ
        disciplines = get_all_disciplines()
        
        # Inicializace typu disciplín, pokud ještě nejsou nastaveny
        for discipline in disciplines:
            if discipline.typ is None:
                if discipline.nazev in ["Referát", "Reprezentace školy", "Nošení cvičebního úboru", 
                                       "Vedení rozcvičky", "Mimoškolní aktivita (např. screenshot aplikace sledující aktivitu)", 
                                       "Aktivní přístup, snaha", "Zlepšení výkonu od posledního měření", 
                                       "Pomoc s organizací", "Ostatní plusové body"]:
                    discipline.typ = 'bonus'
                elif discipline.nazev in ["Nenošení cvičebního úboru", "Bezpečnostní riziko (gumička, boty, …)", 
                                         "Nekázeň (rušení, neperespektování pokynů, …)", "Ostatní mínusové body"]:
                    discipline.typ = 'penalty'
                else:
                    discipline.typ = 'regular'
        
        # Získání aktuálního ročníku žáka
        rocnik = None
        if vybrany_skolni_rok and zak.rok_nastupu_2_stupen:
            # Výpočet ročníku: číslo třídy + rozdíl let mezi vybraným rokem a rokem nástupu
            rocnik = zak.cislo_tridy + (vybrany_skolni_rok - zak.rok_nastupu_2_stupen)
            # Omezení na rozsah 6-9 tříd
            rocnik = max(6, min(9, rocnik))
        else:
            # Defaultní hodnota, pokud není známý ročník
            rocnik = zak.cislo_tridy if zak.cislo_tridy else 6
            
        # Důležité: Pro testovací účely u žáků z 9. třídy
        # Žák, který nastoupil do 9. třídy, by měl zůstat v 9. třídě pro účely testů
        if zak.cislo_tridy == 9 and rocnik > 9:
            rocnik = 9
        
        # Výpočet bodového rozmezí pro známky
        bodove_rozmezi = vypocet_rozmezi_bodu(zak.pohlavi, rocnik if rocnik else 6)
        
        # Načtení existujících výkonů
        reference_scores = get_student_performances(zak_id, rocnik=rocnik, skolni_rok=vybrany_skolni_rok)
        
        # Příprava dat pro šablonu
        performance_data = {}
        for ReferenceScore in reference_scores:
            if ReferenceScore and ReferenceScore.discipline_id:
                performance_data[ReferenceScore.discipline_id] = {
                    'vykon': ReferenceScore.vykon or '',
                    'body': ReferenceScore.body or 0
                }
        
        # Obecná oprava pro zpracování výkonů
        discipliny_sum = {}
        for ReferenceScore in reference_scores:
            if ReferenceScore.discipline_id not in discipliny_sum:
                discipliny_sum[ReferenceScore.discipline_id] = 0
            discipliny_sum[ReferenceScore.discipline_id] += ReferenceScore.vykon or 0  # Oprava: ochrana proti None

        return render_template(
            "detail_zaka.html", 
            zak=zak, 
            disciplines=disciplines, 
            rocnik=rocnik, 
            bodove_rozmezi=bodove_rozmezi,
            vybrany_rok=vybrany_skolni_rok,
            reference_scores=performance_data,
            FORMATY_DISCIPLIN=FORMATY_DISCIPLIN  # Přidáme slovník formátů do kontextu šablony
        )
    except Exception as e:
        app.logger.error(f"Chyba při zobrazení detailu žáka: {e}")
        return render_template("error.html", error=f"Chyba při zobrazení detailu žáka: {e}")

@app.route("/nacti_vykony")
def nacti_vykony():
    """Načte výkony žáka pro daný ročník."""
    try:
        zak_id = request.args.get('zak_id', type=int)
        rocnik = request.args.get('rocnik', type=int)
        
        if not zak_id or not rocnik:
            return jsonify({"error": "Chybí ID žáka nebo ročník"}), 400
        
        # Získání žáka pro kontrolu
        zak = get_zak_by_id(zak_id)
        if not zak:
            return jsonify({"error": "Žák nebyl nalezen"}), 404
            
        # Získání všech disciplín
        disciplines = get_all_disciplines()
        discipline_dict = {d.id: d for d in disciplines}
        
        # Získání výkonů žáka
        performances = Performance.query.filter_by(zak_id=zak_id, rocnik=rocnik).all()
        
        # Sestavení JSON odpovědi
        results = []
        for perf in performances:
            disciplina = discipline_dict.get(perf.discipline_id)
            if disciplina:
                results.append({
                    "disciplina_id": perf.discipline_id,
                    "disciplina_nazev": disciplina.nazev,
                    "vykon": perf.vykon or "",  # Oprava: Prázdný řetězec místo None
                    "body": perf.body or 0,     # Oprava: 0 místo None
                    "rocnik": perf.rocnik
                })
        
        return jsonify({"vykony": results})
    except Exception as e:
        app.logger.error(f"Chyba při načítání výkonů: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/student_summary")
def student_summary():
    """Vrátí souhrn výkonů žáka ve formátu JSON."""
    try:
        zak_id = request.args.get('zak_id', type=int)
        rocnik = request.args.get('rocnik', type=int)
        skolni_rok = request.args.get('skolni_rok', type=int)
        
        if not zak_id:
            return jsonify({"error": "Chybí ID žáka"}), 400
            
        summary = get_student_summary(zak_id, rocnik, skolni_rok)
        return jsonify(summary)
    except Exception as e:
        app.logger.error(f"Chyba při získávání souhrnu žáka: {e}")
        return jsonify({"error": str(e)}), 500

def inicializovat_databazi():
    """Inicializuje databázi výchozími daty, pokud je prázdná."""
    try:
        # Kontrola existence tabulek
        db.create_all()
        app.logger.info("🚀 Inicializace databáze - přidávám výchozí školní rok...")
        
        # Přidání výchozího školního roku, pokud žádný neexistuje
        if not SkolniRok.query.first():
            skolni_rok = SkolniRok()
            skolni_rok.rok_od = 2025
            skolni_rok.rok_do = 2026
            skolni_rok.aktualni = True
            db.session.add(skolni_rok)
            db.session.commit()
            app.logger.info(f"✅ Přidán výchozí školní rok {skolni_rok.rok_od}/{skolni_rok.rok_do}")
    except Exception as e:
        app.logger.error(f"Chyba při inicializaci databáze: {e}")

# ========= ODKAZY A INFORMACE ==========

@app.route("/odkazy_a_informace/", methods=["GET", "POST"])
@app.route("/odkazy_a_informace", methods=["GET", "POST"])
@app.route("/odkazy", methods=["GET", "POST"])  # Pro zpětnou kompatibilitu
def odkazy_a_informace():
    """Zobrazí stránku s odkazy, informacemi a soubory."""
    
    # Načtení odkazů z databáze
    try:
        odkazy = get_all_odkazy()
    except Exception as e:
        flash(f"❌ Chyba při načítání odkazů: {str(e)}", "error")
        odkazy = []
    
    # Seskupení odkazů podle kategorií
    odkazy_podle_kategorii = group_odkazy_by_category(odkazy)
    
    # Pokud nemáme žádné odkazy, vytvoříme ukázkové
    if not odkazy_podle_kategorii:
        vytvorit_vychozi_odkazy()
        odkazy = get_all_odkazy()
        odkazy_podle_kategorii = group_odkazy_by_category(odkazy)
    
    # Načtení informací z databáze
    try:
        informace = get_all_informace()
    except Exception as e:
        flash(f"❌ Chyba při načítání informací: {str(e)}", "error")
        informace = []
    
    # Kontrola a vytvoření složky pro soubory
    upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)

    # Získání seznamu nahraných souborů
    try:
        soubory = get_all_soubory()
    except Exception as e:
        flash(f"❌ Chyba při načítání souborů: {str(e)}", "error")
        soubory = []

    # Aktuální datum pro formulář
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Seznam kategorií pro select
    kategorie_list = list(odkazy_podle_kategorii.keys()) if odkazy_podle_kategorii else ["Škola", "Sport", "Učivo"]

    return render_template(
        "odkazy_a_informace.html", 
        odkazy_podle_kategorii=odkazy_podle_kategorii,
        informace=informace,
        soubory=soubory,
        today_date=today_date,
        kategorie_list=kategorie_list
    )

@app.route("/pridat_odkaz", methods=["POST"])
def pridat_odkaz():
    """Přidá nový odkaz."""
    try:
        nazev = request.form.get("nazev")
        url = request.form.get("url")
        kategorie = request.form.get("kategorie")
        
        if not all([nazev, url, kategorie]):
            flash("Vyplňte všechna povinná pole!", "warning")
            return redirect(url_for("odkazy_a_informace"))
            
        # Přidání http:// pokud chybí
        if url and not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
            
        create_odkaz(nazev, url, kategorie)
        db.session.commit()
        
        flash("Odkaz byl úspěšně přidán!", "success")
        return redirect(url_for("odkazy_a_informace"))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Chyba při přidávání odkazu: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("odkazy_a_informace"))

@app.route("/pridat_informaci", methods=["POST"])
def pridat_informaci():
    """Přidá novou informaci do databáze."""
    try:
        nadpis = request.form["nadpis"]
        text = request.form["text"]
        datum_str = request.form["datum"]
        
        # Převod řetězce na datum
        if datum_str:
            datum = datetime.strptime(datum_str, "%Y-%m-%d")
        else:
            datum = datetime.now()
        
        create_informace(nadpis, text, datum)
        db.session.commit()
        
        flash(f"✅ Informace '{nadpis}' byla úspěšně přidána!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Chyba při přidávání informace: {str(e)}", "error")
    
    return redirect(url_for("odkazy_a_informace"))

@app.route("/nahrat_soubor", methods=["POST"])
def nahrat_soubor():
    """Nahraje nový soubor."""
    try:
        # Kontrola, zda byl soubor přiložen
        if 'soubor' not in request.files:
            flash("Nebyl vybrán žádný soubor!", "warning")
            return redirect(url_for("odkazy_a_informace"))
            
        file = request.files['soubor']
        popis = request.form.get("popis", "")
        
        if file.filename == '':
            flash("Nebyl vybrán žádný soubor!", "warning")
            return redirect(url_for("odkazy_a_informace"))
            
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            flash("Tento typ souboru není podporován!", "warning")
            return redirect(url_for("odkazy_a_informace"))
        
        create_soubor(file, file.filename, popis)
        db.session.commit()
        
        flash("Soubor byl úspěšně nahrán!", "success")
        return redirect(url_for("odkazy_a_informace"))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Chyba při nahrávání souboru: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("odkazy_a_informace"))

@app.route("/smazat_odkaz/<int:odkaz_id>", methods=["GET"])
def smazat_odkaz(odkaz_id):
    """Smaže odkaz."""
    try:
        if delete_odkaz(odkaz_id):
            flash("Odkaz byl úspěšně smazán!", "success")
        else:
            flash("Odkaz nebyl nalezen!", "warning")
            
        return redirect(url_for("odkazy_a_informace"))
    except Exception as e:
        app.logger.error(f"Chyba při mazání odkazu: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("odkazy_a_informace"))

@app.route("/smazat_informaci/<int:informace_id>", methods=["GET"])
def smazat_informaci(informace_id):
    """Smaže informaci."""
    try:
        if delete_informace(informace_id):
            flash("Informace byla úspěšně smazána!", "success")
        else:
            flash("Informace nebyla nalezena!", "warning")
            
        return redirect(url_for("odkazy_a_informace"))
    except Exception as e:
        app.logger.error(f"Chyba při mazání informace: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("odkazy_a_informace"))

@app.route("/smazat_soubor/<int:soubor_id>", methods=["GET"])
def smazat_soubor(soubor_id):
    """Smaže soubor."""
    try:
        if delete_soubor(soubor_id):
            flash("Soubor byl úspěšně smazán!", "success")
        else:
            flash("Soubor nebyl nalezen!", "warning")
            
        return redirect(url_for("odkazy_a_informace"))
    except Exception as e:
        app.logger.error(f"Chyba při mazání souboru: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("odkazy_a_informace"))

@app.route("/stahnout_soubor/<path:filename>", methods=["GET"])
def stahnout_soubor(filename):
    """Stáhne soubor."""
    try:
        upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        return send_from_directory(upload_folder, filename, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Chyba při stahování souboru: {str(e)}")
        flash(f"Došlo k chybě: {str(e)}", "danger")
        return redirect(url_for("odkazy_a_informace"))
    
@app.route("/zebricky_a_statistiky")
def zebricky_a_statistiky():
    try:
        disciplines = get_all_disciplines()
        skolni_roky = get_all_skolni_roky()

        # Načteme zvolené roky ze session
        rok_od = session.get("vybrany_skolni_rok_od")
        rok_do = session.get("vybrany_skolni_rok_do")

        # Najdeme odpovídající objekt školního roku
        vybrany_rok = None
        if rok_od:
            vybrany_rok = SkolniRok.query.filter_by(rok_od=rok_od).first()
            if not vybrany_rok:
                flash("Školní rok není platný nebo nebyl vybrán.", "warning")
                return redirect(url_for("home"))

        rocnik = request.args.get('rocnik', 'all')
        vybrany_rocnik = rocnik or "all"

        # TODO: sem přijde výběr výkonů podle vybrany_rok a rocnik
        discipline_performances = []

        return render_template(
            "zebricky_a_statistiky.html",
            disciplines=disciplines,
            skolni_roky=skolni_roky,
            vybrany_skolni_rok=vybrany_rok,  # 👉 objekt, ne string
            vybrany_rocnik=vybrany_rocnik,
            discipline_performances=discipline_performances
        )
    except Exception as e:
        app.logger.error(f"Chyba při zobrazení žebříčků: {e}")
        return render_template("error.html", error=f"Chyba při zobrazení žebříčků: {e}")

@app.route("/admin", methods=["GET"])
def admin():
    """Administrační rozhraní aplikace."""
    try:
        # Získání všech školních roků pro formulář
        skolni_roky = get_all_skolni_roky()
        
        return render_template(
            "admin.html", 
            skolni_roky=skolni_roky,
            aktualni_rok=SkolniRok.query.filter_by(aktualni=True).first()
        )
    except Exception as e:
        app.logger.error(f"❌ Chyba administračního rozhraní: {e}")
        flash(f"Došlo k chybě: {e}", "danger")
        return redirect(url_for("home"))

@app.route("/admin/posunout_rocnik", methods=["POST"])
def admin_posunout_rocnik():
    """Administrativní funkce pro roční posun žáků."""
    try:
        # Získání zdrojového a cílového školního roku
        z_roku_id = request.form.get("z_roku_id")
        do_roku_id = request.form.get("do_roku_id")
        
        if not z_roku_id or not do_roku_id:
            flash("Musíte vybrat oba školní roky!", "warning")
            return redirect(url_for("admin"))
        
        # Načtení školních roků z databáze
        z_roku = SkolniRok.query.get(z_roku_id)
        do_roku = SkolniRok.query.get(do_roku_id)
        
        if not z_roku or not do_roku:
            flash("Jeden nebo oba vybrané školní roky neexistují!", "warning")
            return redirect(url_for("admin"))
        
        # Kontrola, zda jde o po sobě jdoucí roky
        if do_roku.rok_od != z_roku.rok_od + 1:
            flash(f"Nelze posunout žáky z roku {z_roku.rok_od}/{z_roku.rok_do} do roku {do_roku.rok_od}/{do_roku.rok_do}. Roky musí být po sobě jdoucí.", "warning")
            return redirect(url_for("admin"))
        
        # Získání všech žáků
        vsichni_zaci = get_all_zaci()
        
        posunuto = 0
        absolventi = 0
        
        for zak in vsichni_zaci:
            # Přeskočit žáky, kteří již jsou absolventi
            if zak.skolni_rok_odchodu_od and zak.skolni_rok_odchodu_od <= z_roku.rok_od:
                continue
                
            # Získání aktuálního ročníku žáka pro zdrojový rok
            if zak.rok_nastupu_2_stupen:
                rocnik_zdroj = zak.cislo_tridy
                
                # Výpočet nového ročníku
                if rocnik_zdroj < 9:
                    # Žák postoupí o ročník výš
                    zak.cislo_tridy = rocnik_zdroj + 1
                    posunuto += 1
                    app.logger.info(f"Žák {zak.jmeno} {zak.prijmeni} posunut z {rocnik_zdroj}. do {zak.cislo_tridy}. třídy")
                elif rocnik_zdroj == 9:
                    # Žák ukončil 9. třídu - stává se absolventem
                    zak.skolni_rok_odchodu_od = do_roku.rok_od
                    zak.skolni_rok_odchodu_do = do_roku.rok_do
                    absolventi += 1
                    app.logger.info(f"Žák {zak.jmeno} {zak.prijmeni} z 9. třídy označen jako absolvent")
        
        # Uložení změn
        db.session.commit()
        
        # Nastavení nového roku jako aktuálního
        do_roku.aktualni = True
        z_roku.aktualni = False
        db.session.commit()
        
        flash(f"Úspěšně posunuto {posunuto} žáků do nového ročníku. {absolventi} žáků označeno jako absolventi. Aktuální rok nastaven na {do_roku.rok_od}/{do_roku.rok_do}.", "success")
        return redirect(url_for("admin"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ Chyba při posunu žáků: {e}")
        flash(f"Došlo k chybě při posunu žáků: {e}", "danger")
        return redirect(url_for("admin"))

if __name__ == "__main__":
    print("🌐 Aplikace běží na adrese: http://127.0.0.1:5000/")
    app.run(debug=True, host='0.0.0.0', port=5000)
