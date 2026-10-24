"""Tests for the generic terminal summary of results and errors."""

import pytest

from hydrolog.catalog import Command, Option
from hydrolog.cli import render
from hydrolog.cli.render import format_number, render_error, render_result

COMMAND = Command(
    name="demo run",
    operation_id="hydrolog_demo_run",
    summary="Summary.",
    summary_pl="Podsumowanie.",
    description="Description.",
    description_pl="Opis.",
    function="hydrolog.operations.demo_run",
    options=(
        Option("length_km", "number", "Length", "Długość", unit="km"),
        Option("values", "number_list", "Values", "Wartości", unit="mm"),
        Option("mode", "string", "Mode", "Tryb"),
    ),
    result_schema="hydrolog-demo-run/1",
    examples=({"length_km": 1.0},),
    example_results=({},),
)


def _render(
    result=None, *, inputs=None, notices=(), files=(), lang="pl", width=100, page=None
):
    """Render the envelope of ``demo run``; ``files`` go to ``result.files``."""
    if files:
        result = {**(result or {}), "files": list(files)}
    data = {"inputs": inputs or {}, "result": result, "notices": list(notices)}
    if page is not None:
        data["page"] = page
    return render_result(data, COMMAND, lang, width)


class TestFormatNumber:
    """Six significant digits, whole numbers without a fraction."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (3.0, "3"),
            (-0.0, "0"),
            (85.97330594494066, "85.9733"),
            (0.30000000000000004, "0.3"),
            (1234567.891, "1234568"),
            (1e15, "1000000000000000"),
            (0.0000123, "1.23e-05"),
            (float("inf"), "inf"),
            (float("-inf"), "-inf"),
            (float("nan"), "nan"),
        ],
    )
    def test_format(self, value, expected):
        assert format_number(value) == expected


class TestScalars:
    """Aligned ``key: value`` lines with units, in Polish and English."""

    def test_polish_summary_with_units(self):
        text = _render(
            {"tc_min": 85.97330594494066, "ok": True, "note": None},
            inputs={"length_km": 8.2, "mode": "fast"},
        )
        assert text == (
            "demo run: Podsumowanie.\n"
            "Wejście:\n"
            "  length_km: 8.2 km\n"
            "  mode:      fast\n"
            "Wynik:\n"
            "  tc_min: 85.9733\n"
            "  ok:     tak\n"
            "  note:   brak"
        )

    def test_english_summary(self):
        text = _render({"ok": False, "note": None}, inputs={"mode": "x"}, lang="en")
        assert text == (
            "demo run: Summary.\nInput:\n  mode: x\nResult:\n  ok:   no\n  note: n/a"
        )

    def test_unit_is_not_added_to_text_values(self):
        text = _render({}, inputs={"length_km": "n/a"})
        assert text.splitlines()[2] == "  length_km: n/a"

    def test_unit_follows_a_numeric_list(self):
        text = _render({}, inputs={"values": [1.5, 2, 3]})
        assert "  values: [1.5, 2, 3] mm" in text

    @pytest.mark.parametrize(
        ("result", "expected"),
        [
            (5, "Wynik: 5"),
            (2.5, "Wynik: 2.5"),
            ("ok", "Wynik: ok"),
            ([1, 2], "Wynik: [1, 2]"),
        ],
    )
    def test_scalar_and_short_list_results(self, result, expected):
        assert _render(result).splitlines()[-1] == expected

    def test_multiline_text_result_is_an_indented_block(self):
        text = _render("first\nsecond\n", inputs={"mode": "x"}, lang="en")
        assert text.splitlines()[3:] == ["Result:", "  first", "  second"]
        assert not text.endswith("\n")

    def test_empty_containers(self):
        text = _render({"a": {}, "b": []})
        assert "  a: {}" in text
        assert "  b: []" in text
        assert _render({}).endswith("Wynik: {}")
        assert _render([]).endswith("Wynik: []")


class TestNesting:
    """Nested objects are indented and bounded in depth."""

    def test_nested_objects_are_indented(self):
        text = _render({"outer": {"a": 1, "inner": {"b": [1, 2, 3]}}, "z": 2})
        assert text.splitlines()[2:] == [
            "  outer:",
            "    a: 1",
            "    inner:",
            "      b: [1, 2, 3]",
            "  z: 2",
        ]

    def test_objects_below_the_depth_limit_become_compact_json(self):
        # The result itself is level 1; the object at level MAX_DEPTH is compacted.
        deep = {"l1": {"l2": {"l3": {"l4": {"l5": 1}}}}}
        lines = _render(deep).splitlines()
        assert lines[2:] == [
            "  l1:",
            "    l2:",
            "      l3:",
            '        l4: {"l5":1}',
        ]


class TestLists:
    """Lists of scalars are summarized; records become tables or blocks."""

    def test_long_numeric_list_shows_head_last_count_and_range(self):
        text = _render({"series": list(range(1, 31))})
        assert text.endswith("series: [1, 2, 3, 4, 5, …, 30] (n=30, min=1, max=30)")

    def test_long_list_of_text_has_no_range(self):
        text = _render({"names": [f"n{i}" for i in range(12)]})
        assert text.endswith("names: [n0, n1, n2, n3, n4, …, n11] (n=12)")

    def test_long_text_items_are_listed_one_per_line(self):
        sections = [
            f"{number}. Section with a rather long title" for number in range(1, 8)
        ]
        text = _render({"sections": sections, "n": 7})
        assert text.splitlines()[2:6] == [
            "  sections:",
            "    - 1. Section with a rather long title",
            "    - 2. Section with a rather long title",
            "    - 3. Section with a rather long title",
        ]
        assert text.splitlines()[-1] == "  n: 7"

    def test_bullets_are_limited_with_a_note(self):
        items = [
            f"item {number} " + "x" * 30 for number in range(render.RECORD_BLOCKS + 5)
        ]
        lines = _render({"items": items}, lang="en").splitlines()
        assert lines[-1] == "    … more items: 5 (full data: --json)"
        assert (
            len([line for line in lines if line.startswith("    - ")])
            == render.RECORD_BLOCKS
        )

    def test_none_in_numbers_is_skipped_for_the_range(self):
        values = [None, 4.0, 9.0] + [5.0] * 8
        assert "(n=11, min=4, max=9)" in _render({"v": values})

    def test_records_become_a_table_with_right_aligned_numbers(self):
        text = _render([{"name": "a", "value": 1}, {"name": "bb", "value": 2.5}])
        assert text.splitlines()[1:] == [
            "Wynik (2):",
            "  name  value",
            "  ----  -----",
            "  a         1",
            "  bb      2.5",
        ]

    def test_short_nested_cells_stay_in_the_table(self):
        records = [{"name": "forest", "cn": {"A": 30, "B": 55}}]
        text = _render(records)
        assert '{"A":30,"B":55}' in text
        assert not any(line.startswith("  - ") for line in text.splitlines())

    def test_records_with_long_nested_cells_become_blocks(self):
        records = [
            {"name": "alpha", "info": {"k": list(range(30))}, "v": 1},
            {"name": "beta", "info": {"k": [1]}, "v": 2},
        ]
        assert _render(records).splitlines()[1:] == [
            "Wynik (2):",
            "  - name: alpha",
            "    info:",
            "      k: [0, 1, 2, 3, 4, …, 29] (n=30, min=0, max=29)",
            "    v:    1",
            "  - name: beta",
            "    info:",
            "      k: [1]",
            "    v:    2",
        ]

    def test_missing_keys_are_shown_as_empty_values(self):
        text = _render([{"a": 1}, {"a": 2, "b": "x"}])
        assert text.splitlines()[-2:] == ["  1  brak", "  2  x"]

    def test_table_rows_are_limited_with_a_note(self):
        text = _render([{"k": i} for i in range(render.RECORD_ROWS + 60)])
        lines = text.splitlines()
        assert lines[-1] == "  … dalsze elementy: 60 (pełne dane: --json)"
        assert lines[-2].strip() == str(render.RECORD_ROWS - 1)

    def test_a_few_rows_over_the_limit_are_shown_in_full(self):
        text = _render([{"k": i} for i in range(render.RECORD_ROWS + 2)])
        assert "dalsze" not in text
        assert text.splitlines()[-1].strip() == str(render.RECORD_ROWS + 1)

    def test_blocks_are_limited_with_a_note(self):
        records = [
            {"a": {"x": list(range(40))}} for _ in range(render.RECORD_BLOCKS + 5)
        ]
        text = _render(records, lang="en")
        assert text.splitlines()[-1] == "  … more items: 5 (full data: --json)"
        assert text.count("  - a:") == render.RECORD_BLOCKS


class TestOddShapes:
    """Values that fit no table or line."""

    def test_multiline_text_field_becomes_an_indented_block(self):
        text = _render({"note": "first\nsecond", "n": 1})
        assert text.splitlines()[2:] == [
            "  note:",
            "    first",
            "    second",
            "  n: 1",
        ]

    def test_empty_record_among_blocks(self):
        records = [{}, {"a": {"x": list(range(40))}}]
        lines = _render(records).splitlines()
        assert lines[2] == "  - {}"
        assert lines[3] == "  - a:"

    def test_records_without_fields_are_listed_not_tabulated(self):
        assert _render([{}, {}]).splitlines()[1:] == ["Wynik (2):", "  - {}", "  - {}"]

    def test_mixed_list_is_compact_json(self):
        assert _render({"m": [1, {"a": 1}]}).splitlines()[-1] == '  m: [1,{"a":1}]'
        assert _render([1, {"a": 1}]).splitlines()[-1] == 'Wynik: [1,{"a":1}]'

    def test_long_compact_json_is_shortened(self):
        text = _render({"m": [{"k": list(range(200))}, 1]}, width=60)
        line = text.splitlines()[-1]
        assert line.endswith("…") and len(line) <= 60


class TestTables:
    """Fitting tables to the terminal."""

    def test_long_text_is_wrapped_and_numbers_are_not_cut(self):
        records = [
            {
                "id": "a",
                "text": "alpha beta gamma delta epsilon zeta eta theta",
                "n": 1234567.891,
            },
            {"id": "bb", "text": "short", "n": 2},
        ]
        text = _render(records, width=40)
        assert text.splitlines()[1:] == [
            "Wynik (2):",
            "  id  text                             n",
            "  --  -------------------------  -------",
            "  a   alpha beta gamma delta     1234568",
            "      epsilon zeta eta theta",
            "  bb  short                            2",
        ]

    def test_wide_numeric_table_keeps_its_headers(self):
        text = _render([{"a_long_header_name": 1, "another_long_header": 2}], width=30)
        header = text.splitlines()[2]
        assert "a_long_header_name" in header and "another_long_header" in header

    def test_a_long_word_is_broken_instead_of_cut(self):
        path = "/very/long/path/" + "x" * 80 + ".csv"
        text = _render([{"p": path}], width=50)
        rows = [line.strip() for line in text.splitlines()[4:]]
        assert "".join(rows) == path
        assert all(len(line) <= 50 for line in text.splitlines()[1:])


class TestArrays:
    """Parallel numeric arrays become one table of the first rows."""

    def test_two_long_arrays_make_a_table_with_a_note(self):
        times = list(range(0, 100, 5))
        flows = [index / 4 for index in range(20)]
        text = _render({"t_min": times, "q": flows, "peak": 4.75})
        assert text.splitlines()[1:] == [
            "Wynik:",
            "  t_min     q",
            "  -----  ----",
            "      0     0",
            "      5  0.25",
            "     10   0.5",
            "     15  0.75",
            "     20     1",
            "     25  1.25",
            "     30   1.5",
            "     35  1.75",
            "     40     2",
            "     45  2.25",
            "     50   2.5",
            "     55  2.75",
            "  … dalsze elementy: 8 (pełne dane: --json)",
            "",
            "  peak: 4.75",
        ]

    def test_arrays_just_over_the_limit_are_shown_in_full(self):
        count = render.ARRAY_ROWS + 2
        text = _render({"t": list(range(count)), "q": list(range(count))})
        assert "dalsze" not in text
        assert text.splitlines()[-1].split() == [str(count - 1), str(count - 1)]

    def test_a_lone_long_array_is_summarized_in_a_line(self):
        text = _render({"t": list(range(40)), "q": list(range(41))})
        assert "  t: [0, 1, 2, 3, 4, …, 39] (n=40, min=0, max=39)" in text
        assert "  q: [0, 1, 2, 3, 4, …, 40] (n=41, min=0, max=40)" in text

    def test_short_arrays_stay_in_lines(self):
        text = _render({"t": [0, 5, 10], "q": [1, 2, 3]})
        assert text.splitlines()[-2:] == ["  t: [0, 5, 10]", "  q: [1, 2, 3]"]


class TestResultSchema:
    """The ``schema`` of a result and its ``files`` are sections, not fields."""

    def test_schema_of_the_result_is_not_listed_as_a_field(self):
        text = _render({"schema": "hydrolog-demo-run/1", "x": 1}, lang="en")
        assert text == "demo run: Summary.\nResult:\n  x: 1"

    def test_a_schema_key_further_down_is_an_ordinary_field(self):
        text = _render({"outer": {"schema": "plain text"}}, lang="en")
        assert text.splitlines()[-1] == "    schema: plain text"


class TestPlan:
    """The plan of ``--check`` lists each target with its action."""

    PLAN = {
        "schema": "hydrolog-plan/1",
        "targets": [
            {"option": "output", "path": "/tmp/a.md", "action": "write"},
            {
                "option": "output_b",
                "path": "/tmp/b.md",
                "action": "conflict",
                "reason": "output_exists",
            },
            {"option": "output_c", "path": "/tmp/c.md", "action": "replace"},
        ],
    }

    def test_english_plan_with_a_conflict(self):
        assert _render(self.PLAN, lang="en").splitlines() == [
            "demo run: Summary.",
            "Plan (--check): nothing was written.",
            "action    option    file       note",
            "--------  --------  ---------  ------------------------------------------",
            "write     output    /tmp/a.md",
            "conflict  output_b  /tmp/b.md  the file exists; add --force to replace it",
            "replace   output_c  /tmp/c.md",
            "Running without --check would fail with the error conflict (exit code 4).",
        ]

    def test_polish_plan_without_a_conflict_has_no_warning(self):
        plan = {**self.PLAN, "targets": [self.PLAN["targets"][0]]}
        lines = _render(plan).splitlines()
        assert lines[:3] == [
            "demo run: Podsumowanie.",
            "Plan (--check): nic nie zostało zapisane.",
            "działanie  opcja   plik       uwaga",
        ]
        assert lines[-1].startswith("zapis")

    def test_plan_without_targets(self):
        plan = {"schema": "hydrolog-plan/1", "targets": []}
        assert _render(plan, lang="en").splitlines()[1:] == [
            "Plan (--check): nothing was written.",
            "No files would be written.",
        ]


class TestCommandList:
    """``commands list`` is a table of names and summaries, then the page."""

    ENTRIES = [
        {"name": "tc kirpich", "operation_id": "hydrolog_tc_kirpich", "summary": "X"},
        {"name": "demo run", "operation_id": "hydrolog_demo_run", "summary": "Own"},
    ]

    def _document(self):
        return {"schema": "hydrolog-command-list/1", "commands": self.ENTRIES}

    def test_summaries_come_from_the_catalog_in_the_language(self):
        lines = _render(self._document(), lang="en").splitlines()
        assert lines[1].split() == ["command", "summary"]
        assert lines[3].startswith("tc kirpich  Compute time of concentration")
        assert lines[4] == "demo run    Own"

    def test_complete_listing_reports_the_total(self):
        page = {"total": 2, "truncated": False, "next_cursor": None}
        lines = _render(self._document(), lang="en", page=page).splitlines()
        assert lines[-1] == "Commands in total: 2."

    def test_truncated_listing_names_the_next_cursor(self):
        page = {"total": 40, "truncated": True, "next_cursor": "2"}
        lines = _render(self._document(), lang="en", page=page).splitlines()
        assert lines[-2:] == ["Showing 2 of 40.", "Next page: --cursor 2"]


class TestConfigShow:
    """``config show``: settings with their source, the file, credentials, store."""

    DOCUMENT = {
        "schema": "hydrolog-config/1",
        "settings": [
            {"key": "lang", "value": "pl", "source": "default"},
            {"key": "log_level", "value": "debug", "source": "file", "detail": "[x]"},
        ],
        "config_file": {"path": "/x/nogat.toml", "exists": True},
        "credentials": [{"name": "TOKEN", "present": False}],
        "store": None,
    }

    def test_english(self):
        assert _render(self.DOCUMENT, lang="en").splitlines()[1:] == [
            "setting    value  source",
            "---------  -----  -------------------",
            "lang       pl     default",
            "log_level  debug  settings file ([x])",
            "Settings file: /x/nogat.toml (exists)",
            "Credentials:",
            "  TOKEN: missing",
            "Data store: n/a",
        ]

    def test_polish_without_credentials_and_file(self):
        document = {
            **self.DOCUMENT,
            "credentials": [],
            "config_file": {"path": "/x/nogat.toml", "exists": False},
        }
        assert _render(document).splitlines()[-3:] == [
            "Plik ustawień: /x/nogat.toml (brak pliku)",
            "Dane uwierzytelniające: brak",
            "Magazyn danych: brak",
        ]


class TestGuide:
    """``commands guide`` prints the guide itself, or the file it wrote."""

    def test_guide_text_is_printed_as_it_is(self):
        document = {"schema": "hydrolog-guide/1", "text": "# Hydrolog\n\nbody\n"}
        assert _render(document) == "# Hydrolog\n\nbody"

    def test_written_guide_shows_the_title_and_the_file(self):
        record = {
            "path": "/tmp/llms.txt",
            "size_bytes": 10,
            "sha256": "ab" * 32,
            "status": "written",
        }
        document = {"schema": "hydrolog-guide/1", "files": [record]}
        assert _render(document, lang="en").splitlines() == [
            "demo run: Summary.",
            "Files:",
            "  /tmp/llms.txt  (written, 10 B, sha256 abababababab…)",
        ]


class TestNoticesAndFiles:
    """The sections after the result."""

    RECORD = {
        "path": "/tmp/a.tif",
        "size_bytes": 12,
        "sha256": "ab" * 32,
        "status": "written",
    }

    def test_notices_and_files(self):
        text = _render(
            {"x": 1},
            notices=[
                {"level": "warning", "code": "short_series", "message": "Only 3"},
                {"level": "info", "code": "note", "message": "FYI"},
            ],
            files=[
                self.RECORD,
                {**self.RECORD, "path": "/tmp/b.tif", "status": "replaced"},
            ],
        )
        assert text.splitlines()[-6:] == [
            "Uwagi:",
            "  [ostrzeżenie] short_series: Only 3",
            "  [informacja] note: FYI",
            "Pliki:",
            "  /tmp/a.tif  (zapisano, 12 B, sha256 abababababab…)",
            "  /tmp/b.tif  (zastąpiono, 12 B, sha256 abababababab…)",
        ]

    def test_files_are_listed_once_not_among_the_result_fields(self):
        text = _render({"x": 1}, files=[self.RECORD], lang="en")
        assert text.count("/tmp/a.tif") == 1
        assert text.splitlines()[:3] == ["demo run: Summary.", "Result:", "  x: 1"]

    def test_english_labels(self):
        text = _render(
            {},
            notices=[{"level": "warning", "code": "c", "message": "t"}],
            lang="en",
        )
        assert "Notices:\n  [warning] c: t" in text

    def test_no_empty_sections(self):
        text = _render({"x": 1})
        assert "Uwagi" not in text and "Pliki" not in text and "Wejście" not in text


class TestErrors:
    """Readable error text: title, message, hint."""

    def test_polish_error_with_hint(self):
        document = {
            "code": "validation_error",
            "title": "Nieprawidłowe dane wejściowe",
            "message": "Line 1\nLine 2",
            "hint": "Do this.",
        }
        assert render_error(document) == (
            "Błąd (validation_error): Nieprawidłowe dane wejściowe\n"
            "  Line 1\n"
            "  Line 2\n"
            "Podpowiedź: Do this."
        )

    def test_english_error_without_message_and_hint(self):
        document = {
            "code": "not_found",
            "title": "Not found",
            "message": "",
            "hint": None,
        }
        assert render_error(document, "en") == "Error (not_found): Not found"


def _random_json(rng, depth=0):
    """A random JSON-native value, favouring the shapes that results have."""
    kinds = ["none", "bool", "int", "float", "text"]
    if depth < 4:
        kinds += ["numbers", "texts", "records", "mixed", "object"]
    kind = rng.choice(kinds)
    if kind == "none":
        return None
    if kind == "bool":
        return rng.random() < 0.5
    if kind == "int":
        return rng.randint(-(10**12), 10**12)
    if kind == "float":
        return rng.choice([0.0, -0.0, 1e-300, 1e300, 123456789.123, 2.5, -7.25e-9])
    if kind == "text":
        return rng.choice(
            ["", "a", "x" * 120, "one\ntwo", "Młynówka", "/p a/" + "y" * 90]
        )
    length = rng.choice([0, 1, 2, 7, 8, 9, 14, 15, 40, 230])
    if kind == "numbers":
        return [
            rng.choice([None, rng.random() * 10, rng.randint(0, 99)])
            for _ in range(length)
        ]
    if kind == "texts":
        return [rng.choice(["a", "bb" * 20, "c" * 70]) for _ in range(length)]
    if kind == "records":
        keys = ["a", "b", "c", "dd", "e"]
        return [
            {
                k: _random_json(rng, depth + 2)
                for k in rng.sample(keys, rng.randint(0, 4))
            }
            for _ in range(min(length, 30))
        ]
    if kind == "mixed":
        return [_random_json(rng, depth + 1) for _ in range(min(length, 8))]
    names = ["a", "b", "key_long_name", "schema", "t", "q"]
    obj = {
        rng.choice(names): _random_json(rng, depth + 1)
        for _ in range(rng.randint(0, 6))
    }
    if rng.random() < 0.2:  # a time axis and its values
        size = rng.choice([9, 15, 30])
        obj["t"] = [rng.random() for _ in range(size)]
        obj["q"] = [rng.random() for _ in range(size)]
    return obj


class TestNeverFails:
    """Whatever JSON a command returns, the summary is produced."""

    @pytest.mark.parametrize("width", [20, 80, 200])
    def test_random_results_render_to_text(self, width):
        import random

        rng = random.Random(width)
        for _ in range(200):
            data = {
                "inputs": {"v": _random_json(rng)},
                "result": _random_json(rng),
                "notices": [],
            }
            for lang in ("pl", "en"):
                assert isinstance(render_result(data, COMMAND, lang, width), str)
