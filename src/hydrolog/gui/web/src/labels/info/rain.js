/**
 * Explanations (i) of the rainfall of „Hydrogram zlewni” (plan D16, slice S3): the source of
 * the rainfall ("rain-source"), the four design hyetographs of `hietogram_type` ("rain-<type>")
 * and the time step ("rain-timestep", whose range against the unit hydrograph's time to peak
 * is Hydrolog's: `typical_ranges` of `hydrograph generate`), in the format of ui/info.js.
 */

export const rainInfo = {
  "rain-source": {
    title: "Źródło opadu: PMAXTP, hietogram albo własna seria",
    intro:
      "<p>PMAXTP: wysokość opadu P o prawdopodobieństwie przewyższenia p i czasie trwania D z atlasu " +
      "PMAXTP (IMGW-PIB; p i D wybierasz z wartości atlasu), wpisana ręcznie albo przyniesiona z " +
      "przekazaniem; GUI niczego nie pobiera. " +
      "Hietogram: wysokość i czas trwania podane wprost. W obu przypadkach Hydrolog rozkłada P w czasie " +
      "hietogramem projektowym (<code>hietogram_type</code>, <code>total_mm</code>, " +
      "<code>duration_min</code>; jak <code>precip hietogram</code>).</p>" +
      "<p>Własna seria: wysokości opadu w kolejnych krokach Δt (<code>values</code>, w poleceniu także " +
      "plik <code>input_file</code>), np. z deszczomierza; typ hietogramu nie jest wtedy używany, a czas " +
      "trwania to n·Δt.</p>",
    formula:
      "<math display='block'><mi>T</mi><mo>=</mo><mfrac><mn>100</mn><mi>p</mi></mfrac>" +
      "<mspace width='1.5em'></mspace><mi>P</mi><mo>=</mo><munderover><mo>∑</mo><mrow><mi>i</mi>" +
      "<mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msub><mi>P</mi><mi>i</mi></msub></math>",
    vars: [
      {
        symbol: "<math><mi>p</mi></math>",
        text:
          "prawdopodobieństwo przewyższenia: szansa, że w danym roku opad o czasie trwania D osiągnie lub " +
          "przekroczy P",
        unit: "%",
      },
      { symbol: "<math><mi>T</mi></math>", text: "okres powtarzalności", unit: "lata" },
      {
        symbol: "<math><mi>P</mi></math>",
        text: "suma opadu: <code>total_mm</code> albo suma serii",
        unit: "mm",
      },
      {
        symbol: "<math><mi>D</mi></math>",
        text: "czas trwania opadu, <code>duration_min</code>",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text:
          "wysokość opadu w i-tym kroku (<code>values</code>, każda ≥ 0); to wysokości w kroku, nie " +
          "natężenia w mm/h",
        unit: "mm",
      },
      {
        symbol: "<math><mi>n</mi></math>",
        text: "liczba kroków: w hietogramie ⌊D/Δt⌋, w serii liczba wartości",
        unit: "–",
      },
    ],
    note:
      "<p>Hydrogramowi przypisuje się to samo p co opadowi; to założenie metodyki, bo opad stuletni nie " +
      "zawsze wywołuje wezbranie stuletnie. Krytyczny czas trwania, dający największe wezbranie, nie jest " +
      "znany z góry (wg DVWK zwykle między t<sub>c</sub> a 2·t<sub>c</sub>), więc warto porównać kilka " +
      "czasów trwania. Własna seria daje hydrogram konkretnego zdarzenia, bez przypisanego " +
      "prawdopodobieństwa.</p>",
    sources:
      "IMGW-PIB 2022 (PMAXTP); DVWK 1984 (za KZGW 2017); KZGW 2017; USGS 2018; opis polecenia " +
      "<code>hydrograph generate</code>",
  },

  "rain-block": {
    title: "Hietogram blokowy",
    intro:
      "<p>Stałe natężenie przez cały czas trwania: każdy krok dostaje tę samą wysokość opadu. Polecenie " +
      "<code>precip hietogram</code>, w hydrogramie <code>hietogram_type = block</code>; typ nie ma " +
      "parametrów kształtu.</p>",
    formula:
      "<math display='block'><msub><mi>P</mi><mi>i</mi></msub><mo>=</mo><mfrac><mi>P</mi><mi>n</mi>" +
      "</mfrac><mspace width='1.5em'></mspace><mi>n</mi><mo>=</mo><mrow><mo>⌊</mo><mfrac><mi>D</mi>" +
      "<mi>Δt</mi></mfrac><mo>⌋</mo></mrow></math>",
    vars: [
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text: "wysokość opadu w i-tym kroku",
        unit: "mm",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu, <code>total_mm</code>", unit: "mm" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba kroków", unit: "–" },
      {
        symbol: "<math><mi>D</mi></math>",
        text: "czas trwania opadu, <code>duration_min</code>",
        unit: "min",
      },
      { symbol: "<math><mi>Δt</mi></math>", text: "krok czasowy, <code>timestep_min</code>", unit: "min" },
    ],
    note:
      "<p>Przy tej samej sumie i czasie trwania rozkład natężenia zmienia wysokość i czas kulminacji: opad " +
      "efektywny SCS-CN liczy się od sumy narastającej, więc ten sam blok opadu daje więcej odpływu, gdy " +
      "spada później (straty I<sub>a</sub> są już pokryte).</p>",
    sources: "Chow i in. 1988; KZGW 2017; opis polecenia <code>precip hietogram</code>",
  },

  "rain-triangular": {
    title: "Hietogram trójkątny",
    intro:
      "<p>Wysokości w krokach rosną liniowo do maksimum w położeniu p czasu trwania, potem liniowo " +
      "maleją. Polecenie <code>precip hietogram</code>, w hydrogramie " +
      "<code>hietogram_type = triangular</code> z parametrem <code>peak_position</code> (domyślnie 0,5).</p>",
    formula:
      "<math display='block'><msub><mi>w</mi><mi>j</mi></msub><mo>=</mo><mfrac><mi>j</mi>" +
      "<msub><mi>j</mi><mi>p</mi></msub></mfrac><mspace width='0.6em'></mspace><mtext>dla</mtext>" +
      "<mspace width='0.4em'></mspace><mi>j</mi><mo>≤</mo><msub><mi>j</mi><mi>p</mi></msub></math>" +
      "<math display='block'><msub><mi>w</mi><mi>j</mi></msub><mo>=</mo><mfrac><mrow><mi>n</mi><mo>−</mo>" +
      "<mi>j</mi><mo>+</mo><mn>1</mn></mrow><mrow><mi>n</mi><mo>−</mo><msub><mi>j</mi><mi>p</mi></msub>" +
      "<mo>+</mo><mn>1</mn></mrow></mfrac><mspace width='0.6em'></mspace><mtext>dla</mtext>" +
      "<mspace width='0.4em'></mspace><mi>j</mi><mo>&gt;</mo><msub><mi>j</mi><mi>p</mi></msub></math>" +
      "<math display='block'><msub><mi>j</mi><mi>p</mi></msub><mo>=</mo><mi>max</mi><mrow><mo>(</mo>" +
      "<mn>2</mn><mo>,</mo><mrow><mo>⌊</mo><mi>n</mi><mo>·</mo><mi>p</mi><mo>⌋</mo></mrow><mo>+</mo>" +
      "<mn>1</mn><mo>)</mo></mrow><mspace width='1.2em'></mspace><msub><mi>P</mi><mi>j</mi></msub>" +
      "<mo>=</mo><mi>P</mi><mo>·</mo><mfrac><msub><mi>w</mi><mi>j</mi></msub><mrow><mo>∑</mo>" +
      "<msub><mi>w</mi><mi>k</mi></msub></mrow></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>P</mi><mi>j</mi></msub></math>",
        text: "wysokość opadu w j-tym kroku",
        unit: "mm",
      },
      { symbol: "<math><msub><mi>w</mi><mi>j</mi></msub></math>", text: "waga kroku", unit: "–" },
      {
        symbol: "<math><mi>j</mi></math>",
        text: "numer kroku, 1…n, gdzie n = ⌊D/Δt⌋ (<code>duration_min</code>, <code>timestep_min</code>)",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>j</mi><mi>p</mi></msub></math>",
        text: "krok maksimum; przy n = 1 cały opad przypada na jeden krok",
        unit: "–",
      },
      {
        symbol: "<math><mi>p</mi></math>",
        text:
          "względne położenie maksimum, <code>peak_position</code>: 0 &lt; p &lt; 1 (bez końców); " +
          "domyślnie 0,5",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu, <code>total_mm</code>", unit: "mm" },
    ],
    note:
      "<p>Przy p = 0,5 i parzystym n maksimum wypada w kroku tuż po połowie czasu trwania (np. w 7. " +
      "z 12). Polska metodyka (za DVWK 1984) zaleca deszcz z maksimum w środku czasu trwania.</p>",
    sources: "KZGW 2017; DVWK 1984 (za KZGW 2017); opis polecenia <code>precip hietogram</code>",
  },

  "rain-beta": {
    title: "Hietogram beta",
    intro:
      "<p>Wysokości w krokach według gęstości rozkładu beta o parametrach α i β, liczonej w środkach " +
      "kroków. Polecenie <code>precip hietogram</code>, w hydrogramie <code>hietogram_type = beta</code> z " +
      "parametrami <code>alpha</code> (domyślnie 2) i <code>beta</code> (domyślnie 5).</p>",
    formula:
      "<math display='block'><msub><mi>w</mi><mi>i</mi></msub><mo>=</mo><msubsup><mi>t</mi><mi>i</mi>" +
      "<mrow><mi>α</mi><mo>−</mo><mn>1</mn></mrow></msubsup><mo>·</mo><msup><mrow><mo>(</mo><mn>1</mn>" +
      "<mo>−</mo><msub><mi>t</mi><mi>i</mi></msub><mo>)</mo></mrow><mrow><mi>β</mi><mo>−</mo><mn>1</mn>" +
      "</mrow></msup><mspace width='1.2em'></mspace><msub><mi>t</mi><mi>i</mi></msub><mo>=</mo><mfrac>" +
      "<mrow><mi>i</mi><mo>−</mo><mn>0,5</mn></mrow><mi>n</mi></mfrac></math>" +
      "<math display='block'><msub><mi>P</mi><mi>i</mi></msub><mo>=</mo><mi>P</mi><mo>·</mo><mfrac>" +
      "<msub><mi>w</mi><mi>i</mi></msub><mrow><mo>∑</mo><msub><mi>w</mi><mi>k</mi></msub></mrow></mfrac>" +
      "<mspace width='1.2em'></mspace><msub><mi>t</mi><mi>max</mi></msub><mo>=</mo><mfrac><mrow>" +
      "<mi>α</mi><mo>−</mo><mn>1</mn></mrow><mrow><mi>α</mi><mo>+</mo><mi>β</mi><mo>−</mo><mn>2</mn>" +
      "</mrow></mfrac><mspace width='0.6em'></mspace><mtext>dla</mtext><mspace width='0.4em'></mspace>" +
      "<mi>α</mi><mo>,</mo><mi>β</mi><mo>&gt;</mo><mn>1</mn></math>",
    vars: [
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text: "wysokość opadu w i-tym kroku",
        unit: "mm",
      },
      { symbol: "<math><msub><mi>w</mi><mi>i</mi></msub></math>", text: "waga kroku", unit: "–" },
      {
        symbol: "<math><msub><mi>t</mi><mi>i</mi></msub></math>",
        text: "środek i-tego kroku w czasie względnym (0–1); i = 1…n, n = ⌊D/Δt⌋",
        unit: "–",
      },
      {
        symbol: "<math><mi>α</mi></math>",
        text: "parametr kształtu ramienia wznoszącego, <code>alpha</code> &gt; 0; domyślnie 2",
        unit: "–",
      },
      {
        symbol: "<math><mi>β</mi></math>",
        text: "parametr kształtu ramienia opadającego, <code>beta</code> &gt; 0; domyślnie 5",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>max</mi></msub></math>",
        text: "położenie maksimum jako ułamek czasu trwania",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu, <code>total_mm</code>", unit: "mm" },
    ],
    note:
      "<p>Para (2; 5) daje wczesne maksimum, w 0,2 czasu trwania (opad konwekcyjny), (2; 2) symetryczne, " +
      "(5; 2) późne. Przy α ≤ 1 &lt; β największa wysokość jest w pierwszym kroku, przy β ≤ 1 &lt; α – w " +
      "ostatnim. Wczesny szczyt pada na zlewnię, w której straty nie są jeszcze pokryte, więc kulminacja " +
      "jest zwykle niższa i wcześniejsza.</p>",
    sources: "Chow i in. 1988; Wachulec i in. 2016; opis polecenia <code>precip hietogram</code>",
  },

  "rain-euler_ii": {
    title: "Hietogram Euler II (DVWK)",
    intro:
      "<p>Bloki naprzemienne: największy blok w położeniu p czasu trwania (domyślnie 0,33, ok. 1/3), " +
      "kolejne coraz mniejsze na przemian przed nim i po nim. Polecenie <code>precip hietogram</code>, w " +
      "hydrogramie <code>hietogram_type = euler_ii</code> z parametrem <code>peak_position</code>.</p>",
    formula:
      "<math display='block'><msub><mi>w</mi><mi>r</mi></msub><mo>=</mo><mfrac><msup><mi>r</mi><mrow>" +
      "<mo>−</mo><mn>0,7</mn></mrow></msup><mrow><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo>" +
      "<mn>1</mn></mrow><mi>n</mi></munderover><msup><mi>k</mi><mrow><mo>−</mo><mn>0,7</mn></mrow>" +
      "</msup></mrow></mfrac><mspace width='1.2em'></mspace><msub><mi>P</mi><mi>r</mi></msub><mo>=</mo>" +
      "<mi>P</mi><mo>·</mo><msub><mi>w</mi><mi>r</mi></msub></math>" +
      "<math display='block'><msub><mi>j</mi><mi>p</mi></msub><mo>=</mo><mi>max</mi><mrow><mo>(</mo>" +
      "<mn>2</mn><mo>,</mo><mrow><mo>⌊</mo><mi>n</mi><mo>·</mo><mi>p</mi><mo>⌋</mo></mrow><mo>+</mo>" +
      "<mn>1</mn><mo>)</mo></mrow></math>" +
      "<math display='block'><mi>r</mi><mo>:</mo><mspace width='0.6em'></mspace><mn>1</mn><mo>→</mo>" +
      "<msub><mi>j</mi><mi>p</mi></msub><mo>,</mo><mspace width='0.5em'></mspace><mn>2</mn><mo>→</mo>" +
      "<msub><mi>j</mi><mi>p</mi></msub><mo>−</mo><mn>1</mn><mo>,</mo><mspace width='0.5em'></mspace>" +
      "<mn>3</mn><mo>→</mo><msub><mi>j</mi><mi>p</mi></msub><mo>+</mo><mn>1</mn><mo>,</mo>" +
      "<mspace width='0.5em'></mspace><mn>4</mn><mo>→</mo><msub><mi>j</mi><mi>p</mi></msub><mo>−</mo>" +
      "<mn>2</mn><mo>,</mo><mspace width='0.5em'></mspace><mo>…</mo></math>",
    vars: [
      {
        symbol: "<math><msub><mi>w</mi><mi>r</mi></msub></math>",
        text: "udział bloku o randze r w sumie opadu",
        unit: "–",
      },
      {
        symbol: "<math><mi>r</mi></math>",
        text: "ranga bloku: 1 największy, n najmniejszy; n = ⌊D/Δt⌋",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>P</mi><mi>r</mi></msub></math>",
        text: "wysokość opadu bloku o randze r",
        unit: "mm",
      },
      {
        symbol: "<math><msub><mi>j</mi><mi>p</mi></msub></math>",
        text: "krok największego bloku",
        unit: "–",
      },
      {
        symbol: "<math><mi>p</mi></math>",
        text:
          "względne położenie maksimum, <code>peak_position</code>: 0 &lt; p &lt; 1 (bez końców); " +
          "domyślnie 0,33",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu, <code>total_mm</code>", unit: "mm" },
    ],
    note:
      "<p>Gdy po jednej stronie maksimum zabraknie kroków, pozostałe bloki idą po drugiej. To przybliżenie " +
      "hietogramu Eulera typu II: wagi bloków nie pochodzą z lokalnej krzywej wysokość–czas trwania, tylko " +
      "z zaniku r<sup>−0,7</sup>, a bloki leżą naprzemiennie, podczas gdy w Eulerze II kolejne co do " +
      "wielkości bloki wypełniają czas przed szczytem, a pozostałe leżą po nim. Rozkład DVWK z polskiej " +
      "metodyki (maksimum w środku czasu trwania) to inny hietogram.</p>",
    sources:
      "DVWK 1984; Chow i in. 1988; KZGW 2017; Malitz 2009; opis polecenia <code>precip hietogram</code>",
  },

  "rain-timestep": {
    title: "Krok czasowy Δt",
    intro:
      "<p>Krok <code>timestep_min</code> (domyślnie 5 min) jest wspólny dla hietogramu projektowego, " +
      "własnej serii, hydrogramu jednostkowego i wyniku; w hydrogramie jednostkowym jest też czasem " +
      "trwania opadu jednostkowego D. Czas trwania opadu nie może być krótszy niż Δt.</p>",
    formula:
      "<math display='block'><mi>n</mi><mo>=</mo><mrow><mo>⌊</mo><mfrac><mi>D</mi><mi>Δt</mi></mfrac>" +
      "<mo>⌋</mo></mrow><mspace width='1.5em'></mspace><msub><mi>t</mi><mi>i</mi></msub><mo>=</mo>" +
      "<mi>i</mi><mo>·</mo><mi>Δt</mi></math>" +
      "<math display='block'><msub><mi>Q</mi><mi>k</mi></msub><mo>=</mo><munderover><mo>∑</mo><mrow>" +
      "<mi>i</mi><mo>=</mo><mn>0</mn></mrow><mi>k</mi></munderover><msub><mi>P</mi><mrow><mi>e</mi>" +
      "<mo>,</mo><mi>i</mi></mrow></msub><mo>·</mo><msub><mi>u</mi><mrow><mi>k</mi><mo>−</mo><mi>i</mi>" +
      "</mrow></msub></math>",
    vars: [
      { symbol: "<math><mi>n</mi></math>", text: "liczba kroków hietogramu", unit: "–" },
      {
        symbol: "<math><mi>D</mi></math>",
        text: "czas trwania opadu, <code>duration_min</code>; D ≥ Δt",
        unit: "min",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy, <code>timestep_min</code> &gt; 0",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>i</mi></msub></math>",
        text: "koniec i-tego kroku hietogramu",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>Q</mi><mi>k</mi></msub></math>",
        text: "przepływ w chwili k·Δt od początku opadu",
        unit: "m³/s",
      },
      {
        symbol: "<math><msub><mi>P</mi><mrow><mi>e</mi><mo>,</mo><mi>i</mi></mrow></msub></math>",
        text: "opad efektywny w i-tym kroku (liczonym od 0)",
        unit: "mm",
      },
      {
        symbol: "<math><msub><mi>u</mi><mi>j</mi></msub></math>",
        text: "rzędna hydrogramu jednostkowego po j krokach",
        unit: "m³/s na 1 mm",
      },
    ],
    symbols: { timestep_min: "Δt", uh_time_to_peak_min: "tp" },
    note:
      "<p>Gdy D nie jest wielokrotnością Δt, hietogram ma ⌊D/Δt⌋ kroków i nie pokrywa końcówki czasu " +
      "trwania (uwaga w wyniku), choć cała suma P trafia do tych kroków. Mniejszy krok lepiej oddaje " +
      "szczyt: NEH 630 zaleca krok nie dłuższy niż część czasu do szczytu t<sub>p</sub> hydrogramu " +
      "jednostkowego (zakres wyżej), a w modelu Clarka Δt nie może przekraczać 2R. Czas do szczytu " +
      "odczytuje się z dokładnością do kroku.</p>",
    sources:
      "USDA-NRCS 2007 (NEH 630-16); Chow i in. 1988; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.3; " +
      "opis polecenia <code>hydrograph generate</code>",
  },
};
