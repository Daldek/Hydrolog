"""The chart module of the GUI (plan D12, slice S2b) in Chromium.

The pure modules (``scale.js``: numbers, ticks, the log, time and Gumbel
scales; ``axes.js``: the layout) are tested through
``page.evaluate(import(…))``, without a Node toolchain (D17). ``draw.js``
draws a hydrograph with its hyetograph and peak, a unit hydrograph, a
probability plot and the tc comparison into the GUI's page (its policy, its
tokens); the readout follows the keys and the pointer, and ``toPng`` gives a
PNG twice the drawn size without breaking the policy. ``Chart`` (Preact)
draws them in both themes, and a theme switch recolours them without a
redraw.
"""

import re
import struct
from collections.abc import Callable
from itertools import pairwise
from typing import Any

import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import Tab

NBSP = "\u00a0"
# Hosts of the charts over the shell, at fixed places (set through the CSSOM).
HOSTS = """
() => {
  const places = {host: [0, 0], host2: [470, 0], host3: [0, 820]};
  for (const [id, [top, left]] of Object.entries(places)) {
    const host = document.createElement("div");
    host.id = id;
    host.style.cssText = `position: fixed; top: ${top}px; left: ${left}px; `
      + "width: 800px; z-index: 1000; background: var(--surface);";
    document.body.append(host);
  }
}
"""
# Nogat's tokens of both themes (tokens.css, Nogat d1b5820): --info, --surface.
INFO = {"light": "rgb(29, 78, 216)", "dark": "rgb(88, 166, 255)"}
SURFACE = {"light": "rgb(255, 255, 255)", "dark": "rgb(22, 27, 34)"}

# Kamiennik-like data: 10 min steps, rain over 12 h, a flood wave over 24 h.
HYDROGRAPH = """
const dt = 10;
const p = Array.from({length: 72}, (_, k) => {
  const t = (k + 0.5) / 72;
  return 105 * 30 * t * (1 - t) ** 4 / 72;
});
const pe = p.map((v, k) => (k < 20 ? 0 : v * 0.6));
const q = Array.from({length: 145}, (_, i) => {
  const t = i * dt;
  return t < 140 ? 0 : 60.2148 * Math.exp(-(((t - 380) / 150) ** 2));
});
const spec = {
  title: "Hietogram i hydrogram",
  x: {label: "czas [h]", scale: "time"},
  y: {label: "Q [m³/s]", unit: "m³/s"},
  y2: {label: "P, Pe [mm / 10 min]", unit: "mm"},
  series: [
    {id: "p", kind: "bars", axis: "y2", cls: "bar-p", label: "Opad całkowity P",
     data: p.map((v, k) => [k * dt, v])},
    {id: "pe", kind: "bars", axis: "y2", cls: "bar-pe", label: "Opad efektywny Pe",
     data: pe.map((v, k) => [k * dt, v])},
    {id: "q", kind: "area", cls: "s1", label: "Przepływ Q",
     data: q.map((v, i) => [i * dt, v])},
  ],
  marks: [{kind: "peak", x: 380, y: 60.2148, label: "Qmax 60,2 m³/s · 6:20 h"},
          {kind: "vline", axis: "y2", x: 200, label: "Pe > 0 od 3:20", extend: 8}],
  legend: true,
  readout: {series: "q"},
};
"""

# The mockup's sample: GEV quantiles and 26 annual maxima, probabilities in %.
PROBABILITY = """
const ps = [99, 95, 90, 80, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1];
const gev = ps.map((p) => {
  const u = -Math.log(-Math.log(1 - p / 100));
  return [p, 120 + 40 * u + 2 * u * u];
});
const empirical = Array.from({length: 26}, (_, i) => {
  const p = 100 * (i + 1) / 27;
  const u = -Math.log(-Math.log(1 - p / 100));
  return [p, 118 + 41 * u];
});
const spec = {
  title: "Krzywe prawdopodobieństwa przewyższenia",
  x: {label: "prawdopodobieństwo przewyższenia (siatka Gumbela)", scale: "gumbel",
      domain: [99.3, 0.09]},
  y: {label: "Q [m³/s]", unit: "m³/s"},
  series: [
    {id: "gev", kind: "line", cls: "s1 best", label: "GEV", data: gev},
    {id: "max", kind: "points", label: "Maksima roczne", data: empirical},
  ],
  marks: [{kind: "peak", x: 1, y: 307.3, guides: "xy",
           label: "Q 1% = 307,3 m³/s (GEV)"}],
  legend: true,
  readout: {series: "gev"},
};
"""


