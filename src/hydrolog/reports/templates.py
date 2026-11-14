"""Polish text templates for hydrological reports.

This module contains all Polish-language text templates, section headers,
method descriptions, and literature references used in report generation.
"""


# =============================================================================
# Section Headers
# =============================================================================

SECTION_HEADERS: dict[str, str] = {
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

TC_METHODS: dict[str, str] = {
    "kirpich": "Wzór Kirpicha (1940)",
    "nrcs": "Równanie opóźnienia NRCS (USDA-NRCS 2010, NEH 630, rozdz. 15)",
    "giandotti": "Wzór Giandottiego (1934)",
    "faa": "Metoda FAA (Federal Aviation Administration 1970, AC 150/5320-5B)",
    "kerby": "Wzór Kerby'ego (1959)",
    "kerby_kirpich": "Metoda złożona Kerby-Kirpich",
}

UH_MODELS: dict[str, str] = {
    "scs": "Hydrogram jednostkowy SCS (NRCS)",
    "nash": "Model kaskady zbiorników Nasha (IUH)",
    "clark": "Model Clarka (IUH)",
    "snyder": "Syntetyczny hydrogram Snydera",
}

HIETOGRAM_TYPES: dict[str, str] = {
    "block": "Rozkład blokowy (równomierny)",
    "triangular": "Rozkład trójkątny",
    "beta": "Rozkład Beta",
    "euler_ii": "Rozkład Euler II (DVWK)",
}

AMC_DESCRIPTIONS: dict[str, str] = {
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

SECTION_INTROS: dict[str, str] = {
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
# Subsection Headers
# =============================================================================

SUBSECTION_HEADERS: dict[str, dict[str, str]] = {
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

PARAMETER_LABELS: dict[str, str] = {
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
    "flow_path_length_km": "Długość najdłuższej drogi spływu",
    "flow_path_slope_m_per_m": "Spadek najdłuższej drogi spływu",
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

UNITS: dict[str, str] = {
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
