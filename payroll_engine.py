"""
Moteur de calcul de paie - Burkina Faso
Reproduit fidèlement les formules du fichier Excel "Paie.xlsx"
(CNSS, IUTS par tranches, TPA, abattements, exonérations, etc.)

Toutes les fonctions sont pures (pas d'effet de bord) pour faciliter
les tests et la réutilisation dans l'app Kivy et/ou un backend.
"""

from dataclasses import dataclass, field
from typing import List, Dict


def round0(x: float) -> int:
    """Arrondi à l'entier le plus proche (comme ROUND(x,0) sous Excel)."""
    return int(round(x))


def rounddown_100(x: float) -> int:
    """Arrondi au multiple de 100 inférieur (comme ROUNDDOWN(x,-2))."""
    return int(x // 100) * 100


@dataclass
class Employee:
    """Un salarié et ses éléments de paie du mois."""
    nom: str = ""
    prenom: str = ""
    classification: str = "AUTRE"       # "CADRE" ou "AUTRE"
    salaire_base: float = 0.0           # F
    taux_prime_anciennete: float = 0.0  # en %, utilisé pour calculer G
    heure_sup: float = 0.0              # H
    sursalaire: float = 0.0             # I
    gratification: float = 0.0          # K
    indemnite_caisse: float = 0.0       # L
    indemnite_logement: float = 0.0     # M
    indemnite_fonction: float = 0.0     # N
    indemnite_transport: float = 0.0    # O
    nb_charges: int = 0                 # AB - nombre de personnes à charge (0 à 4+)
    retenue_avance: float = 0.0         # AG - avances/prêts à déduire


def calcul_iuts_bareme(base_imposable: float) -> float:
    """Barème IUTS Burkina Faso par tranches (colonne AC)."""
    aa = base_imposable
    if aa < 10000:
        return 0
    elif aa < 20000:
        return 0
    elif aa < 30000:
        return 0
    elif aa < 50000:
        return (aa - 30000) * 0.121
    elif aa < 80000:
        return (aa - 50000) * 0.139 + 2420
    elif aa < 120000:
        return (aa - 80000) * 0.157 + 6590
    elif aa < 170000:
        return (aa - 120000) * 0.184 + 12870
    elif aa <= 250000:
        return (aa - 170000) * 0.217 + 22070
    else:
        return (aa - 250000) * 0.25 + 39430


def abattement_charges(iuts_brut: float, nb_charges: int) -> int:
    """Abattement IUTS selon le nombre de personnes à charge (colonne AD)."""
    taux = {0: 1.0, 1: 0.92, 2: 0.90, 3: 0.88}.get(nb_charges, 0.86 if nb_charges >= 4 else 1.0)
    return round0(iuts_brut * taux)


def calcul_bulletin(e: Employee) -> Dict:
    """
    Calcule le bulletin de paie complet d'un salarié.
    Reproduit les colonnes F à AQ de la feuille "Feuil1".
    """
    F = e.salaire_base
    G = round0(F * e.taux_prime_anciennete / 100)   # Prim anc
    H = e.heure_sup
    I = e.sursalaire
    K = e.gratification
    L = e.indemnite_caisse
    M = e.indemnite_logement
    N = e.indemnite_fonction
    O = e.indemnite_transport

    # Q : Rémunération totale
    Q = F + G + H + I + K + L + M + N + O

    # S : CNSS salarié (5.5% plafonné à 44 000)
    S = round0(Q * 0.055) if Q <= 800000 else 44000

    # T : Plafond fiscal = 8% * (F+G+H+I)
    T = 0.08 * (F + G + H + I)

    # U : Salaire brut fiscal
    U = round0(Q - T) if S >= T else round0(Q - S)

    # V : Abattement forfaitaire 20% (cadre) ou 25% (autre)
    base_ghi = F + G + H + I
    V = round0(0.2 * base_ghi) if e.classification.upper() == "CADRE" else round0(0.25 * base_ghi)

    # W, X, Y : Exonérations des indemnités (logement, fonction, transport)
    def exo(indemnite, taux, plafond_bas, plafond_haut):
        seuil = taux * U
        if seuil <= indemnite:
            return seuil if seuil <= plafond_bas else plafond_bas
        else:
            return plafond_haut if indemnite >= plafond_bas else indemnite

    W = exo(M, 0.20, 75000, 75000)
    X = exo(N, 0.05, 50000, 50000)
    Y = exo(O, 0.05, 30000, 30000)

    Z = V + W + X + Y  # Total exonérations

    # AA : Base imposable (arrondie à la centaine inférieure)
    AA = rounddown_100(U - Z)

    # AC : IUTS brut (barème)
    AC = calcul_iuts_bareme(AA)

    # AD : IUTS net (après abattement charges de famille)
    AD = abattement_charges(AC, e.nb_charges)

    # AE : Salaire net (avant retenue 1% et avances)
    AE = Q - S - AD

    # AF : Retenue obligatoire 1%
    AF = round0(AE * 0.01)

    # AG : Retenue avances/prêts
    AG = e.retenue_avance

    # AH : Net perçu
    AH = AE - AF - AG

    # Charges patronales
    AJ = round0(Q * 0.03)   # TPA 3%
    AK = round0(Q * 0.16)   # CNSS patronale 16%
    AL = AJ + AK            # Total charges patronales

    AN = Q + AL              # Coût total employeur
    AP = AK + S               # CNSS total (salarié + patronal)
    AQ = AJ + AD               # IUTS + TPA

    return {
        "nom": e.nom, "prenom": e.prenom, "classification": e.classification,
        "F_salaire_base": F, "G_prime_anciennete": G, "H_heure_sup": H,
        "I_sursalaire": I, "K_gratification": K, "L_indemnite_caisse": L,
        "M_indemnite_logement": M, "N_indemnite_fonction": N, "O_indemnite_transport": O,
        "Q_remuneration_totale": Q, "S_cnss_salarie": S, "T_plafond_fiscal": round0(T),
        "U_salaire_brut": U, "V_abattement": V, "W_exo_logement": round0(W),
        "X_exo_fonction": round0(X), "Y_exo_transport": round0(Y), "Z_total_exo": round0(Z),
        "AA_base_imposable": AA, "AC_iuts_brut": round0(AC), "AD_iuts_net": AD,
        "AE_salaire_net": AE, "AF_retenue_1pct": AF, "AG_retenue_avance": AG,
        "AH_net_percu": AH, "AJ_tpa": AJ, "AK_cnss_patronale": AK,
        "AL_total_charges_patronales": AL, "AN_cout_total": AN,
        "AP_cnss_total": AP, "AQ_iuts_tpa": AQ,
    }


def calcul_bordereau_comptable(bulletins: List[Dict]) -> Dict:
    """
    Génère le bordereau d'écriture comptable agrégé (feuille "Saisie comptable")
    à partir de la liste des bulletins calculés.
    """
    def s(key):
        return sum(b[key] for b in bulletins)

    debit = [
        {"compte": "661100", "libelle": "SAL DE BASE", "montant": s("F_salaire_base")},
        {"compte": "663100", "libelle": "INDEMNITE LOGEMENT", "montant": s("M_indemnite_logement")},
        {"compte": "663200", "libelle": "INDEMNITE DE FONCTION", "montant": s("N_indemnite_fonction")},
        {"compte": "663400", "libelle": "INDEMNITE DE TRANSPORT", "montant": s("O_indemnite_transport")},
        {"compte": "661100", "libelle": "SUR SALAIRE", "montant": s("I_sursalaire")},
    ]
    credit = [
        {"compte": "422000", "libelle": "SALAIRE NET A VIREMENT", "montant": s("AH_net_percu")},
        {"compte": "447220", "libelle": "RETENUE OBLIGATOIRE 1%", "montant": s("AF_retenue_1pct")},
        {"compte": "421000", "libelle": "RETENUE AVANCE / SALAIRES", "montant": s("AG_retenue_avance")},
        {"compte": "431300", "libelle": "CNSS EMPLOYE", "montant": s("S_cnss_salarie")},
        {"compte": "447210", "libelle": "IUTS", "montant": s("AD_iuts_net")},
    ]
    sous_total_1_debit = sum(d["montant"] for d in debit)
    sous_total_1_credit = sum(c["montant"] for c in credit)

    cnss_patronale = s("AK_cnss_patronale")
    tpa = s("AJ_tpa")

    debit2 = [
        {"compte": "664100", "libelle": "CNSS PATRONALE", "montant": cnss_patronale},
        {"compte": "664200", "libelle": "TPA", "montant": tpa},
    ]
    credit2 = [
        {"compte": "431300", "libelle": "CNSS PATRONALE", "montant": cnss_patronale},
        {"compte": "447230", "libelle": "TPA", "montant": tpa},
    ]
    sous_total_2 = cnss_patronale + tpa

    return {
        "debit_1": debit, "credit_1": credit,
        "sous_total_1_debit": sous_total_1_debit, "sous_total_1_credit": sous_total_1_credit,
        "debit_2": debit2, "credit_2": credit2,
        "sous_total_2": sous_total_2,
        "grand_total_debit": sous_total_1_debit + sous_total_2,
        "grand_total_credit": sous_total_1_credit + sous_total_2,
    }


if __name__ == "__main__":
    # Petit test de vérification avec les données de l'exemple Excel (KAF JUILLE)
    emp = Employee(
        nom="KAF", prenom="JUILLE", classification="AUTRE",
        salaire_base=101933, indemnite_logement=30000,
        indemnite_fonction=15000, indemnite_transport=20000,
        retenue_avance=67500,
    )
    bulletin = calcul_bulletin(emp)
    for k, v in bulletin.items():
        print(f"{k}: {v}")
