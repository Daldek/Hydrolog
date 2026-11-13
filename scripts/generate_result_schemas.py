"""Generate the JSON Schemas of the domain documents (AGI-4.1).

Every command of the catalog declares the id of its result document
(``Command.result_schema``, for example ``hydrolog-tc-kirpich/1``). This script runs
the examples of each command (writing commands into a temporary directory), infers a
schema from the documents they produce and writes
``src/hydrolog/schemas/<kind>-<n>.schema.json``. The schemas are deliberately loose:
the top-level properties with their types, the properties that every example has as
``required``, and nothing about nested keys, so a new optional field keeps the version
(AGI-4.1). A field added to a document after its first version is never ``required``,
whatever the examples hold: the documents of earlier releases lack it and keep the
version, so they must still validate. :data:`_ADDED_FIELDS` lists those fields by
document id; a new field of an existing document goes there. The plan document
``hydrolog-plan/1`` and the command list are written by hand below, and so are the
network ``hydrolog-network/1`` that ``route network`` reads (its fields come from the
options of the catalog), the schematic of a network ``hydrolog-network-schematic/1``,
which ``route network`` returns in its result and draws as SVG and ``route schematic``
returns as its result, ``hydrolog-gui-serve/1``, whose only example is a plan (the
server blocks until it is stopped), and ``hydrolog-precip-pmaxtp/1``, whose example
fetches from IMGW-PIB (the script runs offline); ``hydrolog-commands/1`` is the Nogat
``commands-1`` schema (``schemas/nogat/``).

Usage::

    uv run scripts/generate_result_schemas.py            # write the schemas
    uv run scripts/generate_result_schemas.py --check    # fail when they are stale
"""

import argparse
import dataclasses
import json
import os
import sys
import tempfile
import typing
from pathlib import Path
from typing import Any

from hydrolog.catalog import data_commands, run_command
from hydrolog.catalog.groups.hydrograph import GENERATE_OPTIONS
from hydrolog.catalog.groups.precip import HIETOGRAM_OPTIONS
from hydrolog.catalog.groups.route import (
    DISCHARGE_M3S,
    EXTEND_MIN,
    INITIAL_OUTFLOW_M3S,
    MODEL_METHODS,
    TIMES_MIN,
    VALUE_COLUMN,
    model_options,
)
from hydrolog.catalog.spec import Command, Option
from hydrolog.morphometry.watershed_params import WatershedParameters
from hydrolog.routing import HIETOGRAMS, RAINFALL_KINDS, RUNOFF_MODELS
from hydrolog.routing._layout import LABEL_SIDES
from hydrolog.routing.network import MAX_DESCRIPTION_CHARS, MAX_ID_CHARS, MAX_POSITION
from hydrolog.routing.schematic import SCHEMA as SCHEMATIC_SCHEMA

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src" / "hydrolog" / "schemas"
BASE = "https://github.com/Daldek/Hydrolog/blob/main/src/hydrolog/schemas"
NOGAT_COMMANDS = "hydrolog-commands/1"
_RESERVED_ID = (
    "^([Cc][Oo][Nn]|[Pp][Rr][Nn]|[Aa][Uu][Xx]|[Nn][Uu][Ll]"
    "|([Cc][Oo][Mm]|[Ll][Pp][Tt])[1-9\u00b9\u00b2\u00b3])(\\..*)?$"
)
"""Device names of Windows as an ECMA 262 pattern (no inline flags there)."""
_CONTROL = r"[\u0000-\u0009\u000b-\u001f\u007f-\u009f]"
"""Control characters but the line feed, as an ECMA 262 class (escapes, not the
characters themselves)."""

_TYPE_ORDER = ["null", "boolean", "integer", "number", "string", "array", "object"]

