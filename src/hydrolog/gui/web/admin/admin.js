// Hydrolog's part of the admin panel (Nogat DEV-15.13): under „Statystyki”, folded as the
// kit folds a report's „Kontekst”, what each daily total counts (DEV-15.11), the texts of
// labels/admin.js. The kit's shell builds its sections when nogat-admin.js runs, which this
// module imports, so the section exists here. Every text is a text node.

import { STATS_COLUMNS } from "../nogat/nogat-admin.js";
import { admin } from "../src/labels/admin.js";

/** @returns {HTMLDetailsElement} „Co liczą kolumny” with one term per counted column */
function countsNote() {
  const details = document.createElement("details");
  details.className = "nogat-admin-context hydrolog-admin-counts";
  const summary = document.createElement("summary");
  summary.textContent = admin.counts;
  const intro = document.createElement("p");
  intro.className = "nogat-admin-note";
  intro.textContent = admin.countsIntro;
  const list = document.createElement("dl");
  for (const [key, heading] of STATS_COLUMNS) {
    const text = admin.columns[key];
    if (!text) continue;
    const term = document.createElement("dt");
    term.textContent = heading;
    const description = document.createElement("dd");
    description.textContent = text;
    list.append(term, description);
  }
  details.append(summary, intro, list);
  return details;
}

document.querySelector('nogat-admin section[data-admin-section="stats"]')?.append(countsNote());
