from models import Zak

def get_aktivni_tridy(vybrany_skolni_rok):
    if isinstance(vybrany_skolni_rok, str) and "/" in vybrany_skolni_rok:
        vybrany_skolni_rok = int(vybrany_skolni_rok.split("/")[0])

    vsichni_zaci = Zak.query.all()
    aktivni_tridy = {}

    for zak in vsichni_zaci:
        if not all([zak.cislo_tridy, zak.pismeno_tridy, zak.rok_nastupu_2_stupen]):
            continue

        # Přeskočíme absolventy
        if zak.skolni_rok_odchodu_od and zak.skolni_rok_odchodu_od <= vybrany_skolni_rok:
            continue

        # Výpočet ročníku podle výchozí hodnoty
        rocnik = zak.cislo_tridy + (vybrany_skolni_rok - zak.rok_nastupu_2_stupen)
        if zak.cislo_tridy == 9 and rocnik > 9:
            rocnik = 9

        if 6 <= rocnik <= 9:
            klic = (rocnik, zak.pismeno_tridy)
            aktivni_tridy[klic] = aktivni_tridy.get(klic, 0) + 1

    return sorted(aktivni_tridy.items(), key=lambda x: (x[0][0], x[0][1]))

def get_absolventi_tridy(vybrany_skolni_rok):
    if isinstance(vybrany_skolni_rok, str) and "/" in vybrany_skolni_rok:
        vybrany_skolni_rok = int(vybrany_skolni_rok.split("/")[0])

    vsichni_zaci = Zak.query.filter(Zak.skolni_rok_odchodu_od <= vybrany_skolni_rok).all()
    absolventi_tridy = {}

    for zak in vsichni_zaci:
        if zak.cislo_tridy and zak.pismeno_tridy and zak.skolni_rok_odchodu_od:
            klic = (zak.cislo_tridy, zak.pismeno_tridy, zak.skolni_rok_odchodu_od)
            absolventi_tridy[klic] = absolventi_tridy.get(klic, 0) + 1

    return sorted(absolventi_tridy.items(), key=lambda x: (-x[0][2], x[0][0], x[0][1]))