_ADDED_FIELDS: dict[str, tuple[str, ...]] = {
    "hydrolog-hydrograph-generate/1": (
        "uh_times_min",
        "uh_discharge_m3s_per_mm",
        "nash_estimation",
    ),
    "hydrolog-stats-flood-frequency/1": ("fit_method", "source"),
    "hydrolog-stats-low-flow/1": ("source",),
    "hydrolog-stats-homogeneity/1": ("source", "hydrological_years"),
    "hydrolog-stats-characteristic/1": (
        "labels",
        "first_degree_labels",
        "source",
        "first_year",
        "last_year",
        "winter",
        "summer",
        "years",
        "incomplete_years",
    ),
    "hydrolog-stats-low-flow-sequences/1": (
        "threshold_method",
        "exceedance_percent",
        "parameter",
        "first_year",
        "last_year",
        "period_years",
        "n_missing_days",
        "total_deficit_volume_m3",
        "years",
    ),
    "hydrolog-hydrometrics-rating-curve/1": (
        "first_year",
        "last_year",
        "periods",
        "reference_level",
        "reference_discharge_m3s",
    ),
    "hydrolog-stats-mann-kendall/1": (
        "sen_slope",
        "sen_intercept",
        "sen_slope_lower",
        "sen_slope_upper",
    ),
}
"""Fields added to a document after its first version, by id: never ``required``."""


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _merge_types(types: set[str]) -> str | list[str]:
    if "integer" in types and "number" in types:
        types.discard("integer")
    ordered = [name for name in _TYPE_ORDER if name in types]
    return ordered[0] if len(ordered) == 1 else ordered


