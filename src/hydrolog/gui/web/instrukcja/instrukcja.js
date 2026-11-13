// The guide's page: the theme switch of the app's top bar (Auto, Jasny, Ciemny), the same
// component, so the choice is the app's ("nogat-theme"); ../theme-init.js has applied it
// before the first paint. On a public GUI the page ends with the app's footer (Nogat
// DEV-15.7, DEV-15.8: the statement and „Regulamin”), drawn when GET ../api/terms names
// the regulamin; elsewhere, or when the answer fails, there is none. The rest of the page
// is static HTML.

import { html, render } from "../src/html.js";
import { TermsFooter, termsOf } from "../src/ui/footer.js";
import { ThemeSwitch } from "../src/ui/top-bar.js";

const place = document.getElementById("theme");
if (place) render(html`<${ThemeSwitch} />`, place);

/**
 * Draw the footer of a public GUI under the guide: the regulamin's address is relative to
 * the app's page, one level up.
 */
async function drawFooter() {
  const footer = document.getElementById("footer");
  if (!footer) return;
  const app = new URL("../", document.baseURI);
  let terms = null;
  try {
    const response = await fetch(new URL("api/terms", app), { cache: "no-store" });
    if (response.ok) terms = termsOf(await response.json());
  } catch {
    // No answer: the page stays without the footer, as on a GUI that is not public
  }
  if (terms) render(html`<${TermsFooter} terms=${new URL(terms, app).href} />`, footer);
}

drawFooter();
