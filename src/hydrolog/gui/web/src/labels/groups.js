/**
 * Polish titles of the catalog's command groups (the first word of a command's name). The
 * catalog has no group titles of its own, so the GUI names them; a group without a title
 * shows its name only.
 */

export const groups = {
  tc: "Czas koncentracji",
  cn: "Liczba CN (TR-55)",
  scs: "Opad efektywny SCS-CN",
  precip: "Hietogramy i opad obszarowy",
  uh: "Hydrogramy jednostkowe",
  hydrograph: "Hydrogram odpływu",
  route: "Transformacja fali",
  morphometry: "Morfometria zlewni",
  network: "Sieć rzeczna",
  stats: "Statystyka przepływów",
  hydrometrics: "Hydrometria",
  meteo: "Statystyka meteorologiczna",
  soil: "Uziarnienie i HSG",
  report: "Raport obliczeniowy",
  config: "Ustawienia",
  commands: "Katalog poleceń",
  gui: "Interfejs graficzny",
};

/**
 * The title of a command group.
 *
 * @param {string} group the group's name, e.g. "uh"
 * @returns {string|null} the Polish title, null when the GUI has none
 */
export function groupTitle(group) {
  return Object.hasOwn(groups, group) ? groups[group] : null;
}
