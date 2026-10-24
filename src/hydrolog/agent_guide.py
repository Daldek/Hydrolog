"""Guide for AI agents generated from the command catalog (spec section 7.3).

:func:`agent_guide` renders ``AGENTS.md`` (``format="agents"``) and ``llms.txt``
(``format="llms"``), in Polish or English, from the hand-written templates in
``src/hydrolog/_data/agents`` (``<format>.<lang>.md``). Every marker
``<!-- hydrolog:<block> -->`` of a template is replaced by a block generated from the
command catalog (:func:`hydrolog.catalog.data_commands`), the error registry
(:data:`hydrolog.exceptions.ERROR_CODES`) and the data of this module: the principles
shared with the MCP server instructions (:func:`principles`) and the typical flows,
whose steps are catalog commands rendered as CLI lines and MCP calls. A marker that
fills a whole line takes a block of any number of lines, a marker inside a line a
one-line block; an unknown block or a block used twice is a program error
(``ValueError``).

The flows are checked while they are rendered: every step names an existing command
and gives valid options (:func:`hydrolog.catalog.validate_command`), so a renamed
option or command stops the generator instead of leaving a stale example in the guide.
The principles name options and commands through ``{opt:...}`` and ``{cmd:...}``
placeholders that are checked against the catalog in the same way.

The output depends only on the installed package (no dates, no version, no local
paths), so ``AGENTS.md`` and ``llms.txt`` in the repository root are derived files
that the tests compare byte for byte with the generator. Regenerate them after any
change of the catalog, the error registry, the templates or this module::

    hydrolog commands guide --format agents --lang pl --path AGENTS.md
    hydrolog commands guide --format llms --lang pl --path llms.txt

The CLI lines of the flows are written by the example formatter of the command line
(:func:`hydrolog.cli.parser.format_example`), imported when a flow is rendered, so they
are exactly what the CLI parses.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Final, Literal, cast

from hydrolog.catalog import Command, data_commands, get_command, validate_command
from hydrolog.catalog.spec import Lang
from hydrolog.exceptions import ERROR_CODES

__all__ = ["GuideFormat", "agent_guide", "principles"]

GuideFormat = Literal["agents", "llms"]

_MARKER: Final = re.compile(r"<!--\s*hydrolog:(?P<name>[^\s>]*)\s*-->")
_PLACEHOLDER: Final = re.compile(r"\{(?P<kind>opt|cmd):(?P<name>[^{}]+)\}")
_DASH: Final = "—"
_TEMPLATES: Final = ("_data", "agents")
_COMMAND_OF_GUIDE: Final = "commands guide"


# --- texts
# -----------------------------------------------------------------------------

# Texts of the generated blocks: (Polish, English).
_TEXTS: Final[Mapping[str, tuple[str, str]]] = {
    "read": ("odczyt", "read"),
    "write": ("zapis z nadpisaniem", "write (replaces an existing file)"),
    "read_write": (
        "odczyt; {options}: zapis z nadpisaniem",
        "read; {options}: write (replaces an existing file)",
    ),
    "one_of_options": ("dokładnie jedno z:", "exactly one of:"),
    "one_of_groups": ("dokładnie jedna grupa:", "exactly one group:"),
}
_HEADERS: Final[Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]]] = {
    "commands": (
        ("Komenda", "Narzędzie MCP", "Opis", "Opcje", "Skutek"),
        ("Command", "MCP tool", "Description", "Options", "Effect"),
    ),
    "errors": (
        ("Kod", "Tytuł", "Kod wyjścia CLI", "Znaczenie i co robić"),
        ("Code", "Title", "CLI exit code", "Meaning and what to do"),
    ),
}
# Titles of the command groups. A group of the catalog without a title here shows its
# bare name; a test requires a title for every group.
_GROUP_TITLES: Final[Mapping[str, tuple[str, str]]] = {
    "tc": ("Czas koncentracji", "Time of concentration"),
    "cn": ("Liczba CN (TR-55)", "Curve Number (TR-55)"),
    "scs": ("Opad efektywny SCS-CN", "SCS-CN effective precipitation"),
    "precip": (
        "Opady: hietogramy i opad obszarowy",
        "Precipitation: hyetographs and areal precipitation",
    ),
    "uh": ("Hydrogramy jednostkowe", "Unit hydrographs"),
    "hydrograph": ("Hydrogram odpływu", "Runoff hydrograph"),
    "morphometry": ("Morfometria zlewni", "Watershed morphometry"),
    "network": ("Sieć rzeczna", "River network"),
    "stats": ("Statystyki przepływów", "Flow statistics"),
    "hydrometrics": ("Hydrometria", "Hydrometry"),
    "soil": ("Gleby: uziarnienie i HSG", "Soil: texture and HSG"),
    "report": ("Raport obliczeniowy", "Calculation report"),
    "commands": ("Opis katalogu komend", "Description of the command catalog"),
}
# The rules of AGENTS.md, llms.txt and the instructions of the MCP server.
# ``{opt:name}``
# and ``{cmd:name}`` are checked against the catalog and replaced by the bare name.
_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    (
        "**Schemat najpierw:** `{cmd:commands list}` (spis) i `{cmd:commands schema}` "
        "(opcje, jednostki, zakresy, przykłady); w MCP `tools/list`. Nie zgaduj opcji.",
        "**Schema first:** `{cmd:commands list}` (the list) and "
        "`{cmd:commands schema}` (options, units, bounds, examples); in MCP "
        "`tools/list`. Do not guess options.",
    ),
    (
        "**Pliki zamiast tablic:** serie, stacje, odcinki sieci i zlewnie podawaj "
        "plikiem CSV/JSON (`{opt:input_file}`, `{opt:watershed_file}`...), nie wklejaj "
        "długich list liczb.",
        "**Files, not arrays:** give series, stations, network segments and watersheds "
        "as a CSV/JSON file (`{opt:input_file}`, `{opt:watershed_file}`...); do not "
        "paste long lists of numbers.",
    ),
    (
        "**Jednostki:** opis opcji podaje jednostkę (km, km2, m/m, mm, min, m3/s; "
        "spadek w m/m, nie w %); nie przeliczaj po cichu i nie zgaduj wartości "
        "użytkownika.",
        "**Units:** an option's description gives its unit (km, km2, m/m, mm, min, "
        "m3/s; slope in m/m, not %); do not convert silently or guess values the user "
        "did not give.",
    ),
    (
        "**Błędy po kodach:** `hydrolog-error/1`: decyduj po `code` i "
        "`details.option`/`details.reason`, popraw argument według `hint` i ponów; "
        "błędu nie podawaj jako wyniku.",
        "**Errors by code:** `hydrolog-error/1`: decide by `code` and "
        "`details.option`/`details.reason`, fix the argument as `hint` says and call "
        "again; never present an error as a result.",
    ),
    (
        "**Ścieżki bezwzględne w katalogach dozwolonych:** MCP odrzuca (`forbidden`) "
        "pliki spoza `--allow-dir`, a bez niego każdą opcję typu path.",
        "**Absolute paths in allowed directories:** MCP refuses (`forbidden`) files "
        "outside `--allow-dir`, and every path option without it.",
    ),
    (
        "**Zapis zastępuje:** opcje wyjściowe (`{opt:output}`, `{opt:output_path}`, "
        "`{opt:path}`) nadpisują plik bez pytania — podawaj nowe nazwy; `files` "
        "wylicza zapisane (SHA-256).",
        "**Writing replaces:** output options (`{opt:output}`, `{opt:output_path}`, "
        "`{opt:path}`) overwrite a file without asking — give new names; `files` lists "
        "what was written (SHA-256).",
    ),
    (
        "**Bez pobierania danych:** Hydrolog nie używa sieci; szeregi daje IMGWTools "
        "(`series export` → CSV), rastry gleb Kartograf (`soil download`).",
        "**No data downloads:** Hydrolog uses no network; series come from IMGWTools "
        "(`series export` → CSV), soil rasters from Kartograf (`soil download`).",
    ),
)
# What each code of the error registry means for an agent: (Polish, English).
_ERROR_ADVICE: Final[Mapping[str, tuple[str, str]]] = {
    "validation_error": (
        "zła wartość, typ albo zakres opcji, brak opcji wymaganej, nieznana opcja albo "
        "naruszona grupa `one_of`: popraw opcję z `details.option` według "
        "`details.reason` i `hint`",
        "a wrong value, type or range of an option, a missing required option, an "
        "unknown option or a violated `one_of` group: fix the option in "
        "`details.option` as `details.reason` and `hint` say",
    ),
    "not_found": (
        "nieznana komenda (`details.suggestions` podaje podobne) albo brak pliku "
        "wejściowego (`details.path`)",
        "an unknown command (`details.suggestions` lists similar ones) or a missing "
        "input file (`details.path`)",
    ),
    "calculation_error": (
        "dane poprawne formalnie, ale wyniku nie da się obliczyć (brak zbieżności, za "
        "krótka seria): zmień dane lub parametry, ponowienie bez zmian nic nie da",
        "formally valid input but no result is possible (no convergence, a series that "
        "is too short): change the data or the parameters, repeating the call will not "
        "help",
    ),
    "data_error": (
        "plik wejściowy nieczytelny albo błędny (zła kolumna, liczba, data, raster): "
        "`details.path`, `details.reason`, a dla tabeli `details.column`, "
        "`details.row` i `details.available`",
        "an unreadable or malformed input file (a wrong column, number, date or "
        "raster): `details.path`, `details.reason` and, for a table, `details.column`, "
        "`details.row` and `details.available`",
    ),
    "missing_dependency": (
        "brak dodatku opcjonalnego (`hydrolog[raster]`, `hydrolog[mcp]`, "
        "`hydrolog[visualization]`): zainstaluj go według `hint`",
        "an optional extra is not installed (`hydrolog[raster]`, `hydrolog[mcp]`, "
        "`hydrolog[visualization]`): install it as `hint` says",
    ),
    "forbidden": (
        "ścieżka poza katalogami dozwolonymi serwera MCP: użyj ścieżki w jednym z "
        "`details.allowed_dirs` (bez `--allow-dir` każda opcja typu path jest "
        "odrzucana)",
        "a path outside the directories the MCP server allows: use a path inside one "
        "of `details.allowed_dirs` (without `--allow-dir` every path option is "
        "refused)",
    ),
    "conflict": (
        "plik wyjściowy już istnieje: podaj inną ścieżkę albo `force`, żeby go "
        "zastąpić (`details.paths`, `details.reason`)",
        "the output file already exists: give another path or `force` to replace it "
        "(`details.paths`, `details.reason`)",
    ),
    "cancelled": (
        "przerwane przez użytkownika (Ctrl+C): nic nie zostało zapisane częściowo, "
        "uruchom komendę ponownie",
        "cancelled by the user (Ctrl+C): nothing was left half written, run the "
        "command again",
    ),
    "io_error": (
        "nie można zapisać pliku wyjściowego (uprawnienia, brak miejsca, katalog "
        "zamiast pliku): sprawdź `details.path`",
        "the output file cannot be written (permissions, no space, a directory instead "
        "of a file): check `details.path`",
    ),
    "internal_error": (
        "błąd w Hydrologu: zgłoś komendę, opcje i wersję (`hydrolog --version`), nie "
        "ponawiaj",
        "a bug in Hydrolog: report the command, the options and the version "
        "(`hydrolog --version`); do not retry",
    ),
}


# --- flows
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class _Step:
    """One step of a flow: a catalog command or a line of another tool.

    A step is either a catalog command (``command`` and its ``options``) or a line of
    another tool of the ecosystem (``external``; ``{store}`` and ``{station}`` stand
    for the values the reader takes from that tool). The notes are Markdown; in the
    note of an external step the same two symbols are replaced.
    """

    note_pl: str
    note_en: str
    command: str | None = None
    options: Mapping[str, object] = field(default_factory=dict)
    external: str | None = None

    def __post_init__(self) -> None:
        if (self.command is None) == (self.external is None):
            raise ValueError("A flow step needs exactly one of command and external")


@dataclass(frozen=True)
class _Flow:
    """A typical task of an agent: a title, an introduction and its steps."""

    title_pl: str
    title_en: str
    intro_pl: str
    intro_en: str
    steps: tuple[_Step, ...]


# Values that the reader takes from the other tools: (Polish, English).
_SYMBOLS: Final[Mapping[str, tuple[str, str]]] = {
    "store": ("MAGAZYN_IMGW", "IMGW_STORE"),
    "station": ("KOD_STACJI", "STATION_CODE"),
}
_WATERSHED: Final = "/dane/hydrolog/zlewnia.json"
_SERIES: Final = "/dane/hydrolog/q_dobowe.csv"
_REPORT: Final = "/dane/hydrolog/raport.md"
_HSG: Final = "/dane/hydrolog/hsg.tif"
_SOILGRIDS: Final = "/dane/kartograf/soil/global_soilgrids_{}_0-5cm_mean/bbox/{}.tif"
_AREA: Final = "626000_480000_628000_482000"
_DESIGN_STORM: Final = {
    "hietogram_type": "beta",
    "total_mm": 50,
    "duration_min": 60,
}
_FLOWS: Final[tuple[_Flow, ...]] = (
    _Flow(
        "Hydrogram projektowy ze zlewni opisanej plikiem JSON",
        "Design hydrograph of a watershed described by a JSON file",
        "Plik zlewni ma format `WatershedParameters` (`to_json()`): wymagane są "
        "`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m` i "
        "`elevation_max_m`, opcjonalne m.in. `name`, `cn`, `channel_length_km` i "
        "`channel_slope_m_per_m`. To proponowany format rodzaju "
        "`catchment_characteristics` w Retmanie.",
        "The watershed file has the `WatershedParameters` format (`to_json()`): "
        "`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m` and "
        "`elevation_max_m` are required; `name`, `cn`, `channel_length_km`, "
        "`channel_slope_m_per_m` and others are optional. It is the proposed format of "
        "the `catchment_characteristics` kind of Retman.",
        (
            _Step(
                "wskaźniki geometryczne, kształtu i rzeźby zlewni; przy okazji "
                "sprawdzasz, że plik się wczytuje (zły plik to `data_error` z "
                "`details.path` i `details.reason`).",
                "geometric, shape and relief indicators of the watershed; it also "
                "checks that the file loads (a bad file is a `data_error` with "
                "`details.path` and `details.reason`).",
                "morphometry watershed",
                {"watershed_file": _WATERSHED},
            ),
            _Step(
                "czas koncentracji (`result.tc_min`) z pól pliku zlewni (długość i "
                "spadek cieku); brak pola wymaganego przez metodę to "
                "`validation_error` z listą braków.",
                "time of concentration (`result.tc_min`) from the fields of the "
                "watershed file (channel length and slope); a field the method "
                "needs but the file lacks is a `validation_error` listing what is "
                "missing.",
                "tc watershed",
                {"watershed_file": _WATERSHED, "method": "kirpich"},
            ),
            _Step(
                "hydrogram odpływu bezpośredniego: hietogram Beta (50 mm w 60 min) → "
                "SCS-CN (`cn` z pliku, AMC II) → hydrogram jednostkowy SCS → splot; "
                "`result` ma m.in. `peak_discharge_m3s`, `time_to_peak_min`, "
                "`total_volume_m3` i `runoff_coefficient`, ostrzeżenia są w "
                "`notices`.",
                "direct runoff hydrograph: a Beta hyetograph (50 mm in 60 min) → "
                "SCS-CN (`cn` from the file, AMC II) → SCS unit hydrograph → "
                "convolution; `result` holds `peak_discharge_m3s`, "
                "`time_to_peak_min`, `total_volume_m3`, `runoff_coefficient` and "
                "more, warnings are in `notices`.",
                "hydrograph generate",
                {
                    "watershed_file": _WATERSHED,
                    "tc_method": "kirpich",
                    **_DESIGN_STORM,
                    "timestep_min": 5,
                    "uh_model": "scs",
                },
            ),
            _Step(
                "raport Markdown (wzory, tabele, bilans wodny) z tych samych opcji "
                "plus `output`; zastępuje istniejący plik, a `files` podaje jego "
                "ścieżkę i SHA-256.",
                "a Markdown report (formulas, tables, water balance) from the same "
                "options plus `output`; it replaces an existing file and `files` "
                "gives its path and SHA-256.",
                "report generate",
                {
                    "output": _REPORT,
                    "watershed_file": _WATERSHED,
                    "tc_method": "kirpich",
                    **_DESIGN_STORM,
                    "timestep_min": 5,
                    "uh_model": "scs",
                },
            ),
        ),
    ),
    _Flow(
        "Częstość wezbrań z eksportu CSV z IMGWTools",
        "Flood frequency from an IMGWTools CSV export",
        "Hydrolog niczego nie pobiera: dobowy szereg przepływów eksportuje IMGWTools "
        "(`series export`) do pliku CSV z jednostkami w nagłówku (`Q [m3/s]`), "
        "kolumną `date`, flagami wartości i atrybucją. Hydrolog wczytuje ten plik bez "
        "przetwarzania.",
        "Hydrolog downloads nothing: IMGWTools exports the daily discharge series "
        "(`series export`) to a CSV file with units in the header (`Q [m3/s]`), a "
        "`date` column, value flags and attribution. Hydrolog loads that file "
        "without preprocessing.",
        (
            _Step(
                "IMGWTools (osobne narzędzie, jego przewodnik to AGENTS.md w "
                "repozytorium IMGWTools): eksport szeregu jednej stacji do pliku; "
                "`{station}` wskazuje `imgw stations find`, `{store}` to magazyn "
                "IMGWTools. Do wiarygodnych kwantyli potrzeba co najmniej 30 lat.",
                "IMGWTools (a separate tool, its guide is AGENTS.md in the IMGWTools "
                "repository): export of one station's series to a file; "
                "`{station}` comes from `imgw stations find`, `{store}` is the "
                "IMGWTools store. Reliable quantiles need at least 30 years.",
                external=(
                    "imgw series export --root {store} --dataset pl.imgw.hydro_daily "
                    "--station {station} --variables Q --format csv "
                    f"--path {_SERIES}"
                ),
            ),
            _Step(
                "maksima roczne są wybierane z lat hydrologicznych (XI–X); kolumny "
                "podajesz nazwą bez jednostki (`Q` znajduje `Q [m3/s]`); wynik: "
                "`best_distribution` (kryterium AIC) i `distributions[].quantiles` "
                "(kwantyle dla `return_periods`); seria krótsza niż 30 lat daje "
                "ostrzeżenie w `notices`.",
                "the annual maxima are taken from the hydrological years (Nov–Oct); "
                "name the columns without the unit (`Q` finds `Q [m3/s]`); result: "
                "`best_distribution` (by AIC) and `distributions[].quantiles` "
                "(quantiles for `return_periods`); a series shorter than 30 years "
                "raises a warning in `notices`.",
                "stats flood-frequency",
                {
                    "input_file": _SERIES,
                    "value_column": "Q",
                    "date_column": "date",
                    "distribution": "all",
                    "return_periods": [10, 50, 100],
                },
            ),
            _Step(
                "wartości charakterystyczne II stopnia (WWQ … NNQ) z tego samego "
                "pliku (rok hydrologiczny XI–X).",
                "second-degree characteristic values (WWQ … NNQ) from the same file "
                "(hydrological year Nov–Oct).",
                "stats characteristic",
                {
                    "input_file": _SERIES,
                    "value_column": "Q",
                    "date_column": "date",
                    "parameter": "Q",
                },
            ),
        ),
    ),
    _Flow(
        "Grupy hydrologiczne gleb (HSG) z rastrów SoilGrids i ważone CN",
        "Hydrologic soil groups (HSG) from SoilGrids rasters and the weighted CN",
        "Hydrolog nie pobiera rastrów: ił, piasek i pył z SoilGrids (g/kg) pobiera "
        "Kartograf (`soil download`), a Hydrolog liczy z nich HSG (dodatek "
        "`hydrolog[raster]`).",
        "Hydrolog downloads no rasters: Kartograf downloads clay, sand and silt from "
        "SoilGrids (g/kg) (`soil download`) and Hydrolog computes the HSG from them "
        "(extra `hydrolog[raster]`).",
        (
            _Step(
                "Kartograf (osobne narzędzie): powtórz z `--property sand` i "
                "`--property silt`; ścieżki rastrów (`files[].file.path` odpowiedzi "
                "`--json`) są wejściami następnego kroku.",
                "Kartograf (a separate tool): repeat with `--property sand` and "
                "`--property silt`; the paths of the rasters (`files[].file.path` of "
                "the `--json` answer) are the inputs of the next step.",
                external=(
                    "kartograf soil download --property clay --depth 0-5cm "
                    f"--stat mean --bbox {_AREA.replace('_', ',')} "
                    "--bbox-crs EPSG:2180 --output /dane/kartograf --json"
                ),
            ),
            _Step(
                "raster HSG (GeoTIFF `uint8`: 0 — brak danych, 1–4 to A–D) z trzech "
                "rastrów o tym samym układzie współrzędnych, siatce i rozmiarze; "
                "zapis zastępuje istniejący plik.",
                "the HSG raster (GeoTIFF `uint8`: 0 — no data, 1–4 are A–D) from three "
                "rasters with the same coordinate system, grid and size; writing "
                "replaces an existing file.",
                "soil hsg",
                {
                    "clay_path": _SOILGRIDS.format("clay", _AREA),
                    "sand_path": _SOILGRIDS.format("sand", _AREA),
                    "silt_path": _SOILGRIDS.format("silt", _AREA),
                    "output_path": _HSG,
                },
            ),
            _Step(
                "powierzchnia i udział każdej grupy (`groups.A` … `groups.D`: "
                "`area_ha`, `percent`) oraz brak danych (`nodata`); opcjonalnie "
                "tylko prostokąt `bbox` z `bbox_crs`.",
                "the area and share of each group (`groups.A` … `groups.D`: "
                "`area_ha`, `percent`) and the no-data cells (`nodata`); optionally "
                "only the rectangle `bbox` with `bbox_crs`.",
                "soil hsg-stats",
                {"hsg_path": _HSG},
            ),
            _Step(
                "tablica CN TR-55: dla każdego pokrycia terenu i stanu CN grup A–D "
                "(jedną parę daje `cn lookup`); wybierz wiersz pokrycia terenu "
                "zlewni, tu `meadow`, stan `good`.",
                "the TR-55 CN table: the CN of the groups A–D for every land cover "
                "and condition (`cn lookup` gives one pair); take the row of the "
                "land cover of the watershed, here `meadow`, condition `good`.",
                "cn list",
            ),
            _Step(
                "CN zlewni ważone powierzchnią (`result.cn`): `area` każdej części to "
                "`area_ha` grupy z `soil hsg-stats`; przy kilku pokryciach terenu "
                "części są parami (HSG × pokrycie), a przecięcie rastrów robisz poza "
                "Hydrologiem.",
                "the area-weighted CN of the watershed (`result.cn`): the `area` of "
                "each part is the `area_ha` of the group from `soil hsg-stats`; with "
                "several land covers the parts are pairs (HSG × cover) and you "
                "intersect the rasters outside Hydrolog.",
                "cn weighted",
                {
                    "parts": [
                        {"cn": 30, "area": 75.0},
                        {"cn": 58, "area": 75.0},
                        {"cn": 71, "area": 75.0},
                        {"cn": 78, "area": 68.75},
                    ]
                },
            ),
            _Step(
                "hydrogram z samej powierzchni i CN (zamiast pliku zlewni); `tc_min` "
                "daje np. `tc watershed`.",
                "a hydrograph from the area and the CN alone (instead of a watershed "
                "file); `tc_min` comes from e.g. `tc watershed`.",
                "hydrograph generate",
                {"area_km2": 45.3, "cn": 58.85, "tc_min": 120, **_DESIGN_STORM},
            ),
        ),
    ),
    _Flow(
        "Porównanie metod czasu koncentracji",
        "Comparison of time-of-concentration methods",
        "Metody dają różne `tc` (nawet kilkukrotnie) i każda ma swój zakres "
        "stosowalności: porównaj je i przeczytaj `notices`, nie wybieraj po cichu — "
        "pokaż różnice użytkownikowi albo uzasadnij wybór. Bez pliku zlewni służą "
        "komendy metod (`tc kirpich`, `tc nrcs`, `tc giandotti`...) z samymi "
        "liczbami. `faa` i `kerby` liczą czas spływu powierzchniowego (z "
        "`overland_length_km` i `overland_slope_m_per_m`, nie z długości i spadku "
        "koryta), więc nie zastępują czasu koncentracji zlewni z korytem — do tego "
        "służy `kerby_kirpich`.",
        "The methods give different `tc` (by a factor of several) and each has its "
        "own range of validity: compare them and read `notices`, do not choose "
        "silently — show the differences to the user or justify the choice. Without a "
        "watershed file the method commands (`tc kirpich`, `tc nrcs`, `tc "
        "giandotti`...) take the numbers directly. `faa` and `kerby` give the "
        "overland flow time (from `overland_length_km` and "
        "`overland_slope_m_per_m`, not from the channel length and slope), so they "
        "do not replace the time of concentration of a watershed with a channel — "
        "`kerby_kirpich` does.",
        (
            _Step(
                "metoda Kirpicha: długość i spadek cieku z pliku zlewni.",
                "Kirpich: the channel length and slope from the watershed file.",
                "tc watershed",
                {"watershed_file": _WATERSHED, "method": "kirpich"},
            ),
            _Step(
                "metoda NRCS (TR-55): długość cieku, średni spadek zlewni "
                "(`mean_slope_m_per_m`, dopiero bez niego spadek cieku) i `cn` z "
                "pliku zlewni.",
                "NRCS (TR-55): the channel length, the mean slope of the watershed "
                "(`mean_slope_m_per_m`; the channel slope only without it) and the "
                "`cn` of the watershed file.",
                "tc watershed",
                {"watershed_file": _WATERSHED, "method": "nrcs"},
            ),
            _Step(
                "metoda Giandottiego: powierzchnia, długość i wysokość średnia nad "
                "przekrojem zamykającym; wzór jest dla dużych zlewni górskich, więc "
                "dla małej zlewni (poza zakresem z opisu komendy) wynik ma "
                "ostrzeżenie w `notices`.",
                "Giandotti: the area, the length and the mean elevation above the "
                "outlet; the formula is for large mountain watersheds, so for a small "
                "watershed (outside the range in the command description) the result "
                "carries a warning in `notices`.",
                "tc watershed",
                {"watershed_file": _WATERSHED, "method": "giandotti"},
            ),
            _Step(
                "wybraną wartość podaj jako `tc_min` (zamiast `tc_method`), np. wynik "
                "pierwszego kroku.",
                "give the chosen value as `tc_min` (instead of `tc_method`), e.g. the "
                "result of the first step.",
                "hydrograph generate",
                {"watershed_file": _WATERSHED, "tc_min": 136, **_DESIGN_STORM},
            ),
        ),
    ),
)
_EXAMPLE: Final = ("tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})
_EXTERNAL_TOOLS: Final = ("imgw", "kartograf")


# --- helpers
# ---------------------------------------------------------------------------


def _pick[T](pair: tuple[T, T], lang: Lang) -> T:
    """Return the English element of a (Polish, English) pair for ``en``, or Polish."""
    return pair[1] if lang == "en" else pair[0]


def _code(text: object) -> str:
    return f"`{text}`"


def _cell(text: str) -> str:
    """Table cell text: a pipe escaped, no line breaks."""
    return text.replace("|", "\\|").replace("\n", " ")


def _table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    lines = [
        "| " + " | ".join(_cell(text) for text in header) + " |",
        "|" + "---|" * len(header),
    ]
    lines += ["| " + " | ".join(_cell(text) for text in row) + " |" for row in rows]
    return "\n".join(lines)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _groups(commands: Sequence[Command]) -> dict[str, list[Command]]:
    """Group the commands by group, in catalog order."""
    grouped: dict[str, list[Command]] = {}
    for command in commands:
        grouped.setdefault(command.group, []).append(command)
    return grouped


def _group_title(group: str, lang: Lang) -> str:
    titles = _GROUP_TITLES.get(group)
    return group if titles is None else _pick(titles, lang)


def _checked(text: str, commands: Sequence[Command]) -> str:
    """``text`` with its ``{opt:...}``/``{cmd:...}`` placeholders checked and replaced.

    Raises
    ------
    ValueError
        If a placeholder names an option or a command that the catalog lacks.
    """
    options = {option.name for command in commands for option in command.options}
    names = {command.name for command in commands}

    def fill(match: re.Match[str]) -> str:
        known, kind = (
            (options, "option") if match["kind"] == "opt" else (names, "command")
        )
        if match["name"] not in known:
            raise ValueError(
                f"The guide names the {kind} {match['name']!r}, which the catalog "
                "does not have"
            )
        return match["name"]

    return _PLACEHOLDER.sub(fill, text)


# --- blocks
# ----------------------------------------------------------------------------


def principles(lang: Lang = "pl") -> tuple[str, ...]:
    """Return the rules for an agent, shared by the guides and the MCP instructions.

    Parameters
    ----------
    lang : {"pl", "en"}, optional
        Language of the rules, by default ``"pl"``.

    Returns
    -------
    tuple of str
        The rules as Markdown (one string per rule, without numbering): learn the
        schema first, pass files not long arrays, units, errors by code, absolute
        paths in allowed directories, writing replaces, no data downloads. The options
        and commands they name exist in the catalog.

    Raises
    ------
    InvalidParameterError
        If ``lang`` is not ``"pl"`` or ``"en"``.
    """
    language = cast(Lang, validate_command(_COMMAND_OF_GUIDE, {"lang": lang})["lang"])
    commands = data_commands()
    return tuple(_checked(_pick(rule, language), commands) for rule in _PRINCIPLES)


def _rules(lang: Lang) -> str:
    return "\n".join(
        f"{number}. {rule}" for number, rule in enumerate(principles(lang), start=1)
    )


def _summary(lang: Lang) -> str:
    commands = data_commands()
    count, groups = len(commands), len(_groups(commands))
    if lang == "en":
        return f"Commands in the catalog: {count}, in {groups} groups."
    return f"Liczba komend w katalogu: {count}, liczba grup: {groups}."


def _default(value: object) -> str:
    return value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))


def _options(command: Command, lang: Lang) -> str:
    """Options in catalog order (``*`` required, ``=`` default) and the one_of note."""
    words = []
    for option in command.options:
        word = option.name + ("*" if option.required else "")
        if option.default is not None:
            word += "=" + _default(option.normalize(option.default))
        words.append(_code(word))
    text = ", ".join(words) or _DASH
    if not command.one_of:
        return text
    single = all(len(group) == 1 for group in command.one_of)
    groups = " / ".join(
        "+".join(_code(name) for name in group) for group in command.one_of
    )
    label = _pick(_TEXTS["one_of_options" if single else "one_of_groups"], lang)
    return f"{text} ({label} {groups})"


def _effect(command: Command, lang: Lang) -> str:
    """Describe the effect of a run: reading, or writing the files of output options."""
    outputs = [option for option in command.options if option.writes]
    if not outputs:
        return _pick(_TEXTS["read"], lang)
    names = ", ".join(_code(option.name) for option in outputs)
    if any(option.required for option in outputs):
        return f"{_pick(_TEXTS['write'], lang)}: {names}"
    return _pick(_TEXTS["read_write"], lang).format(options=names)


def _commands(lang: Lang) -> str:
    sections = []
    for group, commands in _groups(data_commands()).items():
        rows = [
            (
                _code(command.name),
                _code(command.operation_id),
                command.summarize(lang),
                _options(command, lang),
                _effect(command, lang),
            )
            for command in commands
        ]
        table = _table(_pick(_HEADERS["commands"], lang), rows)
        sections.append(f"### {_code(group)} — {_group_title(group, lang)}\n\n{table}")
    return "\n\n".join(sections)


def _group_list(lang: Lang) -> str:
    """One line per group: its title and the names of its commands."""
    return "\n".join(
        f"- {_code(group)} — {_group_title(group, lang)}: "
        + ", ".join(_code(command.subcommand) for command in commands)
        for group, commands in _groups(data_commands()).items()
    )


def _error_advice(code: str, lang: Lang) -> str:
    advice = _ERROR_ADVICE.get(code)
    if advice is None:
        raise ValueError(f"The guide has no description of the error code {code!r}")
    return _pick(advice, lang)


def _errors(lang: Lang) -> str:
    rows = [
        (
            _code(spec.code),
            spec.title_en if lang == "en" else spec.title,
            str(spec.exit_code),
            _error_advice(spec.code, lang),
        )
        for spec in ERROR_CODES.values()
    ]
    return _table(_pick(_HEADERS["errors"], lang), rows)


def _error_codes() -> str:
    return ", ".join(
        f"{_code(spec.code)} ({spec.exit_code})" for spec in ERROR_CODES.values()
    )


def _cli_line(command: Command, options: Mapping[str, object]) -> str:
    """Return the command line that gives ``command`` the ``options``.

    The line is written the way the CLI parses it.
    """
    from hydrolog.cli.parser import format_example

    return format_example(command, options)


def _python_call(command: Command, options: Mapping[str, object]) -> str:
    function = command.function.partition(":")[2]
    arguments = ", ".join(f"{name}={value!r}" for name, value in options.items())
    return f"hydrolog.operations.{function}({arguments})"


def _call_example(lang: Lang) -> str:
    """Render the same command as a Python call, a CLI line and an MCP call."""
    name, options = _EXAMPLE
    command = get_command(name)
    validate_command(command, options)
    if lang == "en":
        head = f"The same command ({_code(name)}) in every interface:"
        mcp = f"- MCP: tool {_code(command.operation_id)} with the arguments "
    else:
        head = f"Ta sama komenda ({_code(name)}) w każdym interfejsie:"
        mcp = f"- MCP: narzędzie {_code(command.operation_id)} z argumentami "
    return "\n".join(
        [
            head,
            "",
            f"- Python: {_code(_python_call(command, options))}",
            f"- CLI: {_code(_cli_line(command, options))}",
            mcp + _code(_json(options)),
        ]
    )


def _external_line(step: _Step, lang: Lang) -> str:
    """Render the line of another tool, with symbols in the language of the guide."""
    assert step.external is not None
    line = step.external.format(**_symbols(lang))
    words = shlex.split(line)  # unbalanced quotes are a program error
    if words[0] not in _EXTERNAL_TOOLS:
        raise ValueError(f"The flow step runs {words[0]!r}, an unknown tool: {line}")
    return line


def _symbols(lang: Lang) -> dict[str, str]:
    return {name: _pick(pair, lang) for name, pair in _SYMBOLS.items()}


def _rendered_step(step: _Step, lang: Lang) -> tuple[str, str | None]:
    """Render the line of a step (CLI or of another tool) and its MCP call, validated.

    Raises
    ------
    NotFoundError
        If the step names a command that the catalog lacks.
    InvalidParameterError
        If the options of the step are not valid for its command.
    """
    if step.external is not None:
        return _external_line(step, lang), None
    assert step.command is not None
    command = get_command(step.command)
    validate_command(command, step.options)
    call = f"{command.operation_id} {_json(dict(step.options))}"
    return _cli_line(command, step.options), call


def _flows(lang: Lang) -> str:
    """Render the typical flows: numbered steps with a CLI line and an MCP call each."""
    sections = []
    for number, flow in enumerate(_FLOWS, start=1):
        title = _pick((flow.title_pl, flow.title_en), lang)
        lines = [
            f"### {number}. {title}",
            "",
            _pick((flow.intro_pl, flow.intro_en), lang),
            "",
        ]
        for index, step in enumerate(flow.steps, start=1):
            note = _pick((step.note_pl, step.note_en), lang)
            if step.external is not None:
                note = note.format(**_symbols(lang))
            line, call = _rendered_step(step, lang)
            lines.append(f"{index}. {_code(line)} — {note}")
            if call is not None:
                lines.append(f"   - MCP: {_code(call)}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _flows_short(lang: Lang) -> str:
    """Render the flows as titles over fenced lines of commands (for ``llms.txt``)."""
    sections = []
    for number, flow in enumerate(_FLOWS, start=1):
        title = _pick((flow.title_pl, flow.title_en), lang)
        lines = [f"**{number}. {title}**", "", "```"]
        lines += [_rendered_step(step, lang)[0] for step in flow.steps]
        lines.append("```")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _flow_symbols(lang: Lang) -> str:
    """Render the symbols of the flows (values from other tools), as code spans."""
    return ", ".join(_code(symbol) for symbol in _symbols(lang).values())


def _blocks(lang: Lang) -> dict[str, Callable[[], str]]:
    """Build the generated blocks of the guide in ``lang`` (rendered only when used)."""
    return {
        "summary": lambda: _summary(lang),
        "rules": lambda: _rules(lang),
        "call_example": lambda: _call_example(lang),
        "commands": lambda: _commands(lang),
        "groups": lambda: _group_list(lang),
        "errors": lambda: _errors(lang),
        "error_codes": _error_codes,
        "flows": lambda: _flows(lang),
        "flows_short": lambda: _flows_short(lang),
        "flow_symbols": lambda: _flow_symbols(lang),
    }


# --- templates
# -------------------------------------------------------------------------


def _render(template: str, blocks: Mapping[str, Callable[[], str]]) -> list[str]:
    """Lines of ``template``, each ending with a newline, with every marker replaced.

    Raises
    ------
    ValueError
        If a marker names an unknown block, a block is used twice or a multi-line
        block stands inside a line (program errors of a template).
    """
    used: set[str] = set()

    def block(name: str) -> str:
        if name not in blocks:
            raise ValueError(f"Unknown guide block {name!r} in a template")
        if name in used:
            raise ValueError(f"Guide block {name!r} is used twice in a template")
        used.add(name)
        return blocks[name]()

    def inline(match: re.Match[str]) -> str:
        text = block(match["name"])
        if "\n" in text:
            raise ValueError(
                f"Guide block {match['name']!r} has several lines but its marker "
                "stands inside a line of the template"
            )
        return text

    lines: list[str] = []
    for line in template.removesuffix("\n").split("\n"):
        whole = _MARKER.fullmatch(line.strip())
        if whole is not None:
            lines += block(whole["name"]).split("\n")
        else:
            lines.append(_MARKER.sub(inline, line))
    return [f"{line}\n" for line in lines]


def _template(format: GuideFormat, lang: Lang) -> str:
    resource = files("hydrolog").joinpath(*_TEMPLATES, f"{format}.{lang}.md")
    return resource.read_text(encoding="utf-8")


def agent_guide(format: GuideFormat, lang: Lang = "pl") -> str:
    r"""Generate the guide for AI agents from the command catalog.

    ``format="agents"`` gives ``AGENTS.md``: what Hydrolog is, the rules, the
    interfaces (Python, CLI, MCP), the result envelope, the errors, the input files,
    every command with its options and effect, typical flows as CLI lines and MCP
    calls, what not to do and how to work on the code. ``format="llms"`` gives
    ``llms.txt`` (at most 150 lines): a summary, the rules, the command groups, the
    flows and links to the documentation. The text depends only on the installed
    package (no dates, no version, no local paths), so the repository files
    ``AGENTS.md`` and ``llms.txt`` equal ``agent_guide(format, "pl")`` byte for byte.

    Parameters
    ----------
    format : {"agents", "llms"}
        Guide to generate: ``AGENTS.md`` or ``llms.txt``.
    lang : {"pl", "en"}, optional
        Language of the guide and of the catalog texts in it, by default ``"pl"``;
        identifiers, codes and option names are the same in both.

    Returns
    -------
    str
        UTF-8 Markdown with ``"\n"`` line ends, ending with a newline.

    Raises
    ------
    InvalidParameterError
        If ``format`` or ``lang`` is not allowed (``details.option`` names it).
    ValueError
        If a template or a flow is inconsistent with the catalog (a program error
        that the tests of the repository catch).

    Examples
    --------
    >>> guide = agent_guide("llms", "en")
    >>> guide.splitlines()[0]
    '# Hydrolog'
    """
    options = validate_command(_COMMAND_OF_GUIDE, {"format": format, "lang": lang})
    guide = cast(GuideFormat, options["format"])
    language = cast(Lang, options["lang"])
    return "".join(_render(_template(guide, language), _blocks(language)))
