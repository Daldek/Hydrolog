/**
 * Texts of the generic result view (forms/result-view.js): notices, scalars, series as a
 * chart and a table, tables of records, the targets of a plan, files and the JSON.
 */

export const results = {
  notices: "Uwagi",
  parameters: "Parametry wyniku",
  series: "Szeregi wyniku",
  seriesSub: "{names} · {rows}",
  rowForms: ["wiersz", "wiersze", "wierszy"],
  valueForms: ["wartość", "wartości", "wartości"],
  index: "Krok",
  time: "t [h:min]",
  timeAxis: "czas [h]",
  chart: "Wykres",
  records: "{name} · {rows}",
  json: "Dokument wyniku",
  jsonSub: "{envelope} z {schema}; długie listy zwinięte",
  fold: "… razem {count}",
  cancelled: "Obliczenie anulowano",
  plan: "Plan zapisu",
  nothing: "Wynik nie ma pól liczbowych ani szeregów; zobacz JSON.",
  truncated: "Pokazano {shown} z {rows}; całość w CSV i JSON.",
  more: "Pokaż wszystkie wiersze",
  /** Short names of the tiles (a field without one shows its label or name). */
  tiles: {
    cn_adjusted: "CN po AMC",
    initial_abstraction_mm: "Ia",
    k_min: "K",
    lag_time_min: "t_lag = n·K",
    n: "n",
    peak_discharge_m3s: "Qmax",
    peak_discharge_m3s_per_mm: "q_p",
    retention_mm: "S",
    runoff_coefficient: "Wsp. odpływu",
    tc_min: "tc",
    time_to_peak_min: "Do szczytu",
    total_effective_mm: "Pe",
    total_precipitation_mm: "P",
    total_volume_m3: "Objętość",
  },
};
