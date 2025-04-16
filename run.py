from hejbni_kostrou import app, inicializovat_databazi
from app_utils.performance_utils import initialize_discipline_types
import logging

if __name__ == "__main__":
    # Nastavení logování
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Inicializace databáze pokud je prázdná
    try:
        with app.app_context():
            inicializovat_databazi()
            # Inicializace typů disciplín při prvním spuštění
            initialize_discipline_types()
    except Exception as e:
        logging.error(f"Chyba při inicializaci databáze: {e}")
    
    # Spuštění aplikace
    print("🌐 Aplikace běží na adrese: http://127.0.0.1:5000/")
    app.run(debug=True, host='0.0.0.0', port=5000)