def infer(schema_id: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the loose schema of ``documents``, all results of one command."""
    types: dict[str, set[str]] = {}
    for document in documents:
        for key, value in document.items():
            types.setdefault(key, set()).add(_json_type(value))
    added = _ADDED_FIELDS.get(schema_id, ())
    required = [
        key
        for key in types
        if key not in added and all(key in document for document in documents)
    ]
    properties: dict[str, Any] = {}
    for key, found in types.items():
        if key == "schema":
            properties[key] = {"const": schema_id}
        elif found == {"null"}:
            # Only null in the examples (an optional field they leave out): the type
            # is unknown, so the schema must not forbid a value (AGI-4.1).
            properties[key] = {}
        else:
            properties[key] = {"type": _merge_types(found)}
    stem = schema_id.replace("/", "-")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/{stem}.schema.json",
        "title": schema_id,
        "description": (
            "Domain document of the result envelope hydrolog-result/1 (generated by "
            "scripts/generate_result_schemas.py). Unknown fields are allowed: adding "
            "optional fields keeps the version (AGI-4.1)."
        ),
        "type": "object",
        "required": required,
        "properties": properties,
    }


def _example_options(command: Command, number: int, scratch: Path) -> dict[str, Any]:
    options = dict(command.examples[number])
    for option in command.options:
        if option.path_role == "output" and option.name in options:
            name = f"{command.name.replace(' ', '_')}-{number}-"
            options[option.name] = str(
                scratch / (name + Path(options[option.name]).name)
            )
    return options


def _documents(command: Command, scratch: Path) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for number in range(len(command.examples)):
        options = _example_options(command, number, scratch)
        if options.get("check"):
            continue
        document = run_command(command, options).to_dict()["result"]
        document.pop("files", None)
        documents.append(document)
    return documents


def _node_fields(options: tuple[Option, ...]) -> dict[str, Any]:
    """Return the options of the catalog as the properties of a node of a network."""
    properties: dict[str, Any] = {}
    for option in options:
        schema = option.json_schema("en")
        if option.type == "path":
            # the path rules of a server see the options of a call, not the files that
            # a document names, so a file of the document stays beside the document
            schema = {
                "type": "string",
                "minLength": 1,
                "description": (
                    "File relative to the directory of the network file, and inside it."
                ),
            }
        properties[option.name] = schema
    return properties


_RUNOFF_FIELDS = (
    "tc_min",
    "tc_method",
    "ia_coefficient",
    "amc",
    "uh_model",
    "nash_n",
    "nash_k_min",
    "nash_estimation",
    "clark_r_min",
    "clark_r_tc_ratio",
    "snyder_length_km",
    "snyder_centroid_length_km",
    "snyder_ct",
    "snyder_cp",
)
"""The options of ``hydrograph generate`` that the ``curve-number`` runoff takes."""


def _watershed_schema() -> dict[str, Any]:
    """Return the schema of a ``watershed``: the fields of ``WatershedParameters``."""
    hints = typing.get_type_hints(WatershedParameters)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for item in dataclasses.fields(WatershedParameters):
        kinds = [
            kind for kind in typing.get_args(hints[item.name]) if kind is not type(None)
        ]
        text = (kinds[0] if kinds else hints[item.name]) is str
        properties[item.name] = {"type": "string" if text else "number"}
        if item.default is dataclasses.MISSING:
            required.append(item.name)
    for name in ("area_km2", "perimeter_km", "length_km"):
        properties[name]["exclusiveMinimum"] = 0
    properties["cn"].update(minimum=0, maximum=100)
    return {
        "title": "watershed",
        "description": (
            "The area of a subcatchment: the fields of `WatershedParameters`, "
            "as in `hydrograph generate`. The `curve-number` runoff needs `cn`, "
            "unless it is given `tc_min` the fields of its `tc_method`, and with "
            "`nash_estimation` the fields of the estimation."
        ),
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _runoff_schema() -> dict[str, Any]:
    """Return the schema of a ``runoff``: one variant per model of the registry."""
    assert RUNOFF_MODELS.names == ("curve-number",), "a runoff model has no schema"
    chosen = {option.name: option for option in GENERATE_OPTIONS}
    variant = {
        "title": "runoff curve-number",
        "description": (
            "The SCS Curve Number loss and a unit hydrograph, with the options of "
            "`hydrograph generate`."
        ),
        "type": "object",
        "required": ["model"],
        "properties": {
            "model": {"const": "curve-number"},
            **_node_fields(tuple(chosen[name] for name in _RUNOFF_FIELDS)),
        },
        "additionalProperties": False,
    }
    return {"oneOf": [variant]}


def _rainfall_schema() -> dict[str, Any]:
    """Return the schema of a ``rainfall``: one variant per kind of the registry."""
    assert RAINFALL_KINDS.names == ("design", "series"), "a rainfall has no schema"
    shape = {option.name: option for option in HIETOGRAM_OPTIONS}
    design_fields = _node_fields(
        tuple(shape[name] for name in ("hietogram_type", "total_mm", "duration_min"))
        + tuple(shape[name] for name in ("alpha", "beta", "peak_position"))
    )
    design_fields["hietogram_type"] = {
        **design_fields["hietogram_type"],
        "enum": list(HIETOGRAMS.names),
    }
    design = {
        "title": "design storm",
        "description": "A depth over a duration, in the shape of a hyetograph.",
        "type": "object",
        "required": ["kind", "hietogram_type", "total_mm", "duration_min"],
        "properties": {"kind": {"const": "design"}, **design_fields},
        "additionalProperties": False,
    }
    series = {
        "title": "rainfall series",
        "description": (
            "The depth of every time step. It is not resampled: the network takes its "
            "time step."
        ),
        "type": "object",
        "required": ["kind", "depths_mm", "timestep_min"],
        "properties": {
            "kind": {"const": "series"},
            "depths_mm": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "number", "minimum": 0},
                "description": "Depth of each step [mm], not negative.",
            },
            "timestep_min": {
                "type": "number",
                "exclusiveMinimum": 0,
                "description": "Time step of the series [min].",
            },
        },
        "additionalProperties": False,
    }
    return {"oneOf": [design, series]}


def _network_document(schema_id: str) -> dict[str, Any]:
    """Return the schema of the network document (ADR-0010): one variant per node type.

    A reach has a variant per method, with the options of ``route <method>``.
    """
    run = _node_fields((INITIAL_OUTFLOW_M3S, EXTEND_MIN))
    sources = _node_fields((TIMES_MIN, DISCHARGE_M3S, VALUE_COLUMN))
    sources[TIMES_MIN.name]["description"] = (
        "Times of the ordinates [min], strictly increasing at a regular step, the same "
        "step and first time for every subcatchment; with `discharge_m3s`."
    )
    sources[DISCHARGE_M3S.name]["description"] = (
        "Discharge at each time [m3/s], not negative; as many values as `times_min`."
    )
    sources[VALUE_COLUMN.name]["description"] = (
        "Column of `inflows_file` with the discharges [m3/s] of the subcatchment; "
        "default the `id`. Not with inline discharges."
    )
    identifier = {"$ref": "#/$defs/id"}

    def upstream(low: int, high: int | None) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "array",
            "items": identifier,
            "uniqueItems": True,
            "minItems": low,
            "description": "The ids of the nodes that flow into this one.",
        }
        if high is not None:
            schema["maxItems"] = high
        return schema

    def variant(
        title: str, kind: str, properties: dict[str, Any], required: list[str]
    ) -> dict[str, Any]:
        return {
            "title": title,
            "type": "object",
            "required": ["id", "type", *required],
            "properties": {
                "id": identifier,
                "type": {"const": kind},
                **properties,
                "description": {"$ref": "#/$defs/description"},
                "position": {"$ref": "#/$defs/position"},
            },
            "additionalProperties": False,
        }

    given = variant(
        "subcatchment with discharges",
        "subcatchment",
        {"from": upstream(0, 0), **sources},
        [],
    )
    given["dependentRequired"] = {
        TIMES_MIN.name: [DISCHARGE_M3S.name],
        DISCHARGE_M3S.name: [TIMES_MIN.name],
    }
    given["not"] = {"required": [VALUE_COLUMN.name, TIMES_MIN.name]}
    made = variant(
        "subcatchment from rainfall",
        "subcatchment",
        {
            "from": upstream(0, 0),
            "watershed": {"$ref": "#/$defs/watershed"},
            "runoff": {"$ref": "#/$defs/runoff"},
            "rainfall": {"$ref": "#/$defs/rainfall"},
        },
        ["watershed", "runoff"],
    )
    variants = [given, made]
    for method in MODEL_METHODS:
        options = model_options(method)
        required = ["from", "method", *(o.name for o in options if o.required)]
        properties = {
            "from": upstream(1, 1),
            "method": {"const": method},
            **run,
            **_node_fields(options),
        }
        variants.append(variant(f"reach by {method}", "reach", properties, required))
    variants.append(
        variant(
            "reservoir",
            "reservoir",
            {
                "from": upstream(1, 1),
                **run,
                **_node_fields(model_options("level-pool")),
            },
            ["from"],
        )
    )
    variants.append(
        variant("junction", "junction", {"from": upstream(1, None)}, ["from"])
    )
    variants.append(variant("outlet", "outlet", {"from": upstream(1, 1)}, ["from"]))
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/hydrolog-network-1.schema.json",
        "title": schema_id,
        "description": (
            "River network read by `route network` (ADR-0010, ADR-0012): "
            "subcatchments (with their discharges, or making them from a watershed, a "
            "runoff model and a rainfall), reaches and reservoirs, junctions and one "
            "outlet, linked by `from`. A reach has a `method` and the options of "
            "`route <method>`. `schema` is required. A `rainfall` at the top is the "
            "rain of the subcatchments that have none; `timestep_min` fixes the time "
            "step of the network. Every node may have a `description` and a "
            "`position` in the grid of the schematic, and the network a `description` "
            "(ADR-0023); they change no calculation. A network of data of IMGW-PIB or "
            "ČHMÚ (a PMAXTP depth) may carry `attribution` and `terms_notice`, the "
            "lines their terms require (ADR-0028), which `route network` carries into "
            "its result and files."
        ),
        "type": "object",
        "required": ["schema", "nodes"],
        "properties": {
            "schema": {"const": schema_id},
            "name": {"type": "string", "minLength": 1},
            "description": {"$ref": "#/$defs/description"},
            "timestep_min": {
                "type": "number",
                "exclusiveMinimum": 0,
                "description": (
                    "Time step of the network [min]; default that of the sources, "
                    "else 5."
                ),
            },
            "rainfall": {"$ref": "#/$defs/rainfall"},
            "attribution": {
                "$ref": "#/$defs/lines",
                "description": (
                    "The attribution lines of the data providers, verbatim (Nogat "
                    "DEV-20.6)."
                ),
            },
            "terms_notice": {
                "$ref": "#/$defs/lines",
                "description": (
                    "The notice of IMGW-PIB's terms of use and the addresses of the "
                    "terms, verbatim (Nogat DEV-20.7)."
                ),
            },
            "nodes": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/node"},
            },
        },
        "additionalProperties": False,
        "$defs": {
            "lines": {
                "type": "array",
                "items": {"type": "string", "pattern": r"\S"},
            },
            "id": {
                "type": "string",
                "pattern": r"^\w[\w.-]*$",
                "not": {"pattern": _RESERVED_ID},
                "maxLength": MAX_ID_CHARS,
                "description": (
                    "Names the node and its file `<id>.csv`: letters, digits, `_`, `.` "
                    "and `-`, not starting with `.` or `-` and not ending with `.`, "
                    "not a device name of Windows (`con`, `prn`, `aux`, `nul`, `com1` "
                    "to `com9`, `lpt1` to `lpt9`, any case, any extension); unique "
                    "without regard to case."
                ),
            },
            "description": {
                "type": "string",
                "minLength": 1,
                "maxLength": MAX_DESCRIPTION_CHARS,
                "pattern": r"\S",
                "not": {"pattern": _CONTROL},
                "description": (
                    "Plain text for people, never read as HTML or Markdown: not "
                    f"blank, at most {MAX_DESCRIPTION_CHARS} characters, lines broken "
                    "by a line feed and no other control character."
                ),
            },
            "position": {
                "type": "object",
                "required": ["x", "y"],
                "properties": {
                    axis: {
                        "type": "integer",
                        "minimum": -MAX_POSITION,
                        "maximum": MAX_POSITION,
                    }
                    for axis in ("x", "y")
                },
                "additionalProperties": False,
                "description": (
                    "The cell of the node in the grid of the schematic (ADR-0013): `x` "
                    "grows downstream, `y` sideways. A network whose every node has a "
                    "cell of its own is drawn where its nodes are (ADR-0023)."
                ),
            },
            "node": {"oneOf": variants},
            "watershed": _watershed_schema(),
            "runoff": _runoff_schema(),
            "rainfall": _rainfall_schema(),
        },
    }


def _schematic_document(schema_id: str) -> dict[str, Any]:
    """Return the schema of the schematic of a network (ADR-0013, ADR-0025).

    Hydrolog writes the document and whoever draws it reads it, so the schema is as
    loose as the schemas of the results: an unknown field is allowed and a new optional
    one keeps the version (AGI-4.1).
    """
    identifier = {"$ref": "#/$defs/id"}
    count = {"$ref": "#/$defs/count"}
    notice = {
        "type": "object",
        "required": ["level", "code", "message"],
        "properties": {
            "level": {"enum": ["info", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
        },
    }
    parameter = {
        "type": "object",
        "required": ["name", "value", "unit", "source"],
        "properties": {
            "name": {"type": "string"},
            "value": {"type": ["number", "string", "boolean"]},
            "unit": {"type": ["string", "null"]},
            "source": {"enum": ["given", "computed", "default"]},
        },
    }
    values = ["peak_m3s", "time_to_peak_min", "volume_m3", "notices"]
    node = {
        "type": "object",
        "required": ["id", "type", "x", "y", "line", "label", "parameters"],
        "properties": {
            "id": identifier,
            "type": {"type": "string", "minLength": 1},
            "x": count,
            "y": count,
            "line": count,
            "label": {
                "type": "object",
                "required": ["text", "side"],
                "properties": {
                    "text": {"type": "string", "minLength": 1},
                    "side": {"enum": list(LABEL_SIDES)},
                },
            },
            "description": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "The description of the node: plain text for people, shown as "
                    "text and never as markup (ADR-0023)."
                ),
            },
            "parameters": {"type": "array", "items": parameter},
            "peak_m3s": {"type": "number", "minimum": 0},
            "time_to_peak_min": {"type": "number"},
            "volume_m3": {"type": "number", "minimum": 0},
            "notices": {"type": "array", "items": notice},
        },
        "dependentRequired": {
            name: [o for o in values if o != name] for name in values
        },
    }
    line = {
        "type": "object",
        "required": ["index", "role", "nodes"],
        "properties": {
            "index": count,
            "role": {"enum": ["main", "tributary"]},
            "nodes": {"type": "array", "minItems": 1, "items": identifier},
            "joins": identifier,
        },
        "if": {"properties": {"role": {"const": "tributary"}}},
        "then": {"required": ["joins"]},
    }
    edge = {
        "type": "object",
        "required": ["from", "to", "line", "points"],
        "properties": {
            "from": identifier,
            "to": identifier,
            "line": count,
            "points": {
                "type": "array",
                "minItems": 2,
                "items": {"$ref": "#/$defs/point"},
            },
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/hydrolog-network-schematic-1.schema.json",
        "title": schema_id,
        "description": (
            "Schematic of a routing network in the style of a metro map (ADR-0013): "
            "the nodes on an integer grid (`x` grows downstream, to the right, `y` "
            "grows downwards), the lines of the map, the polylines of the edges (every "
            "segment "
            "at 0, 45 or 90 degrees), the place of every label and, per node, its "
            "description, the parameters of its calculation and, with a result, its "
            "peak, time to peak, volume and notices. The nodes are at their given "
            "positions (`layout` `given`, rule D, ADR-0023; the edges may cross) or "
            "laid out (`computed`). Written by `RoutingNetwork.schematic()` and by "
            "`route network` with `schematic`, and for the structure of a draft alone "
            "by `structure_schematic()` and `route schematic` with `structure_only` "
            "(ADR-0025); unknown fields are allowed (AGI-4.1)."
        ),
        "type": "object",
        "required": [
            "schema",
            "outlet",
            "has_result",
            "grid",
            "lines",
            "nodes",
            "edges",
        ],
        "properties": {
            "schema": {"const": schema_id},
            "name": {"type": "string", "minLength": 1},
            "outlet": identifier,
            "timestep_min": {
                "type": "number",
                "exclusiveMinimum": 0,
                "description": (
                    "The time step of the network [min]: always in the schematic of a "
                    "network; in that of a structure only when its document gives it "
                    "(ADR-0025)."
                ),
            },
            "has_result": {"type": "boolean"},
            "layout": {
                "enum": ["given", "computed"],
                "description": (
                    "`given`: the nodes are at the positions of the network document "
                    "and the edges follow rule D (ADR-0023); `computed`: the layout of "
                    "ADR-0013. A document without it is computed."
                ),
            },
            "structure_only": {
                "type": "boolean",
                "description": (
                    "`true`: the schematic of the structure of a document alone (its "
                    "ids, types and links, ADR-0025): the layout is computed and the "
                    "nodes have no parameters. Absent in the schematic of a network."
                ),
            },
            "grid": {
                "type": "object",
                "required": ["width", "height"],
                "properties": {"width": count, "height": count},
                "description": "The extent of the nodes in grid units.",
            },
            "lines": {"type": "array", "minItems": 1, "items": line},
            "nodes": {"type": "array", "minItems": 1, "items": node},
            "edges": {"type": "array", "items": edge},
        },
        "if": {
            "properties": {"structure_only": {"const": True}},
            "required": ["structure_only"],
        },
        "else": {"required": ["timestep_min"]},
        "$defs": {
            "id": {"type": "string", "minLength": 1},
            "count": {"type": "integer", "minimum": 0},
            "point": {
                "type": "array",
                "prefixItems": [count, count],
                "items": False,
                "minItems": 2,
                "description": "A point of the grid: `[x, y]`.",
            },
        },
    }


def _series_document(schema_id: str) -> dict[str, Any]:
    """Return the schema of a station's series handed to the statistics (ADR-0020)."""
    values = {
        "description": (
            "The values in the order of `dates` or `years`, the same length; `null` "
            "for a missing value."
        ),
        "type": "array",
        "minItems": 1,
        "items": {"type": ["number", "null"]},
    }
    common = {
        "schema": {"const": schema_id},
        "name": {
            "description": "What the series is, for people (the station and variable).",
            "type": "string",
            "minLength": 1,
        },
        "variable": {
            "description": "The variable as its provider names it (`Q`, `H`).",
            "type": "string",
            "pattern": "^[A-Za-z][A-Za-z0-9_]*$",
        },
        "unit": {"description": "Its unit (`m3/s`, `cm`).", "type": "string"},
        "values": values,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/hydrolog-series-1.schema.json",
        "title": schema_id,
        "description": (
            "A series of one variable handed to the statistics (ADR-0020), the payload "
            "of a `nogat-handoff/1` from Archiwista: the daily values of a station "
            "(`step` `day`, with `dates`), whose annual extremes the statistics find, "
            "or an annual extreme of each year (`step` `year`, with `years`, "
            "`statistic` and `year_type`). Unknown fields are refused."
        ),
        "oneOf": [
            {
                "title": "daily values",
                "type": "object",
                "required": [
                    "schema",
                    "name",
                    "variable",
                    "unit",
                    "step",
                    "dates",
                    "values",
                ],
                "properties": {
                    **common,
                    "step": {"const": "day"},
                    "dates": {
                        "description": "The days, ISO 8601 (`2024-03-02`), increasing.",
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "string",
                            "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                        },
                    },
                },
                "additionalProperties": False,
            },
            {
                "title": "annual extremes",
                "type": "object",
                "required": [
                    "schema",
                    "name",
                    "variable",
                    "unit",
                    "step",
                    "statistic",
                    "year_type",
                    "years",
                    "values",
                ],
                "properties": {
                    **common,
                    "step": {"const": "year"},
                    "statistic": {
                        "description": "Which extreme of the year: `max` or `min`.",
                        "enum": ["max", "min"],
                    },
                    "year_type": {
                        "description": (
                            "How the years are numbered: `hydrological` (1 Nov to "
                            "31 Oct, named after the year it ends in) or `calendar`."
                        ),
                        "enum": ["hydrological", "calendar"],
                    },
                    "years": {
                        "description": "The years, increasing.",
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "integer"},
                    },
                },
                "additionalProperties": False,
            },
        ],
    }