def open_page(tab: Tab) -> Any:
    """Open the GUI's page in ``tab`` and add the chart hosts; return the page."""
    tab.open()
    tab.page.evaluate(HOSTS)
    return tab.page


@pytest.fixture
def page(tab: Tab) -> Any:
    """Yield the GUI's page with the chart hosts (the tab checks errors and CSP)."""
    return open_page(tab)


def scale_js(page: Any, body: str) -> Any:
    """Evaluate ``body`` (an expression of ``s``, the module ``scale.js``)."""
    return page.evaluate(
        f"async () => {{ const s = await import('./src/charts/scale.js'); "
        f"return {body}; }}"
    )


def draw(page: Any, data: str, host: str = "host") -> None:
    """Draw ``spec`` (defined by the script ``data``) into ``#<host>``."""
    page.evaluate(
        "async () => { const {drawChart} = await import('./src/charts/draw.js');"
        f"{data} window.__chart = drawChart("
        f"document.getElementById('{host}'), spec); }}"
    )


# --- pure functions ----------------------------------------------------------


def test_polish_numbers(page: Any) -> None:
    got = scale_js(
        page,
        "[s.formatNumber(1046213.2), s.formatNumber(1000), s.formatNumber(0.25, 2),"
        " s.formatNumber(-3), s.formatNumber(-0.001, 1), s.formatNumber(60.2148, 2),"
        " s.formatTime(380), s.formatTime(5)]",
    )
    assert got == [
        f"1{NBSP}046{NBSP}213",
        "1000",
        "0,25",
        "\u22123",
        "0,0",
        "60,21",
        "6:20",
        "0:05",
    ]


def test_nice_steps_and_domains(page: Any) -> None:
    got = scale_js(
        page,
        "[s.niceStep(65, 7), s.niceStep(3.3, 4), s.niceStep(0.9, 4),"
        " s.niceDomain([0, 60.2148], {count: 7}),"
        " s.niceDomain([2.4, 3.1], {zero: false, pad: 0}),"
        " s.niceDomain([0, 1.2], {count: 6}).ticks.map((t) => t.label),"
        " s.niceDomain([0, 0])]",
    )
    step65, step33, step09, flood, narrow, labels, empty = got
    assert (step65, step33, step09) == (10, 1, 0.25)
    assert (flood["min"], flood["max"], flood["step"]) == (0, 70, 10)
    assert [tick["label"] for tick in flood["ticks"]] == [
        "0",
        "10",
        "20",
        "30",
        "40",
        "50",
        "60",
        "70",
    ]
    assert (narrow["min"], narrow["max"], narrow["step"]) == (2.4, 3.2, 0.2)
    # one number of decimals per axis, so the labels align
    assert labels == ["0,00", "0,25", "0,50", "0,75", "1,00", "1,25", "1,50"]
    assert (empty["min"], empty["max"]) == (0, 1.2)  # all zero: 0 to 1 with headroom


