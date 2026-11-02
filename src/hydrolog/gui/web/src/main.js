// Entry of the page: the shell renders into <div id="app" class="shell">. Every URL the page
// uses is relative to it (document.baseURI), so the GUI works at "/" and under a prefix.

import { App } from "./app.js";
import { html, render } from "./html.js";

render(html`<${App} />`, document.getElementById("app"));