def _hand_written() -> dict[str, dict[str, Any]]:
    plan_id = "hydrolog-plan/1"
    list_id = "hydrolog-command-list/1"
    network_id = "hydrolog-network/1"
    series_id = "hydrolog-series/1"
    schematic_id = SCHEMATIC_SCHEMA
    serve_id = "hydrolog-gui-serve/1"
    pmaxtp_id = "hydrolog-precip-pmaxtp/1"
    return {
        network_id: _network_document(network_id),
        series_id: _series_document(series_id),
        schematic_id: _schematic_document(schematic_id),
        serve_id: {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{BASE}/hydrolog-gui-serve-1.schema.json",
            "title": serve_id,
            "description": (
                "Where and when `gui serve` served once it has stopped: the address of "
                "the page and the times it started and stopped (ISO 8601, UTC; "
                "ADR-0014)."
            ),
            "type": "object",
            "required": ["schema", "url", "started_at", "stopped_at"],
            "properties": {
                "schema": {"const": serve_id},
                "url": {"type": "string"},
                "started_at": {"type": "string"},
                "stopped_at": {"type": "string"},
            },
        },
        pmaxtp_id: {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{BASE}/hydrolog-precip-pmaxtp-1.schema.json",
            "title": pmaxtp_id,
            "description": (
                "The PMAXTP depth of IMGW-PIB that `precip pmaxtp` fetches through "
                "Obserwator for a point, a duration and a probability, with the "
                "source line the terms of PMAXTP prescribe (ADR-0018, ADR-0028); the "
                "envelope's `attribution` and `terms_notice` have every line. Unknown "
                "fields are allowed: adding optional fields keeps the version "
                "(AGI-4.1)."
            ),
            "type": "object",
            "required": [
                "schema",
                "depth_mm",
                "latitude",
                "longitude",
                "method",
                "duration_min",
                "probability_percent",
                "attribution",
            ],
            "properties": {
                "schema": {"const": pmaxtp_id},
                "depth_mm": {"type": "number"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "method": {"type": "string"},
                "duration_min": {"type": "number"},
                "probability_percent": {"type": "number"},
                "attribution": {"type": "string"},
            },
        },
        plan_id: {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{BASE}/hydrolog-plan-1.schema.json",
            "title": plan_id,
            "description": (
                "Plan of a `check` run: each output file with its action (DEV-19.10). "
                "The plan of `gui serve` has no targets and gives the address it would "
                "serve on (`url`) and whether its port is free (`port_free`)."
            ),
            "type": "object",
            "required": ["schema", "targets"],
            "properties": {
                "schema": {"const": plan_id},
                "url": {"type": "string"},
                "port_free": {"type": "boolean"},
                "targets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["option", "path", "action"],
                        "properties": {
                            "option": {"type": "string"},
                            "path": {"type": "string"},
                            "action": {"enum": ["write", "replace", "conflict"]},
                            "reason": {
                                "enum": [
                                    "output_exists",
                                    "duplicate_output_name",
                                    "output_in_store",
                                ]
                            },
                        },
                    },
                },
            },
        },
        list_id: {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{BASE}/hydrolog-command-list-1.schema.json",
            "title": list_id,
            "description": "Summary of the catalog commands (`commands list`).",
            "type": "object",
            "required": ["schema", "tool", "version", "commands"],
            "properties": {
                "schema": {"const": list_id},
                "tool": {"const": "hydrolog"},
                "version": {"type": "string"},
                "commands": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "name",
                            "operation_id",
                            "summary",
                            "families",
                            "read_only",
                        ],
                        "properties": {
                            "name": {"type": "string"},
                            "operation_id": {"type": "string"},
                            "summary": {"type": "string"},
                            "families": {"type": "array", "items": {"type": "string"}},
                            "read_only": {"type": "boolean"},
                        },
                    },
                },
            },
        },
    }


