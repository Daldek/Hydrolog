// The guide's page: the theme switch of the app's top bar (Auto, Jasny, Ciemny), the same
// component, so the choice is the app's ("nogat-theme"); ../theme-init.js has applied it
// before the first paint. The rest of the page is static HTML.

import { html, render } from "../src/html.js";
import { ThemeSwitch } from "../src/ui/top-bar.js";

const place = document.getElementById("theme");
if (place) render(html`<${ThemeSwitch} />`, place);
