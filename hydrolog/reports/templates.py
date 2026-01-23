"""Polish text templates for hydrological reports.

This module contains all Polish-language text templates, section headers,
method descriptions, and literature references used in report generation.
"""

from typing import Dict

# =============================================================================
# Section Headers
# =============================================================================

SECTION_HEADERS: Dict[str, str] = {
    "watershed": "## 1. Parametry Zlewni",
    "concentration": "## 2. Czas Koncentracji",
    "hietogram": "## 3. Hietogram Opadu",
    "scs_cn": "## 4. Opad Efektywny (SCS-CN)",
    "unit_hydrograph": "## 5. Hydrogram Jednostkowy",
    "convolution": "## 6. Splot Dyskretny (Konwolucja)",
    "hydrograph": "## 7. Wyniki - Hydrogram Odpływu",
    "water_balance": "## 8. Bilans Wodny",
    "appendices": "## 9. Załączniki",
}

# =============================================================================
# Method Descriptions
# =============================================================================

TC_METHODS: Dict[str, str] = {
    "kirpich": "Wzór Kirpicha (1940)",
    "nrcs": "Równanie NRCS (USDA TR-55)",
    "giandotti": "Wzór Giandottiego (1934)",
}

UH_MODELS: Dict[str, str] = {
    "scs": "Hydrogram jednostkowy SCS (NRCS)",
    "nash": "Model kaskady zbiorników Nasha (IUH)",
    "clark": "Model Clarka (IUH)",
    "snyder": "Syntetyczny hydrogram Snydera",
}

HIETOGRAM_TYPES: Dict[str, str] = {
    "block": "Rozkład blokowy (równomierny)",
    "triangular": "Rozkład trójkątny",
    "beta": "Rozkład Beta",
    "euler_ii": "Rozkład Euler II (DVWK)",
}

AMC_DESCRIPTIONS: Dict[str, str] = {
    "I": "warunki suche - najniższy potencjał odpływu",
    "II": "warunki normalne/przeciętne",
    "III": "warunki mokre - najwyższy potencjał odpływu",
}

# =============================================================================
# Report Header Template
# =============================================================================

REPORT_HEADER_TEMPLATE = """# Raport Hydrologiczny: {name}

**Data wygenerowania:** {date}
**Wygenerowano przez:** Hydrolog v{version}

---
"""

# =============================================================================
# Section Intro Texts
# =============================================================================

SECTION_INTROS: Dict[str, str] = {
    "watershed": """
Poniżej przedstawiono parametry fizjograficzne analizowanej zlewni.
""",
    "concentration": """
Czas koncentracji ($t_c$) to czas potrzebny, aby woda z najdalszego punktu zlewni
dotarła do przekroju zamykającego. Jest kluczowym parametrem określającym
odpowiedź hydrologiczną zlewni.
""",
    "hietogram": """
Hietogram przedstawia rozkład czasowy opadu. Poniżej zamieszczono parametry
opadu oraz jego rozkład w kolejnych krokach czasowych.
""",
    "scs_cn": """
Metoda SCS-CN (Soil Conservation Service - Curve Number) służy do obliczania
opadu efektywnego na podstawie charakterystyki zlewni wyrażonej liczbą CN.
Opad efektywny to ta część opadu, która bezpośrednio zasila odpływ powierzchniowy.
""",
    "unit_hydrograph": """
Hydrogram jednostkowy przedstawia odpowiedź zlewni na jednostkowy opad efektywny
(1 mm) o określonym czasie trwania. Służy do transformacji opadu efektywnego
w hydrogram odpływu metodą splotu (konwolucji).
""",
    "convolution": """
Hydrogram odpływu bezpośredniego obliczany jest jako splot dyskretny (konwolucja)
opadu efektywnego z hydrogramem jednostkowym.
""",
    "hydrograph": """
Poniżej przedstawiono wyniki obliczeń hydrogramu odpływu bezpośredniego
wraz z jego głównymi charakterystykami.
""",
    "water_balance": """
Bilans wodny przedstawia podział opadu całkowitego na poszczególne składniki:
abstrakcję początkową, infiltrację oraz opad efektywny (odpływ).
""",
}

# =============================================================================
# Formula Explanations
# =============================================================================

