# Hydrolog: instructions for agents developing the project

Hydrolog is a Python library, CLI (`hydrolog`) and MCP server for hydrological
calculations (time of concentration, SCS-CN, unit hydrographs, flow statistics,
hydrologic soil groups). Profile `tool` (DEV-1.1). It downloads nothing and has no
data store: Kartograf and IMGWTools supply the input files. User documentation:
[README.md](README.md). Nogat standard 2.1:
[DEVELOPMENT_STANDARDS](https://github.com/Daldek/Nogat/blob/main/standards/DEVELOPMENT_STANDARDS.md),
[AGENT_INTERFACE](https://github.com/Daldek/Nogat/blob/main/standards/AGENT_INTERFACE.md),
[DOCUMENTATION_STANDARDS](https://github.com/Daldek/Nogat/blob/main/standards/DOCUMENTATION_STANDARDS.md).

## Critical rules

- Work on a topic branch `<type>/<topic>` from `develop`; Conventional Commits in English
  (DEV-4.1); no AI attribution in messages (DEV-4.3); git identity is set per
  repository (DEV-4.2).
- Without the author's approval in the session never merge, tag, publish or rewrite
  shared history (DEV-3.3).
- Run `scripts/gate.sh` before every commit and do not commit while it fails (DEV-7.6).
- Generated files (`AGENTS.md`, `llms.txt`) are never edited by hand: regenerate them
  with `hydrolog commands guide` (see Commands); a contract test compares them with the
  generator (DEV-10.4).
- The catalog (`src/hydrolog/catalog/groups/`) is the single source of truth for the
  library API, CLI, MCP tools and guides (AGI-1.1). Add a command there, not in the CLI.
- Code, comments, docstrings, commit messages and docs are English (DEV-2.1); human
  output is Polish by default and English with `--lang en`; machine output is English.
- Option names carry the unit (`area_km2`, `tc_min`, `slope_m_per_m`; DEV-8.2) and
  docstrings state units in brackets (`[km2]`; DEV-9.2).
- Errors use the registry codes only (ERR-1); finer precision goes to
  `details.reason`. `src/hydrolog/_errors.py` is generated: `uv run scripts/generate_errors.py`.
- A change to a command, option, result schema or error code is a public-interface
  change: start with a plan in `docs/plans/` (DEV-17.4) and record decisions as ADRs.

## Environment and commands

```bash
uv sync --locked --all-extras      # environment in .venv (DEV-6.2, DEV-6.3)
scripts/gate.sh                    # ruff format, ruff check, mypy, pytest + coverage, commits
uv run pytest tests/unit -q        # a part of the tests
uv run hydrolog --help             # the CLI
uv run hydrolog mcp --allow-dir .  # the MCP server (stdio)
# regenerate the guides after changing the catalog, templates or flows:
uv run hydrolog commands guide --format agents --output AGENTS.md --force
uv run hydrolog commands guide --format llms --output llms.txt --force
```

Python 3.12 or newer. The tests are offline; there are no `live` tests. Coverage floor 80%.
A change that touches docs ships with its CHANGELOG entry (DOC-7.2).

## Code map

```
src/hydrolog/
├── catalog/      # Command/Option model, groups/<group>.py declarations, dispatch, envelope, documents
├── operations/   # one public function per catalog command (+ _outputs.py: plan/force/check)
├── cli/          # CLI generated from the catalog; render.py (human text), texts.py (PL/EN)
├── mcp/          # MCP server (extra [mcp]): tools, instructions, calls
├── agent_guide.py, _data/agents/   # generator and templates of AGENTS.md, llms.txt, block
├── exceptions.py, _errors.py       # HydrologError classes; registry generated from schemas/nogat
├── _settings.py                    # lang/log_level: option > env > nogat.toml > default
├── routing/      # reaches (lag, muskingum, cunge, cascade, level_pool); network.py (nodes, RoutingNetwork),
│                 # points.py (ControlPointNetwork), rainfall.py, runoff.py, document.py (hydrolog-network/1),
│                 # schematic.py, _layout.py, _svg.py (the metro-style map, hydrolog-network-schematic/1)
├── testing.py    # public builders of the files other projects read (DEV-10.6, ADR-0011, ADR-0012)
├── runoff/ time/ precipitation/ morphometry/ network/ statistics/ hydrometrics/ soil/
├── reports/ visualization/         # Markdown reports, plots (extra [viz])
tests/{unit,integration,contract,fixtures}   schemas/nogat/ (copies of the standard)
```

## Documentation map

| For | Read |
|---|---|
| Current state, next steps | [docs/PROGRESS.md](docs/PROGRESS.md) |
| Why it is the way it is | [docs/DECISIONS.md](docs/DECISIONS.md), [docs/PRD.md](docs/PRD.md), [docs/SCOPE.md](docs/SCOPE.md) |
| Formulas and methods | [docs/COMPUTATION_PATHS.md](docs/COMPUTATION_PATHS.md) |
| Using the library in code | [docs/USAGE.md](docs/USAGE.md) |
| Other tools' files | [docs/INTEGRATION.md](docs/INTEGRATION.md) |
| Plans and specs | [docs/plans/](docs/plans/) |
| Changes for users | [docs/CHANGELOG.md](docs/CHANGELOG.md) |

## Session workflow

Start (DEV-17.1): read this file and `docs/PROGRESS.md`, run `git status` and
`git log --oneline -10`, confirm the branch, list the open GitHub issues labelled
`request`. End (DEV-17.3): update `docs/PROGRESS.md` (Status, Next, Open questions) before
the last commit. Change only this repository (DEV-17.5); a need in another project is a
`request` issue in its repository.

## Cross-project context

Registry entry:
[ecosystem.yaml](https://github.com/Daldek/Nogat/blob/main/ecosystem.yaml) (Hydrolog).
Inputs come from Kartograf (soil rasters, `files[].path` of `--output-dir` downloads) and
IMGWTools (series CSV from `series export --output`); Hydrograf and Retman use Hydrolog.

## Deviations

- DEV-2.2, DEV-2.3: the text of `report generate` and the labels of `hydrolog.visualization`
  plots are Polish and inline in the code; only the CLI/catalog texts are translated.
- DEV-7.3: the tests have one relaxed mypy override (untyped test functions); `src/` is
  `strict`.
- DEV-19.7: a command that writes one file (`--output`) replaces it atomically through a
  temporary file beside the target, not through a `.hydrolog-incoming/` staging directory
  (ADR 0003); `route network` (`--output-dir`, many files) does use the staging directory
  (ADR-0010).
- AGI-4.4: `to_dict()` of a library result does not carry `schema`; the envelope adds it
  to `result` (ADR 0002).
- AGI-5.9: no MCP resources or prompts, tools only.
- DOC-4.2: the group `route` has one line in the command index of `AGENTS.md` instead of one
  per command, to keep the guide within 16 KiB (ADR-0009); `commands list` and `commands schema`
  still give every command.