def test_log_and_time_ticks(page: Any) -> None:
    decades, close, day, short, hour, small, domain = scale_js(
        page,
        "[s.logTicks(1, 1000).map((t) => t.label),"
        " s.logTicks(0.1, 10).map((t) => t.label),"
        " s.timeTicks(0, 1440),"
        " s.timeTicks(0, 90, 8),"
        " s.timeTicks(0, 60),"
        " s.timeTicks(0, 60, 8),"
        " s.timeDomain([0, 10, 1430])]",
    )
    assert decades == ["1", "10", "100", "1000"]
    assert close == ["0,1", "0,2", "0,5", "1", "2", "5", "10"]
    assert day["step"] == 120
    assert [tick["label"] for tick in day["ticks"]] == [str(h) for h in range(0, 25, 2)]
    assert short["step"] == 15
    assert [tick["label"] for tick in short["ticks"]][:3] == ["0,00", "0,25", "0,50"]
    # A one-hour rain: tenths of an hour, not 0,1666666667
    assert [tick["label"] for tick in hour["ticks"]][:3] == ["0,0", "0,1", "0,2"]
    assert [tick["label"] for tick in small["ticks"]] == [
        "0,0",
        "0,2",
        "0,4",
        "0,6",
        "0,8",
        "1,0",
    ]
    assert (domain["min"], domain["max"]) == (0, 1440)


def test_a_series_of_years_keeps_its_ticks_and_its_peak(page: Any) -> None:
    # 150 001 steps of 10 min (a Nash unit hydrograph with n = 200, K = 1500 min)
    got = page.evaluate(
        "async () => { const s = await import('./src/charts/scale.js');"
        " const {thinPoints} = await import('./src/charts/series.js');"
        " const values = Array.from({length: 150001}, (_, i) => i === 29851 ? 5"
        "  : i === 70000 ? NaN : Math.exp(-(((i - 29851) / 3000) ** 2)));"
        " const points = values.map((y, i) => ({x: i * 10, y}));"
        " const kept = thinPoints(points, (x) => x / 2000, 680);"
        " return {extent: s.extent(values), ticks: s.timeTicks(0, 1500010),"
        "  kept: kept.length, peak: kept.some((p) => p.y === 5),"
        "  gap: kept.some((p) => Number.isNaN(p.y)),"
        "  ends: [kept[0].x, kept.at(-1).x],"
        "  ordered: kept.every((p, i) => i === 0 || p.x > kept[i - 1].x),"
        "  short: thinPoints(points.slice(0, 100), (x) => x, 680).length}; }"
    )
    assert got["extent"] == [0, 5]  # no spread into Math.max: no stack overflow
    ticks = got["ticks"]
    assert ticks["step"] % 10080 == 0 and len(ticks["ticks"]) <= 13
    assert 680 < got["kept"] <= 4 * 680  # the columns' extremes, not every step
    assert got["peak"] and got["gap"] and got["ordered"]
    assert got["ends"] == [0, 1500000]
    assert got["short"] == 100  # a short series is drawn whole


def test_the_gumbel_axis_is_linear_in_the_reduced_variate(page: Any) -> None:
    got = scale_js(
        page,
        "(() => { const g = s.gumbelScale([99.3, 0.09], [64, 744]);"
        " return {u1: s.reducedVariate(1), back: s.exceedanceFromVariate("
        "s.reducedVariate(0.5)), at: [90, 1, 0.1].map(g), inv: g.invert(g(2)),"
        " ticks: s.gumbelTicks(g), pos: s.gumbelTicks(g).map((t) => g(t.value)),"
        " domain: s.gumbelDomain([50, 1])}; })()",
    )
    assert got["u1"] == pytest.approx(4.60015, abs=1e-5)
    assert got["back"] == pytest.approx(0.5)
    assert got["inv"] == pytest.approx(2)
    # The mockup's probability paper: 90 % at 124.6, 1 % at 554.2, 0.1 % at 736.7.
    x90, x1, x01 = got["at"]
    assert (x1 - x90) / (x01 - x90) == pytest.approx(429.6 / 612.1, abs=2e-3)
    ticks = {tick["label"]: tick["sub"] for tick in got["ticks"]}
    assert ticks["50"] == "2"
    assert ticks["1"] == "100"
    assert ticks["0,1"] == "1000"
    assert ticks["90"] == "1,11"
    assert "95" not in ticks  # too near 90 on this axis
    assert "99" not in ticks  # beside the row labels "p [%]" and "T [lata]"
    positions = got["pos"]
    assert positions == sorted(positions)
    assert min(b - a for a, b in pairwise(positions)) >= 30
    left, right = got["domain"]
    assert left > 50
    assert right < 1


