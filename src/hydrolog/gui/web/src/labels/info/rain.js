/**
 * Explanations (i) of the rainfall of „Hydrogram zlewni” and Sieć (Nogat DEV-15.14): its source
 * ("rain-source"), the four design hyetographs ("rain-<type>": block, triangular, beta,
 * euler_ii) and the time step ("rain-timestep", whose range against the unit hydrograph's time
 * to peak is Hydrolog's: `typical_ranges` of `hydrograph generate`), in the format of
 * ui/info.js: a definition, the formula with its symbols and units, how to read the value and
 * the sources; an entry with a longer explanation links (`guide`) its subsection of the guide's
 * chapter „Metody obliczeń”.
 */

export const rainInfo = {
  "rain-source": {
    title: "Źródło opadu: PMAXTP, hietogram albo własna seria",
    intro:
      "<p>Opad, z którego liczy się odpływ: suma P o czasie trwania D rozłożona hietogramem projektowym " +
      "albo własna seria wysokości w krokach Δt. Sumę P podaje atlas PMAXTP IMGW-PIB dla punktu zlewni, " +
      "p i D albo wpisuje się ją wprost.</p>",
    formula:
      "<math display='block'><mi>T</mi><mo>=</mo><mfrac><mn>100</mn><mi>p</mi></mfrac>" +
      "<mspace width='1.5em'></mspace><mi>P</mi><mo>=</mo><munderover><mo>∑</mo><mrow><mi>i</mi>" +
      "<mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msub><mi>P</mi><mi>i</mi></msub></math>",
    vars: [
      {
        symbol: "<math><mi>p</mi></math>",
        text: "prawdopodobieństwo przewyższenia: szansa, że w danym roku opad o czasie D osiągnie lub przekroczy P",
        unit: "%",
      },
      { symbol: "<math><mi>T</mi></math>", text: "okres powtarzalności", unit: "lata" },
      {
        symbol: "<math><mi>P</mi></math>",
        text: "suma opadu: z atlasu, podana albo suma serii",
        unit: "mm",
      },
      {
        symbol: "<math><mi>D</mi></math>",
        text: "czas trwania opadu; w serii n·Δt",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text: "wysokość opadu w i-tym kroku (≥ 0), nie natężenie w mm/h",
        unit: "mm",
      },
      {
        symbol: "<math><mi>n</mi></math>",
        text: "liczba kroków: w hietogramie ⌊D/Δt⌋, w serii liczba wartości",
        unit: "–",
      },
    ],
    note:
      "<p>Hydrogramowi przypisuje się p opadu, choć opad o danym p nie zawsze wywołuje wezbranie o tym " +
      "samym p. Własna seria daje hydrogram jednego zdarzenia, bez prawdopodobieństwa.</p>",
    guide: "metoda-rain-source",
    sources: "IMGW-PIB 2022 (PMAXTP, red. B. Ozga-Zieliński); DVWK 1984 (za KZGW 2017); KZGW 2017; USGS 2018",
  },

  "rain-block": {
    title: "Hietogram blokowy",
    intro:
      "<p>Hietogram o stałym natężeniu przez cały czas trwania: każdy krok Δt dostaje tę samą wysokość " +
      "opadu. Nie ma parametrów kształtu.</p>",
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
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba kroków", unit: "–" },
      {
        symbol: "<math><mi>D</mi></math>",
        text: "czas trwania opadu",
        unit: "min",
      },
      { symbol: "<math><mi>Δt</mi></math>", text: "krok czasowy", unit: "min" },
    ],
    note:
      "<p>Choć opad w krokach jest stały, opad efektywny rośnie z kroku na krok: SCS-CN liczy go od sumy " +
      "narastającej, a pierwsze kroki pokrywają straty początkowe.</p>",
    sources: "Chow i in. 1988; KZGW 2017",
  },

  "rain-triangular": {
    title: "Hietogram trójkątny",
    intro:
      "<p>Hietogram trójkątny: wysokości opadu w krokach rosną liniowo do maksimum w położeniu p czasu " +
      "trwania, potem liniowo maleją.</p>",
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
        text: "numer kroku, 1…n, gdzie n = ⌊D/Δt⌋",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>j</mi><mi>p</mi></msub></math>",
        text: "krok maksimum; przy n = 1 cały opad przypada na jeden krok",
        unit: "–",
      },
      {
        symbol: "<math><mi>p</mi></math>",
        text: "względne położenie maksimum: 0 &lt; p &lt; 1 (bez końców); domyślnie 0,5",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
    ],
    note:
      "<p>Przy p = 0,5 i parzystym n maksimum wypada w kroku tuż po połowie czasu trwania (np. w 7. " +
      "z 12). Polska metodyka (za DVWK 1984) zaleca deszcz z maksimum w środku czasu trwania.</p>",
    sources: "KZGW 2017; DVWK 1984 (za KZGW 2017)",
  },

  "rain-beta": {
    title: "Hietogram beta",
    intro:
      "<p>Hietogram beta: wysokości opadu w krokach są proporcjonalne do gęstości rozkładu beta o parametrach " +
      "kształtu α i β, liczonej w środkach kroków. Para α, β ustala położenie i ostrość maksimum.</p>",
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
        text: "parametr kształtu ramienia wznoszącego, &gt; 0; domyślnie 2",
        unit: "–",
      },
      {
        symbol: "<math><mi>β</mi></math>",
        text: "parametr kształtu ramienia opadającego, &gt; 0; domyślnie 5",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>max</mi></msub></math>",
        text:
          "położenie maksimum jako ułamek czasu trwania; przy α ≤ 1 &lt; β pierwszy krok, przy β ≤ 1 &lt; α " +
          "ostatni",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
    ],
    note:
      "<p>Para (2; 5) daje maksimum wcześnie, w 0,2 czasu trwania (opad konwekcyjny), (2; 2) w środku, " +
      "(5; 2) późno. Wczesne maksimum pada, zanim straty są pokryte, więc kulminacja jest zwykle niższa i " +
      "wcześniejsza.</p>",
    sources: "Chow i in. 1988; Wachulec i in. 2016",
  },

  "rain-euler_ii": {
    title: "Hietogram Euler II (DVWK)",
    intro:
      "<p>Hietogram bloków naprzemiennych wzorowany na deszczu Eulera II (DVWK): największy blok w " +
      "położeniu p czasu trwania (domyślnie ok. 1/3), a kolejne coraz mniejsze na przemian przed nim i po nim.</p>",
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
        text: "względne położenie maksimum: 0 &lt; p &lt; 1 (bez końców); domyślnie 0,33",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
    ],
    note:
      "<p>Wysokości bloków maleją jak r<sup>−0,7</sup>, a nie według lokalnej krzywej wysokość–czas " +
      "trwania, więc hietogram tylko przybliża deszcz Eulera II. Gdy po jednej stronie zabraknie kroków, " +
      "reszta bloków idzie po drugiej.</p>",
    guide: "metoda-rain-euler-ii",
    sources: "DVWK 1984; Chow i in. 1988; KZGW 2017; Malitz 2009",
  },

  "rain-timestep": {
    title: "Krok czasowy Δt",
    intro:
      "<p>Krok czasowy obliczenia, wspólny dla opadu, hydrogramu jednostkowego i wyniku; w hydrogramie " +
      "jednostkowym jest zarazem czasem trwania opadu jednostkowego. Czas trwania opadu D nie może być " +
      "krótszy niż Δt.</p>",
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
        text: "czas trwania opadu; D ≥ Δt",
        unit: "min",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy, &gt; 0",
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
      "<p>Krótszy krok lepiej oddaje szczyt; krok dłuższy niż część czasu do szczytu t<sub>p</sub> " +
      "hydrogramu jednostkowego (zakres wyżej) go spłaszcza. Czas do szczytu odczytuje się z dokładnością " +
      "do kroku.</p>",
    guide: "metoda-rain-timestep",
    sources: "USDA-NRCS 2007 (NEH 630-16); Chow i in. 1988",
  },
};
