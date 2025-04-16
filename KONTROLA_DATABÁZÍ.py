from flask import Flask
from db_config import db, DATABASE_URI
from models.zak import Zak
from models.disciplines import Discipline, ReferenceScore
from models.performance import Performance
from models.skolni_rok import SkolniRok

# Nastavení aplikace
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    print("📋 Žáci:")
    for z in Zak.query.all():
        print(f"{z.prijmeni}\t{z.jmeno}\t{z.cislo_tridy}\t{z.pismeno_tridy}\t{z.pohlavi}\t{z.rok_nastupu_2_stupen}\t{z.skolni_rok_odchodu_od}\t{z.skolni_rok_odchodu_do}")

    print("\n📅 Školní roky:")
    for rok in SkolniRok.query.all():
        print(f"{rok.rok_od}/{rok.rok_do}")

    print("\n🎯 Disciplíny:")
    for d in Discipline.query.all():
        print(f"{d.nazev} – {d.jednotka} ({d.napoveda})")

    print("\n🏆 Skóre:")
    for s in ReferenceScore.query.limit(10):
        print(f"ID disciplíny {s.discipline_id} | Výkon: {s.vykon} | Body: {s.body}")