def test_the_hyetograph_panel_hangs_above_the_hydrograph(page: Any) -> None:
    got = page.evaluate(
        "async () => { const {chartLayout} = await import('./src/charts/axes.js');"
        f"{HYDROGRAPH} const l = chartLayout(spec);"
        " return {upper: l.upper, main: l.main, zero2: l.y2.scale(0),"
        " zero: l.y.scale(0), x0: l.x.scale(0), x1: l.x.scale(1440),"
        " plot: l.plot, ymax: l.y.max, y2max: l.y2.max}; }"
    )
    assert got["upper"]["bottom"] < got["main"]["top"]
    assert got["zero2"] == pytest.approx(got["upper"]["top"])
    assert got["zero"] == pytest.approx(got["main"]["bottom"])
    assert got["x0"] == got["plot"]["left"]
    assert got["x1"] == got["plot"]["right"]
    assert got["ymax"] == 70
    assert got["y2max"] >= 3.3


# --- drawing -----------------------------------------------------------------


def test_a_hydrograph_with_its_hyetograph_and_peak(page: Any) -> None:
    draw(page, HYDROGRAPH)
    svg = page.locator("#host svg.chart-svg")
    assert svg.get_attribute("viewBox") == "0 0 760 432"
    assert svg.get_attribute("aria-label") == "Hietogram i hydrogram"
    assert page.locator("#host").get_attribute("class") == "chart wide"
    top = page.evaluate("window.__chart.svg.querySelector('.axis:nth-of-type(2)')")
    assert top is not None
    bars = page.locator("#host .bars.bar-p rect")
    assert bars.count() == 72
    hanging = {bars.nth(i).get_attribute("y") for i in range(72)}
    assert hanging == {"26"}  # every bar hangs from the top of the upper panel
    assert page.locator("#host .bars.bar-pe rect").count() == 52
    assert page.locator("#host path.q-area.s1").get_attribute("d").endswith("Z")
    line = page.locator("#host path.ser.s1").get_attribute("d")
    assert line.startswith("M56,394L")
    dot = page.locator("#host .peak-dot")
    peak = page.evaluate(
        "(() => { const c = document.querySelector('#host .peak-dot');"
        " return [Number(c.getAttribute('cx')), Number(c.getAttribute('cy'))]; })()"
    )
    assert dot.count() == 1
    assert peak[0] == pytest.approx(56 + 688 * 380 / 1440, abs=0.1)
    label = page.locator("#host .peak-label")
    assert label.text_content() == "Qmax 60,2 m³/s · 6:20 h"
    box = page.evaluate(
        "(() => { const b = document.querySelector('#host .peak-box').getBBox();"
        " const t = document.querySelector('#host .peak-label').getBBox();"
        " return [b.x, b.width, t.x, t.width]; })()"
    )
    assert box[0] < box[2] and box[2] + box[3] < box[0] + box[1]
    ticks = page.locator("#host text.tick[text-anchor=middle]").all_text_contents()
    assert ticks == [str(h) for h in range(0, 25, 2)]
    assert page.locator("#host .mark.vline .note").text_content() == "Pe > 0 od 3:20"
    legend = page.locator("#host .chart-legend > span")
    assert legend.all_text_contents() == [
        "Opad całkowity P",
        "Opad efektywny Pe",
        "Przepływ Q",
    ]
    assert page.locator("#host .chart-legend i.sw.bar-p").count() == 1
    assert page.locator("#host .chart-legend i.sw-line.s1").count() == 1


