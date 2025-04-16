"""
Balíček modelů pro aplikaci Hejbni kostrou.
"""

# Nová implementace - přímé importy ze souborů
from models.zak import Zak
from models.disciplines import Discipline, ReferenceScore
from models.performance import Performance
from models.skolni_rok import SkolniRok
from models.odkazy_info import Odkaz, Informace, Soubor

# Export pro zachování kompatibility
__all__ = [
    'Zak',
    'Discipline',
    'ReferenceScore',  # Toto je správný název
    'Performance',
    'SkolniRok',
    'Odkaz',
    'Informace',
    'Soubor'
]
