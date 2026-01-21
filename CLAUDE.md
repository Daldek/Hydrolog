# Instrukcje dla Claude Code

## Środowisko Python

Używaj środowiska wirtualnego z `.venv`:
- Python: `.venv/bin/python`
- Pip: `.venv/bin/pip`

## Przed rozpoczęciem pracy

**ZAWSZE przeczytaj:**
1. `docs/PROGRESS.md` - aktualny stan projektu i zadania
2. `docs/SCOPE.md` - zakres projektu (co IN/OUT)
3. `docs/DEVELOPMENT_STANDARDS.md` - standardy kodowania
4. `docs/IMPLEMENTATION_PROMPT.md`
5. `docs/PRD.md` - Product Requirements Document
6. `docs/CHANGELOG.md`

## Workflow sesji

### Początek sesji
```bash
# 1. Przeczytaj PROGRESS.md - sekcja "Bieżąca sesja"
# 2. Sprawdź stan repo
git status
git log --oneline -5
```

### W trakcie sesji
- W razie wątpliwości zadawaj pytania
- Commituj często (małe zmiany)
- Aktualizuj CHANGELOG.md, zeby byc na biezaco ze zmianami
- Aktualizuj PROGRESS.md po każdym milestone
- Używaj Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`

### Koniec sesji
**OBOWIĄZKOWO zaktualizuj** `docs/PROGRESS.md`:
- Co zostało zrobione
- Co jest w trakcie (plik, linia, kontekst)
- Następne kroki
- Commit i push

## Git Workflow

### Gałęzie
- **main** - stabilna wersja (tylko merge z develop)
- **develop** - aktywny rozwój (ZAWSZE pracuj na tej gałęzi)

### Tagowanie (OBOWIĄZKOWE)
Claude Code MUSI automatycznie tagować wydania wersji:

```bash
# Wydanie wersji
git tag -a v0.1.0 -m "Release v0.1.0: SCS-CN hydrograph"
git push origin v0.1.0
```

**Uwaga:** Checkpointy (CP) są śledzone tylko w PROGRESS.md, bez tagów Git.

## Konwencje kodowania

- **Python:** snake_case dla zmiennych/funkcji, PascalCase dla klas
- **Docstrings:** NumPy style, w języku angielskim
- **Type hints:** wymagane wszędzie
- **Testy:** pytest, pokrycie > 80%
- **Formatowanie:** Black (88 znaków)

## Zależności zewnętrzne

- **NumPy** - obliczenia numeryczne (wymagane)
- **Kartograf** - zestaw narzędzi do pobierania NMT, pokrycia terenu i danych glebowych (opcjonalne)
- **SciPy** - funkcje gamma dla Nash IUH (opcjonalne)

Hydrolog NIE zawiera funkcji pobierania danych - to zadanie zewnętrznych bibliotek.

## Struktura modułów

```
hydrolog/
├── runoff/          # SCS-CN, hydrogramy
├── morphometry/     # Parametry fizjograficzne
├── precipitation/   # Hietogramy, interpolacja
├── network/         # Klasyfikacja sieci rzecznej
├── time/            # Czas koncentracji
└── cli/             # Interfejs CLI
```

## Komendy

```bash
# Testy
.venv/bin/python -m pytest tests/ -v

# Testy z pokryciem
.venv/bin/python -m pytest tests/ --cov=hydrolog --cov-report=html

# Formatowanie
.venv/bin/python -m black hydrolog/ tests/

# Type checking
.venv/bin/python -m mypy hydrolog/
```