def test_a_small_unit_hydrograph(page: Any) -> None:
    uh = """
    const u = Array.from({length: 31},
      (_, i) => [i * 10, 1.2 * (i / 9) ** 3 * Math.exp(3 - i / 3)]);
    const spec = {size: "small", x: {label: "czas [h]", scale: "time", max: 300},
      y: {label: "u [m³/s na 1 mm]"}, series: [{id: "u", kind: "area", data: u}],
      marks: [{kind: "peak", x: 90, y: 1.2, label: "qp 1,20 · tp 1:30"}],
      readout: true};
    """
    draw(page, uh)
    assert page.locator("#host svg").get_attribute("viewBox") == "0 0 360 178"
    assert page.locator("#host").get_attribute("class") == "chart"
    assert page.locator("#host .peak-tag").text_content() == "qp 1,20 · tp 1:30"
    assert page.locator("#host .peak-box").count() == 0
    labels = page.locator("#host text.tick[text-anchor=end]").all_text_contents()
    assert labels[0] == "0,0" and "1,5" in labels
    assert page.locator("#host .chart-legend").count() == 0


def test_a_probability_plot_on_gumbel_paper(page: Any) -> None:
    draw(page, PROBABILITY)
    assert page.locator("#host .emp circle").count() == 26
    assert page.locator("#host path.ser.s1.best").count() == 1
    subs = page.locator("#host text.tick.sub").all_text_contents()
    assert "100" in subs and "1000" in subs and "1,11" in subs
    labels = page.locator("#host text.axis-label").all_text_contents()
    assert labels[:2] == ["p [%]", "T [lata]"]
    assert page.locator("#host .peak-line").count() == 2  # guides to both axes
    assert page.locator("#host .chart-legend i.sw-dot").count() == 1


def test_horizontal_bars_on_a_band_axis(page: Any) -> None:
    tc = """
    const spec = {x: {label: "tc [min]"}, y: {scale: "band"},
      series: [{id: "tc", data: [
      {y: "Kirpich", sub: "kirpich", x: 162.9, cls: "warn used", text: "162,9 min"},
      {y: "NRCS (NEH 630)", sub: "nrcs", x: 377.5, cls: "ok", text: "377,5 min"},
      {y: "FAA", sub: "faa", x: 23.8, cls: "bad", text: "23,8 min"}]}],
      legend: [{kind: "box", cls: "ok", label: "w zakresie"}]};
    """
    draw(page, tc)
    bars = page.locator("#host rect.hbar")
    assert bars.count() == 3
    assert bars.nth(0).get_attribute("class") == "hbar warn used"
    assert bars.nth(0).get_attribute("x") == "160"
    names = page.locator("#host .bar-name").all_text_contents()
    assert names == ["Kirpich", "NRCS (NEH 630)", "FAA"]
    assert page.locator("#host .bar-val").nth(1).text_content() == "377,5 min"
    widths = [float(bars.nth(i).get_attribute("width")) for i in range(3)]
    assert widths[1] > widths[0] > widths[2]
    assert page.locator("#host svg").get_attribute("tabindex") is None
    assert page.locator("#host .chart-legend i.sw.ok").count() == 1


# --- readout -----------------------------------------------------------------


def test_the_readout_follows_the_keys(page: Any) -> None:
    draw(page, HYDROGRAPH)
    svg = page.locator("#host svg")
    assert svg.get_attribute("tabindex") == "0"
    live = page.locator("#host .chart-sr")
    svg.focus()
    page.keyboard.press("Home")
    assert live.text_content().startswith("t = 0:00 · ")
    for _ in range(38):
        page.keyboard.press("ArrowRight")
    text = live.text_content()
    assert text.startswith("t = 6:20 · ")
    assert f"Przepływ Q: 60,21{NBSP}m³/s" in text
    assert "Opad całkowity P: " in text and f"{NBSP}mm" in text
    page.keyboard.press("Shift+ArrowLeft")
    assert live.text_content().startswith("t = 4:40 · ")
    page.keyboard.press("End")
    assert live.text_content().startswith("t = 24:00 · ")
    assert "Opad całkowity P" not in live.text_content()  # no rain after 12 h
    readout = page.locator("#host g.readout")
    assert readout.get_attribute("visibility") is None
    assert page.locator("#host .readout-line").count() == 1
    assert page.locator("#host .readout-box").count() == 1
    page.keyboard.press("Escape")
    assert readout.get_attribute("visibility") == "hidden"
    assert live.text_content() == ""


