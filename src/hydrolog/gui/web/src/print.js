// The print view (plan D14, D18 „Raport do druku”): css/print.css lays the shown section
// out on A4 (its charts, data, results, notices, provenance and command line; no
// controls), and the browser saves it as PDF. For the time of printing the page also
// takes the light theme, since paper is white, and opens the section's closed parts
// (<details>), then puts both back. „Raport do druku” calls printView; the browser's own
// print (Ctrl+P) gets the same through `beforeprint` and `afterprint`, which this module
// listens to from its first import.

let restore = null;

/**
 * Prepare the page for printing (once until finishPrint): the light theme and the shown
 * section's closed parts opened.
 */
export function preparePrint() {
  if (restore) return;
  const root = document.documentElement;
  const theme = Object.hasOwn(root.dataset, "theme") ? root.dataset.theme : null;
  root.dataset.theme = "light";
  root.dataset.printing = "true";
  const opened = [...document.querySelectorAll("section.section:not([hidden]) details:not([open])")];
  for (const part of opened) part.open = true;
  restore = () => {
    for (const part of opened) part.open = false;
    if (theme === null) delete root.dataset.theme;
    else root.dataset.theme = theme;
    delete root.dataset.printing;
  };
}

/** Put the page back as it was before preparePrint. */
export function finishPrint() {
  if (!restore) return;
  const undo = restore;
  restore = null;
  undo();
}

/** Print the shown section: „Raport do druku”, a PDF through the browser's dialog. */
export function printView() {
  preparePrint();
  try {
    window.print();
  } finally {
    finishPrint();
  }
}

window.addEventListener("beforeprint", preparePrint);
window.addEventListener("afterprint", finishPrint);
