"""
Utility funkce pro výpočet hodnocení a známek.
"""

def vypocet_rozmezi_bodu(pohlavi, rocnik):
    """
    Vypočítá rozmezí bodů pro známky na základě pohlaví a ročníku.
    """
    base_reference = 130 if pohlavi.lower() == "chlapec" else 110
    reference_value = base_reference * (0.9 ** (9 - rocnik))

    grade_ranges = {
        1: f"{round(reference_value * 1.0)} - 200",
        2: f"{round(reference_value * 0.9)} - {round(reference_value * 1.0) - 1}",
        3: f"{round(reference_value * 0.8)} - {round(reference_value * 0.9) - 1}",
        4: f"20 - {round(reference_value * 0.8) - 1}",
        5: "0 - 19"
    }

    return grade_ranges


def vypocet_znamky(body, pohlavi, rocnik):
    """
    Vyhodnotí známku na základě bodů, pohlaví a ročníku studenta.
    """
    if body is None:
        return None

    base_reference = 130 if pohlavi.lower() == "chlapec" else 110
    reference_value = base_reference * (0.9 ** (9 - rocnik))

    if body >= round(reference_value * 1.0):
        return 1
    elif body >= round(reference_value * 0.9):
        return 2
    elif body >= round(reference_value * 0.8):
        return 3
    elif body >= 20:
        return 4
    else:
        return 5