def test_the_readout_follows_the_pointer_and_survives_an_update(page: Any) -> None:
    draw(page, HYDROGRAPH)
    box = page.locator("#host svg").bounding_box()
    scale = box["width"] / 760
    x = box["x"] + (56 + 688 * 380 / 1440) * scale
    page.mouse.move(x, box["y"] + 300 * scale)
    head = page.locator("#host .readout-head")
    assert head.text_content() == "t = 6:20"
    dots = page.locator("#host .readout-dot.s1")
    assert dots.count() == 1
    page.mouse.move(box["x"] + 5, box["y"] + 5)
    assert page.locator("#host g.readout").get_attribute("visibility") == "hidden"
    page.locator("#host svg").focus()
    page.keyboard.press("End")
    page.evaluate(
        f"() => {{ {HYDROGRAPH} spec.series[2].data = spec.series[2].data.map("
        "([t, v]) => [t, v * 2]); window.__chart.update(spec); }"
    )
    text = page.locator("#host .chart-sr").text_content()
    assert text.startswith("t = 24:00")
    labels = page.locator("#host text.tick[text-anchor=end]").all_text_contents()
    assert "140" in labels and "70" not in labels


def test_a_probability_readout_names_the_return_period(page: Any) -> None:
    draw(page, PROBABILITY)
    page.locator("#host svg").focus()
    page.keyboard.press("Home")
    for _ in range(9):
        page.keyboard.press("ArrowRight")
    text = page.locator("#host .chart-sr").text_content()
    assert text.startswith("p = 1,0 % · T = 100 lat · GEV: ")


# --- PNG ---------------------------------------------------------------------


def test_to_png_is_twice_the_drawn_size(page: Any) -> None:
    draw(page, HYDROGRAPH)
    got = page.evaluate(
        "async () => { const {toPng} = await import('./src/charts/png.js');"
        " const svg = window.__chart.svg; const r = svg.getBoundingClientRect();"
        " const blob = await toPng(svg);"
        " const bytes = Array.from(new Uint8Array(await blob.arrayBuffer()));"
        " return {type: blob.type, w: Math.round(r.width), h: Math.round(r.height),"
        " bytes: bytes.slice(0, 24), size: bytes.length}; }"
    )
    head = bytes(got["bytes"])
    assert got["type"] == "image/png"
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", head[16:24])
    assert (width, height) == (2 * got["w"], 2 * got["h"])
    assert got["size"] > 5_000  # drawn, not blank


def test_to_png_inlines_the_styles_and_leaves_the_readout_out(page: Any) -> None:
    draw(page, HYDROGRAPH)
    page.locator("#host svg").focus()
    page.keyboard.press("Home")
    assert page.locator("#host .readout-box").count() == 1
    got = page.evaluate(
        "async () => { const {svgText} = await import('./src/charts/png.js');"
        " const {text, width} = svgText(window.__chart.svg);"
        " return {text, width}; }"
    )
    text = got["text"]
    assert text.startswith("<svg")
    assert 'xmlns="http://www.w3.org/2000/svg"' in text
    assert f'width="{got["width"]}"' in text
    assert "stroke-dasharray" in text and "tabindex" not in text
    assert "readout" not in text


# --- Chart (Preact) and the themes --------------------------------------------

CHART_RENDER = """
async () => {
  const htm = (await import('./vendor/htm/htm.mjs')).default;
  const {h, render} = await import('./vendor/preact/preact.mjs');
  const {Chart} = await import('./src/charts/chart.js');
  const html = htm.bind(h);
  window.__render = (id, spec, ref) =>
    render(html`<${Chart} spec=${spec} svgRef=${ref} />`, document.getElementById(id));
  window.__unmount = (id) => render(null, document.getElementById(id));
}
"""
UH = """
const spec = {size: "small", x: {label: "czas [h]", scale: "time", max: 300},
  y: {label: "u [m³/s na 1 mm]"}, readout: true,
  series: [{id: "u", kind: "area", label: "u(t)", data: Array.from({length: 31},
    (_, i) => [i * 10, 1.2 * (i / 9) ** 3 * Math.exp(3 - i / 3)])}],
  marks: [{kind: "peak", x: 90, y: 1.2, label: "qp 1,20 · tp 1:30"}]};
"""