FORMULA_EXPLANATIONS: Dict[str, str] = {
    "scs_retention": "gdzie CN - Curve Number [-]",
    "scs_ia": "gdzie S - retencja maksymalna [mm], λ - współczynnik abstrakcji (domyślnie 0.2)",
    "scs_pe": (
        "gdzie P - opad całkowity [mm], Ia - abstrakcja początkowa [mm], "
        "S - retencja maksymalna [mm]"
    ),
    "kirpich": "gdzie L - długość cieku [km], S - spadek cieku [m/m]",
    "nrcs": (
        "gdzie L - długość hydrauliczna [m], S - retencja [mm], "
        "Y - średni spadek zlewni [%]"
    ),
    "giandotti": (
        "gdzie A - powierzchnia zlewni [km²], L - długość cieku [km], "
        "H - różnica wysokości [m]"
    ),
    "scs_uh_lag": "gdzie tc - czas koncentracji [min]",
    "scs_uh_tp": "gdzie D - czas trwania opadu [min], tlag - czas opóźnienia [min]",
    "scs_uh_qp": "gdzie A - powierzchnia zlewni [km²], tp - czas do szczytu [h]",
    "nash_iuh": (
        "gdzie n - liczba zbiorników, K - stała zbiornika [min], "
        "Γ(n) - funkcja gamma"
    ),
    "convolution": (
        "gdzie Q(n) - przepływ w kroku n, Pe(m) - opad efektywny w kroku m, "
        "UH(k) - rzędna hydrogramu jednostkowego"
    ),
}

# =============================================================================
# Literature References
# =============================================================================

REFERENCES: Dict[str, str] = {
    "scs": (
        "USDA-NRCS (1986). *Urban Hydrology for Small Watersheds*. "
        "Technical Release 55 (TR-55). Washington, D.C."
    ),
    "kirpich": (
        "Kirpich, Z.P. (1940). Time of concentration of small agricultural watersheds. "
        "*Civil Engineering*, 10(6), 362."
    ),
    "nash": (
        "Nash, J.E. (1957). The form of the instantaneous unit hydrograph. "
        "*IAHS Publication*, 45(3), 114-121."
    ),
    "clark": (
        "Clark, C.O. (1945). Storage and the Unit Hydrograph. "
        "*Transactions of the American Society of Civil Engineers*, 110, 1419-1446."
    ),
    "snyder": (
        "Snyder, F.F. (1938). Synthetic unit-graphs. "
        "*Eos, Transactions American Geophysical Union*, 19(1), 447-454."
    ),
    "giandotti": (
        "Giandotti, M. (1934). Previsione delle piene e delle magre dei corsi d'acqua. "
        "*Memorie e Studi Idrografici*, 8(2), 107-117."
    ),
    "lutz": (
        "Lutz, W. (1984). *Berechnung von Hochwasserabflüssen unter Anwendung von "
        "Gebietskenngrößen*. Mitteilungen des Instituts für Hydrologie und "
        "Wasserwirtschaft, H. 24, Universität Karlsruhe."
    ),
    "chow": (
        "Chow, V.T., Maidment, D.R., Mays, L.W. (1988). *Applied Hydrology*. "
        "McGraw-Hill, New York."
    ),
}

# =============================================================================
# Subsection Headers
# =============================================================================

SUBSECTION_HEADERS: Dict[str, Dict[str, str]] = {
    "watershed": {
        "input": "### 1.1 Dane wejściowe",
        "shape": "### 1.2 Wskaźniki kształtu",
    },
    "concentration": {
        "method": "### 2.1 Metoda obliczeniowa",
        "calculation": "### 2.2 Obliczenia",
    },
    "hietogram": {
        "params": "### 3.1 Parametry opadu",
        "distribution": "### 3.2 Rozkład czasowy",
    },
    "scs_cn": {
        "params": "### 4.1 Parametry metody",
        "retention": "### 4.2 Retencja maksymalna",
        "ia": "### 4.3 Abstrakcja początkowa",
        "pe": "### 4.4 Opad efektywny",
        "distribution": "### 4.5 Rozkład opadu efektywnego w czasie",
    },
    "unit_hydrograph": {
        "model": "### 5.1 Model",
        "params": "### 5.2 Parametry modelu",
        "formulas": "### 5.3 Wzory obliczeniowe",
        "ordinates": "### 5.4 Rzędne hydrogramu jednostkowego",
    },
    "convolution": {
        "formula": "### 6.1 Wzór",
        "description": "### 6.2 Opis procedury",
    },
    "hydrograph": {
        "characteristics": "### 7.1 Charakterystyki",
        "series": "### 7.2 Szereg czasowy",
    },
    "water_balance": {
        "summary": "### 8.1 Podsumowanie bilansu",
        "coefficient": "### 8.2 Współczynnik odpływu",
    },
}

