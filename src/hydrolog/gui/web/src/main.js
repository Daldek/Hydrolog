// Entry of the page: the diagnostics of „Zgłoś uwagę” start recording, then the shell
// renders into <div id="app" class="shell">. Every URL the page uses is relative to it
// (document.baseURI), so the GUI works at "/" and under a prefix.

import { App } from "./app.js";
import { installDiagnostics } from "./diagnostics.js";
import { html, render } from "./html.js";

installDiagnostics();
render(html`<${App} />`, document.getElementById("app"));
