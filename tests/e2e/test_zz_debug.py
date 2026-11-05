"""Throwaway: diagnose the macOS and Windows failures on hosted runners."""

import json
import time
from collections.abc import Callable

from tests.e2e.conftest import Tab

WIDE = """() => {
  const page = document.querySelector('.guide-page');
  if (!page) return {missing: true};
  const box = page.getBoundingClientRect();
  const wide = [...page.querySelectorAll('*')]
    .map((el) => ({el, r: el.getBoundingClientRect()}))
    .filter(({r}) => r.width > 0 && r.right > box.right + 0.5)
    .map(({el, r}) => ({
      tag: el.tagName, cls: el.className && String(el.className),
      right: Math.round(r.right), width: Math.round(r.width),
      font: getComputedStyle(el).fontFamily,
      text: (el.textContent || '').trim().slice(0, 80)}));
  return {clientWidth: page.clientWidth, scrollWidth: page.scrollWidth,
    right: box.right, font: getComputedStyle(page).fontFamily, wide: wide.slice(0, 15)};
}"""


def test_zz_guide_width(new_tab: Callable[..., Tab]) -> None:
    tab = new_tab(width=390, height=844)
    tab.page.goto("about:blank")
    tab.open("instrukcja/")
    tab.page.wait_for_timeout(2000)
    print("GUIDE", json.dumps(tab.page.evaluate(WIDE), ensure_ascii=False, indent=1))


def test_zz_hash(tab: Tab) -> None:
    logs: list[str] = []
    page = tab.page
    page.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
    tab.open("#polecenia")
    page.wait_for_timeout(1500)
    page.locator(
        'section[data-section="polecenia"] .cmd-item[data-command="route lag"] button'
    ).click()
    page.wait_for_timeout(1500)
    print("HASH1", page.evaluate("location.hash"))
    page.evaluate(
        "window.__h = []; addEventListener('hashchange', "
        "e => window.__h.push([e.oldURL.split('#')[1], e.newURL.split('#')[1], "
        "location.hash]))"
    )
    page.evaluate("location.hash = '#polecenia/scs/effective'")
    for _ in range(6):
        time.sleep(0.5)
        print(
            "HASH2",
            page.evaluate("location.hash"),
            page.evaluate("JSON.stringify(window.__h)"),
            page.locator('section[data-section="polecenia"] .cmd-form .cmd-head code')
            .all_inner_texts(),
        )
    print("CONSOLE", logs[-20:])


import pytest


@pytest.mark.parametrize("rate", [1, 4, 8, 12])
def test_zz_hash_throttled(tab: Tab, rate: int) -> None:
    from playwright.sync_api import expect

    from tests.e2e.test_polecenia import HEAD, POL, open_section

    page = tab.page
    page.context.new_cdp_session(page).send(
        "Emulation.setCPUThrottlingRate", {"rate": rate}
    )
    page = open_section(tab)
    lag = page.locator(f'{POL} .cmd-item[data-command="route lag"] button')
    lag.click()
    expect(page.locator(HEAD)).to_have_text("route lag")
    page.evaluate("location.hash = '#polecenia/scs/effective'")
    expect(page.locator(HEAD)).to_have_text("scs effective", timeout=5000)


def test_zz_hash_exact(tab: Tab) -> None:
    from playwright.sync_api import expect

    from tests.e2e.test_polecenia import HEAD, POL, open_section

    page = open_section(tab)
    page.evaluate(
        "window.__h = []; addEventListener('hashchange', "
        "e => window.__h.push([performance.now()|0, e.oldURL.split('#')[1], "
        "e.newURL.split('#')[1], location.hash]));"
        "const r = history.replaceState.bind(history);"
        "history.replaceState = (s, t, u) => { window.__h.push(['replace', "
        "performance.now()|0, String(u), new Error().stack.split('\\n').slice(1, 6)]);"
        " r(s, t, u); };"
    )
    lag = page.locator(f'{POL} .cmd-item[data-command="route lag"] button')
    lag.click()
    expect(page.locator(HEAD)).to_have_text("route lag")
    assert page.evaluate("location.hash") == "#polecenia/route/lag"
    expect(lag).to_have_attribute("aria-current", "true")
    expect(page.locator(".crumb-context")).to_contain_text("route lag")
    page.evaluate("window.__h.push(['set', performance.now()|0])")
    page.evaluate("location.hash = '#polecenia/scs/effective'")
    page.wait_for_timeout(3000)
    print("EXACT", page.evaluate("location.hash"), page.locator(HEAD).all_inner_texts())
    print("EXACT", json.dumps(page.evaluate("window.__h"), indent=1))
    expect(page.locator(HEAD)).to_have_text("scs effective", timeout=2000)
