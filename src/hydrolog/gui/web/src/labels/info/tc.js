/**
 * Explanations (i) of the time of concentration methods (plan D16, slice S3): the entries
 * "tc-<method>" for the six values of `tc_method` (`tc watershed --method`), in the format of
 * ui/info.js. Their ranges hold Hydrolog's warning thresholds (OutsideTypicalRange in
 * hydrolog/time/concentration.py) and the data ranges of the methods.
 */

export const tcInfo = {
  "tc-kirpich": {
    title: "Kirpich (1940): czas koncentracji",
    intro:
      "<p>Wzór empiryczny dla małych zlewni rolniczych z wyraźnym korytem; opisuje głównie czas " +
      "przepływu korytem. Polecenie <code>tc kirpich</code>, ze zlewni <code>tc watershed --method " +
      "kirpich</code>; w hydrogramie <code>tc_method = kirpich</code>, metoda domyślna, gdy model " +
      "potrzebuje t<sub>c</sub>, a nie podano <code>tc_min</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>3,981</mn><mo>·</mo>" +
      "<msup><mi>L</mi><mn>0,77</mn></msup><mo>·</mo>" +
      "<msup><mi>S</mi><mrow><mo>−</mo><mn>0,385</mn></mrow></msup></math>",
    vars: [
      { symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>", text: "czas koncentracji", unit: "min" },
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość cieku głównego od działu wodnego do przekroju zamykającego; ze zlewni " +
          "<code>channel_length_km</code>, gdy brak: <code>length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text:
          "średni spadek cieku głównego (nie w procentach); ze zlewni <code>channel_slope_m_per_m</code>, " +
          "gdy brak: <code>mean_slope_m_per_m</code>, a bez obu: (<code>elevation_max_m</code> − " +
          "<code>elevation_min_m</code>) / (1000·L)",
        unit: "m/m",
      },
    ],
    ranges: [
      {
        option: "channel_length_km",
        label: "L",
        unit: "km",
        min: 0.001,
        max: 80,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "channel_slope_m_per_m",
        label: "S",
        unit: "m/m",
        min: 0.002,
        max: 0.15,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "area_km2",
        label: "A",
        unit: "km²",
        min: 0.004,
        max: 0.45,
        source: "dane Kirpicha: 7 małych zlewni rolniczych w Tennessee",
      },
      {
        option: "channel_slope_m_per_m",
        label: "S",
        unit: "m/m",
        min: 0.03,
        max: 0.1,
        source: "dane Kirpicha: spadki 3–10%",
      },
    ],
    note:
      "<p>Progi Hydrologu to nie zakres metody: poza nimi Hydrolog liczy dalej i dodaje do wyniku " +
      "uwagę. Bez pola zlewni wzór bierze wartość zastępczą i to ją Hydrolog sprawdza. Wg autora wzór " +
      "stosuje się do ok. 0,8 km² (200 akrów). Dla spływu po stoku i korytem: Kerby–Kirpich.</p>",
    sources:
      "Kirpich 1940 (za Roussel i in. 2005); Fang i in. 2005; USDA-NRCS 2010 (NEH 630-15); Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.1 i 3.7; opis polecenia <code>tc kirpich</code>",
  },

  "tc-nrcs": {
    title: "NRCS (TR-55): czas koncentracji z równania opóźnienia",
    intro:
      "<p>Opóźnienie zlewni z równania NRCS (Mockus 1961; NEH 630, rozdz. 15) przeliczone na czas " +
      "koncentracji, t<sub>c</sub> = t<sub>lag</sub>/0,6; opór powierzchni zlewni ujmuje przez CN. " +
      "Polecenie <code>tc nrcs</code>, ze zlewni <code>tc watershed --method nrcs</code>; w hydrogramie " +
      "<code>tc_method = nrcs</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>0,01416</mn><mo>·</mo>" +
      "<msup><mi>L</mi><mn>0,8</mn></msup><mo>·</mo>" +
      "<msup><mrow><mo>(</mo><mi>S</mi><mo>+</mo><mn>25,4</mn><mo>)</mo></mrow><mn>0,7</mn></msup>" +
      "<mo>·</mo><msup><mi>Y</mi><mrow><mo>−</mo><mn>0,5</mn></mrow></msup></math>" +
      "<math display='block'><mi>S</mi><mo>=</mo><mfrac><mn>25400</mn><mi>CN</mi></mfrac><mo>−</mo>" +
      "<mn>254</mn></math>",
    vars: [
      {
        symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>",
        text: "czas koncentracji (t<sub>lag</sub>/0,6)",
        unit: "min",
      },
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość drogi hydraulicznej (najdłuższej drogi spływu), we wzorze w metrach: 1000 × " +
          "<code>channel_length_km</code>, gdy brak: <code>length_km</code>",
        unit: "m",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text: "retencja maksymalna zlewni; dla CN = 100: S = 0",
        unit: "mm",
      },
      {
        symbol: "<math><mi>Y</mi></math>",
        text:
          "średni spadek terenu zlewni w procentach (100 × m/m); ze zlewni " +
          "<code>mean_slope_m_per_m</code>, gdy brak: <code>channel_slope_m_per_m</code>, a bez obu: " +
          "deniwelacja przez długość",
        unit: "%",
      },
      {
        symbol: "<math><mi>CN</mi></math>",
        text:
          "liczba krzywej dla AMC II: <code>cn</code> zlewni albo opcja <code>cn</code> hydrogramu, która " +
          "ją nadpisuje także tutaj; przeliczenie AMC nie zmienia t<sub>c</sub>",
        unit: "–",
      },
    ],
    ranges: [
      {
        option: "channel_length_km",
        label: "L",
        unit: "km",
        min: 0.03,
        max: 30,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "mean_slope_m_per_m",
        label: "Y",
        unit: "m/m",
        min: 0.001,
        max: 0.15,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "cn",
        label: "CN",
        unit: "",
        min: 50,
        max: 95,
        source: "próg ostrzeżenia Hydrologu, granica NEH 630",
      },
      {
        option: "area_km2",
        label: "A",
        unit: "km²",
        min: 0.005,
        max: 24,
        source: "dane równania: 24 zlewnie, w większości poniżej 8 km²",
      },
    ],
    note:
      "<p>Wg NEH 630 równania nie stosuje się dla CN poniżej 50 i powyżej 95; granice L i spadku to " +
      "progi Hydrologu, nie zakres metody. Y to średni spadek terenu zlewni, nie spadek cieku, dlatego " +
      "Hydrolog bierze najpierw <code>mean_slope_m_per_m</code>. Wynik to t<sub>c</sub>, nie " +
      "t<sub>lag</sub> (t<sub>lag</sub> = 0,6·t<sub>c</sub>).</p>",
    sources:
      "Mockus 1961 (za NEH 630-15); USDA-SCS 1986 (TR-55); USDA-NRCS 2010 (NEH 630-15); Fang i in. " +
      "2005; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.7 i 3.7.1; opis polecenia " +
      "<code>tc nrcs</code>",
  },

  "tc-giandotti": {
    title: "Giandotti (1934): czas koncentracji",
    intro:
      "<p>Wzór skalibrowany na dużych zlewniach włoskich; uwzględnia powierzchnię, długość cieku " +
      "głównego i wyniesienie średniej wysokości zlewni nad przekrój zamykający. Polecenie " +
      "<code>tc giandotti</code>, ze zlewni <code>tc watershed --method giandotti</code>; w hydrogramie " +
      "<code>tc_method = giandotti</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>60</mn><mo>·</mo>" +
      "<mfrac><mrow><mn>4</mn><mo>·</mo><msqrt><mi>A</mi></msqrt><mo>+</mo><mn>1,5</mn><mo>·</mo>" +
      "<mi>L</mi></mrow><mrow><mn>0,8</mn><mo>·</mo><msqrt><mi>ΔH</mi></msqrt></mrow></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>",
        text: "czas koncentracji (wzór daje godziny, stąd czynnik 60)",
        unit: "min",
      },
      { symbol: "<math><mi>A</mi></math>", text: "powierzchnia zlewni, <code>area_km2</code>", unit: "km²" },
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość cieku głównego; ze zlewni <code>channel_length_km</code>, gdy brak: " +
          "<code>length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><mi>ΔH</mi></math>",
        text:
          "wyniesienie średniej wysokości zlewni nad przekrój zamykający: <code>elevation_mean_m</code> − " +
          "<code>elevation_min_m</code>; bez <code>elevation_mean_m</code> średnia to środek przedziału, " +
          "(<code>elevation_min_m</code> + <code>elevation_max_m</code>)/2",
        unit: "m",
      },
    ],
    ranges: [
      {
        option: "area_km2",
        label: "A",
        unit: "km²",
        min: 100,
        max: 10000,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "channel_length_km",
        label: "L",
        unit: "km",
        min: 1,
        max: 300,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "area_km2",
        label: "A",
        unit: "km²",
        min: 170,
        max: 70000,
        source: "kalibracja Giandottiego: 12 zlewni we Włoszech",
      },
    ],
    note:
      "<p>Hydrolog ostrzega też, gdy ΔH jest poza 20–3000 m; ΔH to różnica dwóch pól zlewni, więc nie ma " +
      "go na liście zakresów. Kalibracja objęła zlewnie 170–70 000 km² (bez informacji o użytych " +
      "wezbraniach), więc mniejsze zlewnie leżą poza nią, choć próg Hydrologu zaczyna się od 100 km². " +
      "Bez pola zlewni wzór bierze wartość zastępczą i to ją Hydrolog sprawdza.</p>",
    sources:
      "Giandotti 1934 (za Grimaldi i in. 2012); Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.7; " +
      "opis polecenia <code>tc giandotti</code>",
  },

  "tc-faa": {
    title: "FAA: czas spływu powierzchniowego",
    intro:
      "<p>Metoda Federal Aviation Agency (1966) do projektowania odwodnienia lotnisk: czas spływu po " +
      "powierzchni do wpustu, bez przepływu korytem. Polecenie <code>tc faa</code>, ze zlewni " +
      "<code>tc watershed --method faa</code>; w hydrogramie <code>tc_method = faa</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>22,213</mn><mo>·</mo>" +
      "<mrow><mo>(</mo><mn>1,1</mn><mo>−</mo><mi>C</mi><mo>)</mo></mrow><mo>·</mo>" +
      "<mfrac><msup><mi>L</mi><mn>0,5</mn></msup><msup><mi>S</mi><mrow><mn>1</mn><mo>/</mo><mn>3</mn>" +
      "</mrow></msup></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>",
        text: "czas spływu powierzchniowego; dla zlewni z korytem to nie jest jej czas koncentracji",
        unit: "min",
      },
      {
        symbol: "<math><mi>C</mi></math>",
        text:
          "współczynnik spływu metody wymiernej, 0 &lt; C ≤ 1; ze zlewni <code>runoff_coeff</code> " +
          "(wymagany)",
        unit: "–",
      },
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość spływu powierzchniowego; ze zlewni <code>overland_length_km</code> (wymagana, nigdy " +
          "długość cieku)",
        unit: "km",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text:
          "średni spadek spływu powierzchniowego (nie w procentach); ze zlewni " +
          "<code>overland_slope_m_per_m</code> (wymagany)",
        unit: "m/m",
      },
    ],
    ranges: [
      {
        option: "overland_length_km",
        label: "L",
        unit: "km",
        min: 0.015,
        max: 3,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "overland_slope_m_per_m",
        label: "S",
        unit: "m/m",
        min: 0.005,
        max: 0.1,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "runoff_coeff",
        label: "C",
        unit: "",
        min: 0.1,
        max: 0.95,
        source: "próg ostrzeżenia Hydrologu",
      },
    ],
    note:
      "<p>Liczy tylko spływ po powierzchni na długości L; dla zlewni z korytem t<sub>c</sub> daje " +
      "Kerby–Kirpich albo Kirpich. Hydrolog nie bierze w miejsce brakujących pól długości ani spadku " +
      "cieku. Nomogram FAA obejmuje L do 0,24 km (800 ft), spadki 0,5–2,5% i C do 0,95; dłuższe odcinki " +
      "liczy się wzorem.</p>",
    sources:
      "FAA 1966 (AC 150/5320-5A); FAA 1970; FAA 2013 (AC 150/5320-5D); Fang i in. 2005; Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.7; opis polecenia <code>tc faa</code>",
  },

  "tc-kerby": {
    title: "Kerby (1959): czas spływu po stoku",
    intro:
      "<p>Wzór dla spływu płaskiego po powierzchni stoku w bardzo małych, płaskich zlewniach; zwykle " +
      "część stokowa metody Kerby–Kirpich. Polecenie <code>tc kerby</code>, ze zlewni " +
      "<code>tc watershed --method kerby</code>; w hydrogramie <code>tc_method = kerby</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>36,37</mn><mo>·</mo>" +
      "<msup><mrow><mo>(</mo><mi>L</mi><mo>·</mo><mi>N</mi><mo>)</mo></mrow><mn>0,467</mn></msup>" +
      "<mo>·</mo><msup><mi>S</mi><mrow><mo>−</mo><mn>0,2335</mn></mrow></msup></math>" +
      "<math display='block'><mtext>dla</mtext><mspace width='0.4em'></mspace><mi>S</mi><mo>&lt;</mo>" +
      "<mn>0,002</mn><mo>:</mo><mspace width='0.6em'></mspace><mi>S</mi><mo>→</mo><mi>S</mi><mo>+</mo>" +
      "<mn>0,0005</mn></math>",
    vars: [
      { symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>", text: "czas spływu po stoku", unit: "min" },
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość spływu po stoku do wyraźnego koryta; ze zlewni <code>overland_length_km</code> " +
          "(wymagana)",
        unit: "km",
      },
      {
        symbol: "<math><mi>N</mi></math>",
        text:
          "współczynnik oporu (retardacji) Kerby’ego; ze zlewni <code>retardance</code> (wymagany). " +
          "Typowo: 0,02 gładka nawierzchnia nieprzepuszczalna; 0,10 gładka, ubita, odkryta gleba; 0,20 " +
          "słaba trawa, uprawy rzędowe; 0,40 pastwisko, przeciętna trawa; 0,60 las liściasty; 0,80 gęsta " +
          "trawa, las iglasty, las liściasty z grubą ściółką",
        unit: "–",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text:
          "średni spadek stoku (nie w procentach); ze zlewni <code>overland_slope_m_per_m</code> " +
          "(wymagany); poniżej 0,002 wzór bierze S + 0,0005",
        unit: "m/m",
      },
    ],
    ranges: [
      {
        option: "overland_length_km",
        label: "L",
        unit: "km",
        min: 0.01,
        max: 0.366,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "overland_slope_m_per_m",
        label: "S",
        unit: "m/m",
        min: 0.001,
        max: 0.01,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "retardance",
        label: "N",
        unit: "",
        min: 0.02,
        max: 0.8,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "area_km2",
        label: "A",
        unit: "km²",
        max: 0.04,
        source: "dane Kerby’ego: zlewnie poniżej 10 akrów",
      },
    ],
    note:
      "<p>Dane Kerby’ego: zlewnie poniżej 0,04 km² (10 akrów), spadki poniżej 1%, spływ do 0,366 km " +
      "(1200 ft), N do 0,8; dolne granice L i spadku to progi Hydrologu. Poprawka spadku poniżej 0,002 " +
      "pochodzi od Clevelanda i in. (2012); zakres sprawdza spadek przed poprawką. Wynik to czas spływu " +
      "po stoku, nie t<sub>c</sub> zlewni z korytem (wtedy Kerby–Kirpich).</p>",
    sources:
      "Kerby 1959 (za Roussel i in. 2005); Fang i in. 2005; Cleveland i in. 2012; TxDOT 2019; Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.7; opis polecenia <code>tc kerby</code>",
  },

  "tc-kerby_kirpich": {
    title: "Kerby–Kirpich: spływ po stoku i korytem",
    intro:
      "<p>Metoda złożona (Roussel i in. 2005): czas spływu po stoku wzorem Kerby’ego plus czas " +
      "przepływu korytem wzorem Kirpicha. Polecenie <code>tc kerby-kirpich</code>, ze zlewni " +
      "<code>tc watershed --method kerby_kirpich</code>; w hydrogramie " +
      "<code>tc_method = kerby_kirpich</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><msub><mi>t</mi><mi>sp</mi></msub>" +
      "<mo>+</mo><msub><mi>t</mi><mi>k</mi></msub></math>" +
      "<math display='block'><msub><mi>t</mi><mi>sp</mi></msub><mo>=</mo><mn>36,37</mn><mo>·</mo>" +
      "<msup><mrow><mo>(</mo><msub><mi>L</mi><mi>sp</mi></msub><mo>·</mo><mi>N</mi><mo>)</mo></mrow>" +
      "<mn>0,467</mn></msup><mo>·</mo><msubsup><mi>S</mi><mi>sp</mi><mrow><mo>−</mo><mn>0,2335</mn>" +
      "</mrow></msubsup></math>" +
      "<math display='block'><msub><mi>t</mi><mi>k</mi></msub><mo>=</mo><mn>3,981</mn><mo>·</mo>" +
      "<msubsup><mi>L</mi><mi>k</mi><mn>0,77</mn></msubsup><mo>·</mo><msubsup><mi>S</mi><mi>k</mi>" +
      "<mrow><mo>−</mo><mn>0,385</mn></mrow></msubsup></math>" +
      "<math display='block'><mtext>dla</mtext><mspace width='0.4em'></mspace><msub><mi>S</mi><mi>sp</mi>" +
      "</msub><mo>,</mo><msub><mi>S</mi><mi>k</mi></msub><mo>&lt;</mo><mn>0,002</mn><mo>:</mo>" +
      "<mspace width='0.6em'></mspace><mi>S</mi><mo>→</mo><mi>S</mi><mo>+</mo><mn>0,0005</mn></math>",
    vars: [
      {
        symbol: "<math><msub><mi>t</mi><mi>sp</mi></msub></math>",
        text: "czas spływu po stoku (Kerby)",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>k</mi></msub></math>",
        text: "czas przepływu korytem (Kirpich)",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>sp</mi></msub></math>",
        text:
          "długość spływu po stoku od najdalszego punktu do początku wyraźnego koryta; ze zlewni " +
          "<code>overland_length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>S</mi><mi>sp</mi></msub></math>",
        text: "średni spadek stoku; ze zlewni <code>overland_slope_m_per_m</code>",
        unit: "m/m",
      },
      {
        symbol: "<math><mi>N</mi></math>",
        text: "współczynnik oporu (retardacji) Kerby’ego; ze zlewni <code>retardance</code>",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>k</mi></msub></math>",
        text:
          "długość koryta od jego początku do przekroju zamykającego, bez spływu po stoku; ze zlewni " +
          "<code>channel_length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>S</mi><mi>k</mi></msub></math>",
        text: "średni spadek koryta; ze zlewni <code>channel_slope_m_per_m</code>",
        unit: "m/m",
      },
    ],
    ranges: [
      {
        option: "overland_length_km",
        label: "L (stok)",
        unit: "km",
        min: 0.01,
        max: 0.366,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "overland_slope_m_per_m",
        label: "S (stok)",
        unit: "m/m",
        min: 0.001,
        max: 0.01,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "retardance",
        label: "N",
        unit: "",
        min: 0.02,
        max: 0.8,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "channel_length_km",
        label: "L (koryto)",
        unit: "km",
        min: 0.001,
        max: 80,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "channel_slope_m_per_m",
        label: "S (koryto)",
        unit: "m/m",
        min: 0.002,
        max: 0.15,
        source: "próg ostrzeżenia Hydrologu",
      },
      {
        option: "area_km2",
        label: "A",
        unit: "km²",
        min: 0.65,
        max: 388,
        source: "weryfikacja metody: 92 zlewnie w Teksasie",
      },
      {
        option: "channel_length_km",
        label: "L (koryto)",
        unit: "km",
        min: 1.6,
        max: 80,
        source: "weryfikacja metody: 92 zlewnie w Teksasie",
      },
      {
        option: "channel_slope_m_per_m",
        label: "S (koryto)",
        unit: "m/m",
        min: 0.002,
        max: 0.02,
        source: "weryfikacja metody: 92 zlewnie w Teksasie",
      },
    ],
    note:
      "<p>Metoda wymaga wszystkich pięciu pól zlewni. Hydrolog ostrzega osobno dla obu części: stok " +
      "według progów Kerby’ego, koryto według progów Kirpicha. Poprawkę spadku poniżej 0,002 stosuje " +
      "osobno do stoku i do koryta; zakresy sprawdzają spadki przed poprawką.</p>",
    sources:
      "Roussel i in. 2005; Cleveland i in. 2012; Kerby 1959; Kirpich 1940; TxDOT 2019; Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.7; opis polecenia <code>tc kerby-kirpich</code>",
  },
};