def build() -> dict[str, dict[str, Any]]:
    """Return every schema by document id."""
    schemas = _hand_written()
    seen: dict[str, Command] = {}
    with tempfile.TemporaryDirectory() as scratch:
        previous = Path.cwd()
        os.chdir(ROOT)  # the examples use paths relative to the repository root
        try:
            for command in data_commands():
                schema_id = command.result_schema
                if schema_id in schemas or schema_id == NOGAT_COMMANDS:
                    continue
                if schema_id in seen:
                    raise SystemExit(f"{schema_id} is declared by two commands")
                seen[schema_id] = command
                schemas[schema_id] = infer(
                    schema_id, _documents(command, Path(scratch))
                )
        finally:
            os.chdir(previous)
    return schemas


def _text(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the schemas, or with ``--check`` fail when they are stale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="do not write")
    args = parser.parse_args(argv)
    schemas = build()
    expected = {
        TARGET / f"{schema_id.replace('/', '-')}.schema.json": _text(schema)
        for schema_id, schema in schemas.items()
    }
    if args.check:
        stale = [
            path.name
            for path, text in expected.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != text
        ]
        extra = [
            path.name for path in TARGET.glob("*.schema.json") if path not in expected
        ]
        if stale or extra:
            print(
                f"stale: {stale}, unexpected: {extra}: run generate_result_schemas.py"
            )
            return 1
        return 0
    TARGET.mkdir(parents=True, exist_ok=True)
    for path in TARGET.glob("*.schema.json"):
        if path not in expected:
            path.unlink()
    for path, text in expected.items():
        path.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
