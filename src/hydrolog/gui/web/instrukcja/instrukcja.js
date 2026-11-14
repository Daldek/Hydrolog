// The guide's page: the theme switch of the app's top bar (Auto, Jasny, Ciemny), the same
// component, so the choice is the app's ("nogat-theme"); ../theme-init.js has applied it
// before the first paint. On a public GUI the contents on the left end with the app's
// small link „Regulamin” (Nogat DEV-15.7, ../src/ui/terms.js, a new tab), drawn when
// GET ../api/terms names the regulamin; elsewhere, or when the answer fails, there is
// none. The rest of the page is static HTML.

import { html, render } from "../src/html.js";
import { TermsLink, termsOf } from "../src/ui/terms.js";
import { ThemeSwitch } from "../src/ui/top-bar.js";

const place = document.getElementById("theme");
if (place) render(html`<${ThemeSwitch} />`, place);

/**
 * Draw „Regulamin” of a public GUI at the bottom of the contents: the regulamin's address
 * is relative to the app's page, one level up.
 */
async function drawTerms() {
  const slot = document.getElementById("terms");
  if (!slot) return;
  const app = new URL("../", document.baseURI);
  let terms = null;
  try {
    const response = await fetch(new URL("api/terms", app), { cache: "no-store" });
    if (response.ok) terms = termsOf(await response.json());
  } catch {
    // No answer: the contents stay without the link, as on a GUI that is not public
  }
  if (terms) render(html`<${TermsLink} terms=${new URL(terms, app).href} className="guide-terms" />`, slot);
}

drawTerms();
