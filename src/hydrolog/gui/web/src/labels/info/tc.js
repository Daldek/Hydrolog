/**
 * Explanations (i) of the time of concentration methods (plan D16, slice S3): the entries
 * "tc-<method>" for the six values of `tc_method` (`tc watershed --method`), in the format of
 * ui/info.js. They keep the symbols of the parameters only: the typical ranges, with their
 * sources, are Hydrolog's (`typical_ranges` of `tc watershed` and `hydrograph generate`),
 * registered by the sections that load those documents.
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
          "długość najdłuższej drogi spływu, wzdłuż cieku od przekroju zamykającego do najdalszego " +
          "punktu na dziale wodnym; ze zlewni <code>flow_path_length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text:
          "spadek tej drogi (nie w procentach): wysokość jej początku na dziale wodnym minus wysokość " +
          "przekroju, przez L; ze zlewni <code>flow_path_slope_m_per_m</code>",
        unit: "m/m",
      },
    ],
    symbols: { area_km2: "A", length_km: "L", slope_m_per_m: "S" },
    note:
      "<p>Poza zakresem danych metody Hydrolog liczy dalej i dodaje do wyniku uwagę. Ze zlewni bierze " +
      "tylko te dwa pola, bez wartości zastępczych. Dla spływu po stoku i korytem: Kerby–Kirpich.</p>",
    sources:
      "Kirpich 1940 (za Mota i Kobiyama 2015); Fang i in. 2005 (TxDOT 0-4696-1, wzór 3.14); Mota i " +
      "Kobiyama 2015; Roussel i in. 2005; USDA-NRCS 2010 (NEH 630-15); Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.1 i 3.7; opis polecenia <code>tc kirpich</code>",
  },

  "tc-nrcs": {
    title: "NRCS (NEH 630): czas koncentracji z równania opóźnienia",
    intro:
      "<p>Opóźnienie zlewni z równania NRCS (Mockus 1961; NEH 630, rozdz. 15, wzór 15-4) przeliczone " +
      "na czas koncentracji, t<sub>c</sub> = t<sub>lag</sub>/0,6; opór powierzchni zlewni ujmuje przez " +
      "CN. Polecenie <code>tc nrcs</code>, ze zlewni <code>tc watershed --method nrcs</code>; w " +
      "hydrogramie <code>tc_method = nrcs</code>.</p>",
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
          "długość spływu: najdłuższa droga spływu od działu wodnego do przekroju zamykającego, we " +
          "wzorze w metrach: 1000 × <code>flow_path_length_km</code>",
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
          "średni spadek terenu zlewni w procentach (100 × m/m), nie spadek drogi spływu; ze zlewni " +
          "<code>mean_slope_m_per_m</code>",
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
    symbols: { area_km2: "A", length_km: "L", slope_m_per_m: "Y", cn: "CN" },
    note:
      "<p>Wg NEH 630 równania nie stosuje się dla CN spoza zakresu metody. Y to średni spadek " +
      "terenu zlewni, nie spadek cieku ani drogi spływu: Hydrolog bierze go tylko z " +
      "<code>mean_slope_m_per_m</code>. Wynik to t<sub>c</sub>, nie t<sub>lag</sub> " +
      "(t<sub>lag</sub> = 0,6·t<sub>c</sub>).</p>",
    sources:
      "Mockus 1961 (za NEH 630-15); USDA-NRCS 2010 (NEH 630-15, wzór 15-4); Fang i in. 2005; " +
      "Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.7 i 3.7.1; opis polecenia " +
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
        text: "długość cieku głównego; ze zlewni <code>channel_length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><mi>ΔH</mi></math>",
        text:
          "wyniesienie średniej wysokości zlewni nad przekrój zamykający: <code>elevation_mean_m</code> − " +
          "<code>elevation_min_m</code>",
        unit: "m",
      },
    ],
    symbols: { area_km2: "A", length_km: "L", elevation_diff_m: "ΔH" },
    note:
      "<p>Kalibracja objęła duże zlewnie (bez informacji o użytych wezbraniach), więc zlewnie " +
      "mniejsze od nich leżą poza zakresem metody. Ze zlewni metoda bierze tylko te pola, bez " +
      "wartości zastępczych.</p>",
    sources:
      "Giandotti 1934 (za Grimaldi i in. 2012); Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.7; " +
      "opis polecenia <code>tc giandotti</code>",
  },

  "tc-faa": {
    title: "FAA: czas spływu powierzchniowego",
    intro:
      "<p>Metoda Federal Aviation Administration (1970, AC 150/5320-5B) do projektowania odwodnienia " +
      "lotnisk: czas spływu po powierzchni do wpustu, bez przepływu korytem. Polecenie <code>tc " +
      "faa</code>, ze zlewni <code>tc watershed --method faa</code>; w hydrogramie <code>tc_method = " +
      "faa</code>.</p>",
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
    symbols: { length_km: "L", slope_m_per_m: "S", runoff_coeff: "C" },
    note:
      "<p>Liczy tylko spływ po powierzchni na długości L; dla zlewni z korytem t<sub>c</sub> daje " +
      "Kerby–Kirpich albo Kirpich. Hydrolog nie bierze w miejsce brakujących pól długości ani spadku " +
      "cieku. Nomogram FAA obejmuje krótkie odcinki spływu; dłuższe liczy się wzorem.</p>",
    sources:
      "FAA 1970 (AC 150/5320-5B, rys. 7 i tabela I); Fang i in. 2005; Hydrolog, " +
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
    symbols: { area_km2: "A", length_km: "L", slope_m_per_m: "S", retardance: "N" },
    note:
      "<p>Zakres metody to dane Kerby’ego: bardzo małe zlewnie o małych spadkach i krótkim spływie " +
      "po stoku. Poprawka spadku poniżej 0,002 pochodzi od Clevelanda i in. (2012, TxDOT 0-6382-P1); " +
      "zakres sprawdza spadek przed poprawką. Wynik to czas spływu po stoku, nie t<sub>c</sub> zlewni " +
      "z korytem (wtedy Kerby–Kirpich).</p>",
    sources:
      "Kerby 1959 (za Roussel i in. 2005); Fang i in. 2005; Cleveland i in. 2012 (TxDOT 0-6382-P1); " +
      "TxDOT 2019; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.7; opis polecenia " +
      "<code>tc kerby</code>",
  },

  "tc-kerby_kirpich": {
    title: "Kerby–Kirpich: spływ po stoku i korytem",
    intro:
      "<p>Metoda złożona (Roussel i in. 2005) na najdłuższej drodze spływu: czas spływu po stoku " +
      "wzorem Kerby’ego plus czas przepływu korytem, czyli resztą tej drogi, wzorem Kirpicha ze " +
      "spadkiem całej drogi. Polecenie <code>tc kerby-kirpich</code>, ze zlewni " +
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
      "<math display='block'><msub><mi>L</mi><mi>k</mi></msub><mo>=</mo><mi>L</mi><mo>−</mo>" +
      "<msub><mi>L</mi><mi>sp</mi></msub><mspace width='1.2em'></mspace><msub><mi>S</mi><mi>k</mi>" +
      "</msub><mo>=</mo><mi>S</mi></math>" +
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
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość najdłuższej drogi spływu od działu wodnego do przekroju zamykającego, z odcinkiem po " +
          "stoku; ze zlewni <code>flow_path_length_km</code>, większa niż L<sub>sp</sub>",
        unit: "km",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text:
          "spadek całej tej drogi: wysokość jej początku na dziale wodnym minus wysokość przekroju, " +
          "przez L; ze zlewni <code>flow_path_slope_m_per_m</code>",
        unit: "m/m",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>k</mi></msub></math>",
        text:
          "długość odcinka korytem, najdłuższa droga spływu bez odcinka po stoku: " +
          "<code>flow_path_length_km</code> − <code>overland_length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>S</mi><mi>k</mi></msub></math>",
        text: "spadek odcinka korytem: spadek całej drogi spływu, <code>flow_path_slope_m_per_m</code>",
        unit: "m/m",
      },
    ],
    symbols: {
      area_km2: "A",
      overland_length_km: "L (stok)",
      overland_slope_m_per_m: "S (stok)",
      retardance: "N",
      flow_path_length_km: "L (droga spływu)",
      flow_path_slope_m_per_m: "S (droga spływu)",
    },
    note:
      "<p>Metoda wymaga wszystkich pięciu pól zlewni, bez wartości zastępczych. Zakres metody to dane " +
      "jej weryfikacji (92 zlewnie w Teksasie; długość i spadek całej drogi spływu, od przekroju do " +
      "działu wodnego) i dane Kerby’ego dla stoku. Poprawkę spadku poniżej 0,002 Hydrolog stosuje " +
      "osobno do stoku i do drogi spływu; zakresy sprawdzają spadki przed poprawką.</p>",
    sources:
      "Roussel i in. 2005 (TxDOT 0-4696-2, suplement); Cleveland i in. 2012 (TxDOT 0-6382-P1); Kerby " +
      "1959; Kirpich 1940; TxDOT 2019; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.7; opis " +
      "polecenia <code>tc kerby-kirpich</code>",
  },
};
