"""
Balíček obsahující pomocné funkce pro aplikaci.

Tento modul exportuje funkce z různých modulů pro snadnější import.
"""

# Typové definice pro Pylance
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Response
    from typing import Any, Optional, Union, Tuple, Literal
    from sqlalchemy import asc, desc, and_, or_
    from werkzeug.utils import secure_filename

# Import základních funkcí z grade_utils s explicitním přejmenováním
from app_utils.grade_utils import vypocet_rozmezi_bodu, vypocet_znamky

def allowed_file(filename, allowed_extensions=None):
    """
    Kontrola, zda je přípona souboru povolená.
    
    Args:
        filename (str): Název souboru ke kontrole
        allowed_extensions (set, optional): Množina povolených přípon. Když není zadáno,
                                       použije výchozí seznam povolených přípon.
    """
    if allowed_extensions is None:
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'docx'}
        
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Importy z ostatních modulů v balíčku
# Použití try/except bloku pro odchycení případných importních chyb
try:
    # Import funkcí pro práci se žáky
    from app_utils.zaci_utils import get_all_zaci, vyhledat_zaky, get_zak_by_id
    
    # Import funkcí pro práci s třídami
    from app_utils.tridy_utils import get_aktivni_tridy, get_absolventi_tridy
    
    # Import funkcí pro práci s výkony
    from .performance_utils import (
        ziskej_body_z_vykonu,
        get_student_performances,
        save_student_performance,
        save_multiple_performances,
        get_student_summary,
        initialize_discipline_types
    )
    
    # Import funkcí pro práci s odkazy a informacemi
    from app_utils.odkazy_a_informace_utils import (
        get_all_odkazy, group_odkazy_by_category, get_all_informace, 
        get_all_soubory, create_odkaz, create_informace, 
        create_soubor, delete_odkaz, delete_informace, delete_soubor,
        vytvorit_vychozi_odkazy
    )
    
    # Import funkcí pro práci s domovskou stránkou
    from app_utils.home_utils import get_all_skolni_roky, ensure_skolni_rok_session
    
    # Import funkcí pro práci s disciplínami
    from app_utils.discipliny_utils import (
        get_all_disciplines, get_discipline_by_id, 
        get_discipline_name, get_classes_with_performances,
        get_students_with_performances
    )
except ImportError as e:
    print(f"⚠️ Varování: Některé moduly se nepodařilo importovat: {e}")

# Adaptéry pro zpětnou kompatibilitu (původně v utils.py)
def vypocet_znamky_legacy(body, pohlavi, rocnik):
    """
    Vyhodnotí známku na základě počtu bodů, pohlaví a ročníku žáka.
    Zachováno pro zpětnou kompatibilitu.
    
    Args:
        body (int): Počet bodů žáka
        pohlavi (str): Pohlaví žáka ("chlapec" nebo "dívka")
        rocnik (int): Ročník žáka (6-9)
    
    Returns:
        tuple: (známka, rozmezí bodů)
    """
    rozmezi = vypocet_rozmezi_bodu(pohlavi, rocnik)
    znamka = vypocet_znamky(body, pohlavi, rocnik)
    return znamka, rozmezi

# Exportované funkce a objekty pro snadnější import
__all__ = [
    # Základní funkce
    'vypocet_rozmezi_bodu',
    'vypocet_znamky',
    'allowed_file',
    'vypocet_znamky_legacy'
    ,
    
    # Funkce pro práci se žáky
    'get_all_zaci', 'vyhledat_zaky', 'get_zak_by_id', 'get_student_performances',
    
    # Funkce pro práci s třídami
    'get_aktivni_tridy', 'get_absolventi_tridy',
    
    # Funkce pro práci s výkony
    'ziskej_body_z_vykonu', 'get_student_performances', 
    'save_student_performance', 'save_multiple_performances',
    'get_student_summary', 'initialize_discipline_types',
    
    # Funkce pro práci s odkazy a informacemi
    'get_all_odkazy', 'group_odkazy_by_category', 'get_all_informace', 
    'get_all_soubory', 'create_odkaz', 'create_informace', 
    'create_soubor', 'delete_odkaz', 'delete_informace', 'delete_soubor',
    'vytvorit_vychozi_odkazy',
    
    # Funkce pro práci s domovskou stránkou
    'get_all_skolni_roky', 'ensure_skolni_rok_session',
    
    # Funkce pro práci s disciplínami
    'get_all_disciplines', 'get_discipline_by_id', 
    'get_discipline_name', 'get_classes_with_performances',
    'get_students_with_performances'
]
