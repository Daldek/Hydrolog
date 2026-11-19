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
        text: "liczba kroków: w hietogramie D/Δt (D musi być wielokrotnością Δt), w serii liczba wartości",
        unit: "–",
      },
    ],
    note:
      "<p>Hydrogramowi przypisuje się p opadu, choć opad o danym p nie zawsze wywołuje wezbranie o tym " +
      "samym p. Własna seria daje hydrogram jednego zdarzenia, bez prawdopodobieństwa.</p>",
    guide: "metoda-rain-source",
    sources:
      "IMGW-PIB 2022 (PMAXTP, red. B. Ozga-Zieliński, s. 23); DVWK 1984 (za KZGW 2017); KZGW 2017; USGS 2018",
  },

  "rain-block": {
    title: "Hietogram blokowy",
    intro:
      "<p>Hietogram o stałym natężeniu przez cały czas trwania: każdy krok Δt dostaje tę samą wysokość " +
      "opadu. Nie ma parametrów kształtu.</p>",
    formula:
      "<math display='block'><msub><mi>P</mi><mi>i</mi></msub><mo>=</mo><mfrac><mi>P</mi><mi>n</mi>" +
      "</mfrac><mspace width='1.5em'></mspace><mi>n</mi><mo>=</mo><mfrac><mi>D</mi>" +
      "<mi>Δt</mi></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text: "wysokość opadu w i-tym kroku",
        unit: "mm",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba kroków; D musi być wielokrotnością Δt", unit: "–" },
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
      "<p>Hietogram trójkątny Yena i Chowa: natężenie rośnie liniowo od zera na początku opadu do " +
      "maksimum 2P/D w chwili r·D, potem liniowo maleje do zera na końcu. Każdy krok dostaje opad, który " +
      "spada w jego przedziale (całkę trójkąta), więc suma kroków to dokładnie P.</p>",
    formula:
      "<math display='block'><mi>F</mi><mo>(</mo><mi>u</mi><mo>)</mo><mo>=</mo><mfrac><msup><mi>u</mi>" +
      "<mn>2</mn></msup><mi>r</mi></mfrac><mspace width='0.6em'></mspace><mtext>dla</mtext>" +
      "<mspace width='0.4em'></mspace><mi>u</mi><mo>≤</mo><mi>r</mi></math>" +
      "<math display='block'><mi>F</mi><mo>(</mo><mi>u</mi><mo>)</mo><mo>=</mo><mn>1</mn><mo>−</mo>" +
      "<mfrac><msup><mrow><mo>(</mo><mn>1</mn><mo>−</mo><mi>u</mi><mo>)</mo></mrow><mn>2</mn></msup>" +
      "<mrow><mn>1</mn><mo>−</mo><mi>r</mi></mrow></mfrac><mspace width='0.6em'></mspace><mtext>dla</mtext>" +
      "<mspace width='0.4em'></mspace><mi>u</mi><mo>&gt;</mo><mi>r</mi></math>" +
      "<math display='block'><msub><mi>P</mi><mi>j</mi></msub><mo>=</mo><mi>P</mi><mo>·</mo><mrow>" +
      "<mo>[</mo><mi>F</mi><mo>(</mo><mfrac><mi>j</mi><mi>n</mi></mfrac><mo>)</mo><mo>−</mo><mi>F</mi>" +
      "<mo>(</mo><mfrac><mrow><mi>j</mi><mo>−</mo><mn>1</mn></mrow><mi>n</mi></mfrac><mo>)</mo><mo>]</mo>" +
      "</mrow><mspace width='1.2em'></mspace><mi>n</mi><mo>=</mo><mfrac><mi>D</mi><mi>Δt</mi></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>P</mi><mi>j</mi></msub></math>",
        text: "wysokość opadu w j-tym kroku",
        unit: "mm",
      },
      {
        symbol: "<math><mi>F</mi><mo>(</mo><mi>u</mi><mo>)</mo></math>",
        text: "część sumy, która spadła do chwili u·D (pole trójkąta od początku opadu)",
        unit: "–",
      },
      { symbol: "<math><mi>u</mi></math>", text: "czas względny t/D, 0–1", unit: "–" },
      {
        symbol: "<math><mi>j</mi></math>",
        text: "numer kroku, 1…n; D musi być wielokrotnością Δt",
        unit: "–",
      },
      {
        symbol: "<math><mi>r</mi></math>",
        text: "względne położenie maksimum (współczynnik r Yena i Chowa): 0 &lt; r &lt; 1 (bez końców); domyślnie 0,5",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
    ],
    note:
      "<p>Przy r = 0,5 i parzystym n dwa środkowe kroki są równe. Chow i in. (1988, tab. 14.3.2) podają " +
      "r od 0,29 do 0,48 dla miast USA, Indii i Kanady. Polska metodyka (za DVWK 1984) zaleca deszcz z " +
      "maksimum w środku czasu trwania.</p>",
    sources: "Yen i Chow 1980 (za Chow i in. 1988, rozdz. 14.3, s. 462–465); DVWK 1984 (za KZGW 2017)",
  },

  "rain-beta": {
    title: "Hietogram beta",
    intro:
      "<p>Hietogram beta: natężenie w czasie względnym ma kształt gęstości rozkładu beta o parametrach " +
      "kształtu α i β, a każdy krok dostaje opad, który spada w jego przedziale (różnicę dystrybuanty), " +
      "więc suma kroków to dokładnie P. Para α, β ustala położenie i ostrość maksimum.</p>",
    formula:
      "<math display='block'><msub><mi>P</mi><mi>i</mi></msub><mo>=</mo><mi>P</mi><mo>·</mo><mrow>" +
      "<mo>[</mo><msub><mi>I</mi><mrow><mi>i</mi><mo>/</mo><mi>n</mi></mrow></msub><mo>(</mo><mi>α</mi>" +
      "<mo>,</mo><mi>β</mi><mo>)</mo><mo>−</mo><msub><mi>I</mi><mrow><mo>(</mo><mi>i</mi><mo>−</mo>" +
      "<mn>1</mn><mo>)</mo><mo>/</mo><mi>n</mi></mrow></msub><mo>(</mo><mi>α</mi><mo>,</mo><mi>β</mi>" +
      "<mo>)</mo><mo>]</mo></mrow><mspace width='1.2em'></mspace><mi>n</mi><mo>=</mo><mfrac><mi>D</mi>" +
      "<mi>Δt</mi></mfrac></math>" +
      "<math display='block'><msub><mi>I</mi><mi>u</mi></msub><mo>(</mo><mi>α</mi><mo>,</mo><mi>β</mi>" +
      "<mo>)</mo><mo>=</mo><mfrac><mn>1</mn><mrow><mi>B</mi><mo>(</mo><mi>α</mi><mo>,</mo><mi>β</mi>" +
      "<mo>)</mo></mrow></mfrac><msubsup><mo>∫</mo><mn>0</mn><mi>u</mi></msubsup><msup><mi>x</mi><mrow>" +
      "<mi>α</mi><mo>−</mo><mn>1</mn></mrow></msup><msup><mrow><mo>(</mo><mn>1</mn><mo>−</mo><mi>x</mi>" +
      "<mo>)</mo></mrow><mrow><mi>β</mi><mo>−</mo><mn>1</mn></mrow></msup><mi>d</mi><mi>x</mi>" +
      "<mspace width='1.2em'></mspace><msub><mi>t</mi><mi>max</mi></msub><mo>=</mo><mfrac><mrow>" +
      "<mi>α</mi><mo>−</mo><mn>1</mn></mrow><mrow><mi>α</mi><mo>+</mo><mi>β</mi><mo>−</mo><mn>2</mn>" +
      "</mrow></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text: "wysokość opadu w i-tym kroku; i = 1…n, D musi być wielokrotnością Δt",
        unit: "mm",
      },
      {
        symbol: "<math><msub><mi>I</mi><mi>u</mi></msub><mo>(</mo><mi>α</mi><mo>,</mo><mi>β</mi><mo>)</mo></math>",
        text: "dystrybuanta rozkładu beta w czasie względnym u = t/D: część sumy, która spadła do chwili u·D",
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
          "położenie maksimum gęstości jako ułamek czasu trwania, dla α, β &gt; 1; przy α ≤ 1 &lt; β " +
          "maksimum jest na początku, przy β ≤ 1 &lt; α na końcu",
        unit: "–",
      },
      { symbol: "<math><mi>P</mi></math>", text: "suma opadu", unit: "mm" },
    ],
    note:
      "<p>Para (2; 5) daje maksimum wcześnie, w 0,2 czasu trwania, (2; 2) w środku, (5; 2) późno. " +
      "KZGW 2017 (rys. 2.7) pokazuje pary (1; 10), (2; 10), (6; 6) i (10; 2) i dobiera α, β tak, by szczyt " +
      "wezbrania był przepływem tego samego p. Wczesne maksimum pada, zanim straty są pokryte, więc " +
      "kulminacja jest zwykle niższa i wcześniejsza.</p>",
    sources: "KZGW 2017 (rozdz. II.3, wzory 2.20–2.22, s. 25; za Węglarczyk 1993)",
  },

  "rain-euler_ii": {
    title: "Deszcz Eulera typu II (ATV-DVWK-A 118)",
    intro:
      "<p>Deszcz modelowy zbudowany z krzywej wysokość–czas trwania h(D) jednego prawdopodobieństwa: " +
      "w tym GUI z tablicy PMAXTP IMGW-PIB dla wybranego p i metody. Bloki to przyrosty tej krzywej w " +
      "krokach Δt; największy leży w przedziale od 0,3·D, kolejne przed nim, reszta po nim.</p>",
    formula:
      "<math display='block'><mi>n</mi><mo>=</mo><mfrac><mi>D</mi><mi>Δt</mi></mfrac>" +
      "<mspace width='1.2em'></mspace><msub><mi>Δh</mi><mi>j</mi></msub><mo>=</mo><mi>h</mi><mo>(</mo>" +
      "<mi>j</mi><mi>Δt</mi><mo>)</mo><mo>−</mo><mi>h</mi><mo>(</mo><mo>(</mo><mi>j</mi><mo>−</mo>" +
      "<mn>1</mn><mo>)</mo><mi>Δt</mi><mo>)</mo><mo>,</mo><mspace width='0.5em'></mspace><mi>h</mi>" +
      "<mo>(</mo><mn>0</mn><mo>)</mo><mo>=</mo><mn>0</mn></math>" +
      "<math display='block'><mi>k</mi><mo>=</mo><mrow><mo>⌊</mo><mn>0,3</mn><mo>·</mo><mi>n</mi>" +
      "<mo>⌋</mo></mrow><mspace width='1.2em'></mspace><msub><mi>P</mi><mi>k</mi></msub><mo>=</mo>" +
      "<msub><mi>Δh</mi><mn>1</mn></msub><mo>,</mo><mspace width='0.5em'></mspace><msub><mi>P</mi>" +
      "<mrow><mi>k</mi><mo>−</mo><mi>i</mi></mrow></msub><mo>=</mo><msub><mi>Δh</mi><mrow><mi>i</mi>" +
      "<mo>+</mo><mn>1</mn></mrow></msub><mspace width='0.4em'></mspace><mtext>(i = 1…k)</mtext></math>" +
      "<math display='block'><msub><mi>P</mi><mrow><mi>k</mi><mo>+</mo><mi>i</mi></mrow></msub><mo>=</mo>" +
      "<msub><mi>Δh</mi><mrow><mi>k</mi><mo>+</mo><mi>i</mi><mo>+</mo><mn>1</mn></mrow></msub>" +
      "<mspace width='0.4em'></mspace><mtext>(i = 1…n−k−1)</mtext></math>",
    vars: [
      {
        symbol: "<math><mi>h</mi><mo>(</mo><mi>D</mi><mo>)</mo></math>",
        text:
          "wysokość opadu o czasie trwania D przy wybranym p (PMAXTP); czasy między punktami tablicy " +
          "(20, 25, 35, 40, 50, 55 min…) interpolowane liniowo względem ln D, bez ekstrapolacji",
        unit: "mm",
      },
      {
        symbol: "<math><mi>n</mi></math>",
        text: "liczba bloków; D musi być całkowitą wielokrotnością Δt",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>Δh</mi><mi>j</mi></msub></math>",
        text: "przyrost krzywej w j-tym kroku czasu trwania, j = 1…n",
        unit: "mm",
      },
      {
        symbol: "<math><mi>k</mi></math>",
        text: "blok szczytu liczony od 0: przedział od 0,3·D zaokrąglonego w dół do wielokrotności Δt",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>P</mi><mi>i</mi></msub></math>",
        text: "wysokość opadu bloku i (od 0) hietogramu",
        unit: "mm",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy; krzywa musi sięgać od Δt do D, a PMAXTP zaczyna się od 5 min, więc Δt ≥ 5 min",
        unit: "min",
      },
    ],
    note:
      "<p>Przyrosty idą w kolejności czasów trwania: dla krzywej IDF maleją, więc największy leży w " +
      "szczycie, kolejne co do wielkości przed nim (rosnąco), a reszta po nim (malejąco). Każde m bloków " +
      "wokół szczytu ma wysokość h(m·Δt): np. 15 min wokół szczytu ma wysokość PMAXTP dla 15 min, a cały " +
      "deszcz h(D), wysokość PMAXTP dla D. Położenia maksimum się nie podaje.</p>",
    guide: "metoda-rain-euler-ii",
    sources:
      "ATV-DVWK-A 118 (2001), kap. 5.2.2.1, za Thewes 2005 (praca dyplomowa, FH Trier, s. 10); Malitz 2009 " +
      "(DWD, Stark- und Extremniederschlag im Kurzzeitbereich, slajdy 17–19); Kaźmierczak i Kotowski 2012 " +
      "(PWr, s. 31–32)",
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