# =============================================================================
# Parameter Labels (Polish)
# =============================================================================

PARAMETER_LABELS: Dict[str, str] = {
    # Watershed
    "area_km2": "Powierzchnia zlewni",
    "perimeter_km": "Obwód zlewni",
    "length_km": "Długość zlewni",
    "width_km": "Szerokość zlewni",
    "elevation_min_m": "Wysokość minimalna",
    "elevation_max_m": "Wysokość maksymalna",
    "elevation_mean_m": "Wysokość średnia",
    "relief_m": "Deniwelacja",
    "mean_slope_percent": "Średni spadek zlewni",
    "channel_length_km": "Długość cieku głównego",
    "channel_slope_m_per_m": "Spadek cieku głównego",
    "channel_slope_percent": "Spadek cieku głównego",
    # SCS-CN
    "cn": "Curve Number (CN)",
    "cn_ii": "CN dla AMC-II",
    "cn_adjusted": "CN skorygowany",
    "retention_mm": "Retencja maksymalna S",
    "initial_abstraction_mm": "Abstrakcja początkowa Ia",
    "ia_coefficient": "Współczynnik λ",
    # Precipitation
    "total_precip_mm": "Opad całkowity P",
    "effective_precip_mm": "Opad efektywny Pe",
    "duration_min": "Czas trwania opadu",
    "timestep_min": "Krok czasowy",
    "peak_intensity_mm_h": "Intensywność szczytowa",
    # Time
    "tc_min": "Czas koncentracji tc",
    "tlag_min": "Czas opóźnienia tlag",
    "tp_min": "Czas do szczytu tp",
    # Unit hydrograph
    "qp_m3s_mm": "Przepływ szczytowy qp",
    "tb_min": "Czas bazowy tb",
    # Nash
    "nash_n": "Liczba zbiorników n",
    "nash_k_min": "Stała zbiornika K",
    # Clark
    "clark_tc_min": "Czas koncentracji Tc",
    "clark_r_min": "Stała zbiornika R",
    # Snyder
    "snyder_L_km": "Długość cieku L",
    "snyder_Lc_km": "Odległość do centroidu Lc",
    "snyder_ct": "Współczynnik czasowy Ct",
    "snyder_cp": "Współczynnik szczytowy Cp",
    # Results
    "peak_discharge_m3s": "Przepływ szczytowy Qmax",
    "time_to_peak_min": "Czas do szczytu",
    "total_volume_m3": "Objętość odpływu V",
    "runoff_coefficient": "Współczynnik odpływu C",
}

# =============================================================================
# Units
# =============================================================================

UNITS: Dict[str, str] = {
    "area_km2": "km²",
    "perimeter_km": "km",
    "length_km": "km",
    "width_km": "km",
    "elevation_m": "m n.p.m.",
    "relief_m": "m",
    "slope_percent": "%",
    "slope_m_per_m": "m/m",
    "cn": "-",
    "retention_mm": "mm",
    "precip_mm": "mm",
    "intensity_mm_h": "mm/h",
    "time_min": "min",
    "time_h": "h",
    "discharge_m3s": "m³/s",
    "discharge_m3s_mm": "m³/s/mm",
    "volume_m3": "m³",
    "coefficient": "-",
    "n_reservoirs": "-",
}

# =============================================================================
# Appendices Content
# =============================================================================

GLOSSARY: Dict[str, str] = {
    "CN": "Curve Number - bezwymiarowy wskaźnik potencjału odpływu zlewni (0-100)",
    "AMC": "Antecedent Moisture Condition - warunki wilgotnościowe poprzedzające opad",
    "tc": "Czas koncentracji - czas przepływu wody z najdalszego punktu zlewni do przekroju zamykającego",
    "tlag": "Czas opóźnienia - czas od środka ciężkości opadu do szczytu hydrogramu",
    "tp": "Czas do szczytu - czas od początku opadu do maksimum hydrogramu",
    "UH": "Unit Hydrograph - hydrogram jednostkowy",
    "IUH": "Instantaneous Unit Hydrograph - chwilowy hydrogram jednostkowy",
    "Pe": "Opad efektywny - część opadu przekształcająca się w odpływ powierzchniowy",
    "Ia": "Abstrakcja początkowa - straty początkowe (intercepcja, zwilżenie, retencja)",
    "S": "Retencja maksymalna - maksymalna zdolność retencyjna zlewni",
    "Qmax": "Przepływ szczytowy - maksymalny przepływ w hydrogramie",
}