def render_all(page: Any) -> None:
    """Render the hydrograph, the unit hydrograph and the probability plot.

    ``Chart`` draws in an effect, after the render: wait until all three are drawn.
    """
    page.evaluate(CHART_RENDER)
    for host, data in (("host", HYDROGRAPH), ("host2", UH), ("host3", PROBABILITY)):
        page.evaluate(
            f"() => {{ {data} window.__ref_{host} = {{current: null}};"
            f" window.__render('{host}', spec, window.__ref_{host}); }}"
        )
    page.wait_for_function(
        "() => ['host', 'host2', 'host3'].every((id) => window['__ref_' + id].current)"
    )


def colours(page: Any) -> dict[str, str]:
    """Return the computed colours of the drawn charts."""
    return page.evaluate(
        """() => {
          const style = (selector, name) =>
            getComputedStyle(document.querySelector(selector)).getPropertyValue(name);
          return {
            q: style("#host .ser.s1", "stroke"),
            area: style("#host .q-area.s1", "fill"),
            rain: style("#host .bars.bar-p rect", "fill"),
            rainEff: style("#host .bars.bar-pe rect", "fill"),
            peakBox: style("#host .peak-box", "fill"),
            uh: style("#host2 .ser.s1", "stroke"),
            points: style("#host3 .emp circle", "fill"),
            gev: style("#host3 .ser.s1", "stroke"),
            tick: style("#host .tick", "fill"),
          };
        }"""
    )


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_the_charts_render_in_both_themes(
    new_tab: Callable[..., Tab], theme: str
) -> None:
    page = open_page(new_tab(theme=theme))
    render_all(page)
    assert page.locator("#host .bars.bar-p rect").count() == 72
    assert page.locator("#host .peak-label").text_content() == (
        "Qmax 60,2 m³/s · 6:20 h"
    )
    assert page.locator("#host2 svg").get_attribute("viewBox") == "0 0 360 178"
    assert page.locator("#host3 .emp circle").count() == 26
    got = colours(page)
    assert got["q"] == INFO[theme]
    assert got["uh"] == INFO[theme]
    assert got["gev"] == INFO[theme]
    assert got["points"] == SURFACE[theme]
    assert got["peakBox"] == SURFACE[theme]
    assert got["rain"] != got["rainEff"]
    assert "none" not in (got["area"], got["rain"], got["tick"])
    for host in ("host", "host2", "host3"):
        assert page.evaluate(f"window.__ref_{host}.current.tagName") == "svg"


def test_a_theme_switch_recolours_without_a_redraw(
    new_tab: Callable[..., Tab],
) -> None:
    page = open_page(new_tab(theme="light"))
    render_all(page)
    page.evaluate("window.__q = document.querySelector('#host .ser.s1')")
    before = colours(page)
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    after = colours(page)
    assert page.evaluate("document.querySelector('#host .ser.s1') === window.__q")
    assert (before["q"], after["q"]) == (INFO["light"], INFO["dark"])
    assert before["rain"] != after["rain"]
    assert after["points"] == SURFACE["dark"]


def test_chart_redraws_its_svg_in_place_and_unmounts(page: Any) -> None:
    render_all(page)
    page.evaluate("window.__svg = window.__ref_host2.current")
    page.evaluate(
        f"() => {{ {UH} spec.series[0].data = spec.series[0].data.map(([t, v]) =>"
        " [t, v * 3]); window.__render('host2', spec, window.__ref_host2); }"
    )
    assert page.evaluate("window.__ref_host2.current === window.__svg")
    ticks = page.locator("#host2 text.tick[text-anchor=end]")
    expect(ticks.filter(has_text=re.compile(r"^4$"))).to_have_count(1)
    page.evaluate("window.__unmount('host2')")
    assert page.locator("#host2 svg").count() == 0
    assert page.evaluate("window.__ref_host2.current") is None
