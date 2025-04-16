import os
import shutil
import subprocess
import sys

print("🔍 Kontroluji a instaluji balíčky z requirements.txt...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
    print("✅ Všechny potřebné balíčky byly nainstalovány/aktualizovány.")
except subprocess.CalledProcessError as e:
    print(f"❌ Chyba při instalaci balíčků: {e}")
    sys.exit(1)

from flask import Flask
from db_config import db, DATABASE_URI
from sqlalchemy import text, inspect
from import_skolni_roky import import_skolni_roky
from import_zaci import import_zaci
from import_bodovaci_databaze import import_excel

# Inicializace Flask aplikace
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Smazat složku migrations pokud existuje
migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
if os.path.exists(migrations_path):
    print(f"🗑️ Mažu složku migrací: {migrations_path}")
    shutil.rmtree(migrations_path)
    print("✅ Složka migrací vymazána.")

with app.app_context():
    print("🗑️ Mažu databázi...")
    # Explicitně smazat alembic_version pro jistotu
    db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
    db.drop_all()
    print("✅ Databáze vymazána.")

    print("🛠️ Vytvářím tabulky...")
    db.create_all()
    print("✅ Tabulky vytvořeny.")

    # Vypsat přehled vytvořených tabulek
    inspector = inspect(db.engine)
    print("📊 Vytvořené tabulky:", inspector.get_table_names())

    print("📥 Importuji školní roky...")
    import_skolni_roky("skolni_roky.xlsx")

    print("📥 Importuji žáky...")
    import_zaci("zaci.xlsx")

    print("📥 Importuji bodovací databázi...")
    import_excel("bodovaci_databaze.xlsx")

    print("🎉 Reset databáze a import dat dokončen.")
