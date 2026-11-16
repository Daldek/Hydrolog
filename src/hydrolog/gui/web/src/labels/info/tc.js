/**
 * Explanations (i) of the time of concentration methods, by Nogat DEV-15.14: the entries
 * "tc-<method>" for the six methods of tc (`tc_method`, `tc watershed --method`), in the format
 * of ui/info.js, each linking (`guide`) its subsection of the guide's chapter „Metody
 * obliczeń”. They keep the symbols of the parameters only: the typical ranges, with their
 * sources, are Hydrolog's (`typical_ranges` of `tc watershed` and `hydrograph generate`),
 * registered by the sections that load those documents.
 */

export const tcInfo = {
  "tc-kirpich": {
    title: "Kirpich (1940): czas koncentracji",
    intro:
      "<p>Czas dopływu wody do przekroju zamykającego z punktu zlewni najdalszego hydraulicznie. Wzór " +
      "empiryczny Kirpicha dla małych zlewni rolniczych z wyraźnym korytem liczy go z długości i spadku " +
      "najdłuższej drogi spływu.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>3,981</mn><mo>·</mo>" +
      "<msup><mi>L</mi><mn>0,77</mn></msup><mo>·</mo>" +
      "<msup><mi>S</mi><mrow><mo>−</mo><mn>0,385</mn></mrow></msup></math>",
    vars: [
      { symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>", text: "czas koncentracji", unit: "min" },
      {
        symbol: "<math><mi>L</mi></math>",
        text: "długość najdłuższej drogi spływu, od przekroju zamykającego do punktu najdalszego hydraulicznie",
        unit: "km",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text: "spadek tej drogi: różnica wysokości jej końców podzielona przez L",
        unit: "m/m",
      },
    ],
    symbols: { area_km2: "A", length_km: "L", slope_m_per_m: "S" },
    note:
      "<p>Dłuższa i łagodniejsza droga spływu daje dłuższy t<sub>c</sub>, a szczyt hydrogramu niższy i " +
      "późniejszy. Wzór ujmuje głównie przepływ korytem; spływ po stoku dodaje metoda Kerby–Kirpich.</p>",
    guide: "metoda-tc-kirpich",
    sources:
      "Kirpich 1940 (za Mota i Kobiyama 2015); Fang i in. 2005 (TxDOT 0-4696-1, wzór 3.14); Roussel i in. " +
      "2005; USDA-NRCS 2010 (NEH 630, rozdz. 15)",
  },

  "tc-nrcs": {
    title: "NRCS (NEH 630): czas koncentracji z równania opóźnienia",
    intro:
      "<p>Czas dopływu wody do przekroju zamykającego z punktu zlewni najdalszego hydraulicznie, wyznaczony " +
      "z opóźnienia zlewni równaniem NRCS: t<sub>c</sub> = t<sub>lag</sub>/0,6. Opór powierzchni zlewni " +
      "ujmuje w nim liczba krzywej CN.</p>",
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
        text: "czas koncentracji, t<sub>lag</sub>/0,6",
        unit: "min",
      },
      {
        symbol: "<math><mi>L</mi></math>",
        text: "długość najdłuższej drogi spływu, od punktu najdalszego hydraulicznie do przekroju zamykającego",
        unit: "m",
      },
      { symbol: "<math><mi>S</mi></math>", text: "retencja maksymalna zlewni; dla CN = 100: S = 0", unit: "mm" },
      {
        symbol: "<math><mi>Y</mi></math>",
        text: "średni spadek terenu zlewni w procentach, nie spadek cieku ani drogi spływu",
        unit: "%",
      },
      {
        symbol: "<math><mi>CN</mi></math>",
        text: "liczba krzywej odpływu dla AMC II; przeliczenie na AMC I lub III nie zmienia t<sub>c</sub>",
        unit: "–",
      },
    ],
    symbols: { area_km2: "A", length_km: "L", slope_m_per_m: "Y", cn: "CN" },
    note:
      "<p>Większy CN i większy spadek terenu skracają t<sub>c</sub>, dłuższa droga spływu go wydłuża. Wynik " +
      "to t<sub>c</sub>, nie t<sub>lag</sub>; dla CN spoza zakresu metody równania się nie stosuje, a wynik " +
      "ma wtedy uwagę.</p>",
    guide: "metoda-tc-nrcs",
    sources:
      "Mockus 1961 (za USDA-NRCS 2010); USDA-NRCS 2010 (NEH 630, rozdz. 15, wzór 15-4); Fang i in. 2005 " +
      "(TxDOT 0-4696-1)",
  },

  "tc-giandotti": {
    title: "Giandotti (1934): czas koncentracji",
    intro:
      "<p>Czas dopływu wody do przekroju zamykającego z punktu zlewni najdalszego hydraulicznie. Wzór " +
      "Giandottiego dla dużych zlewni liczy go z powierzchni zlewni, długości cieku głównego i wyniesienia " +
      "jej średniej wysokości nad przekrój.</p>",
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
      { symbol: "<math><mi>A</mi></math>", text: "powierzchnia zlewni", unit: "km²" },
      { symbol: "<math><mi>L</mi></math>", text: "długość cieku głównego", unit: "km" },
      {
        symbol: "<math><mi>ΔH</mi></math>",
        text: "wyniesienie średniej wysokości zlewni nad przekrój zamykający (najniższy punkt zlewni)",
        unit: "m",
      },
    ],
    symbols: { area_km2: "A", length_km: "L", elevation_diff_m: "ΔH" },
    note:
      "<p>Większa powierzchnia i dłuższy ciek wydłużają t<sub>c</sub>, większe wyniesienie go skraca. " +
      "Zlewnia mniejsza od zlewni włoskich, z których pochodzi wzór, daje wynik z uwagą.</p>",
    guide: "metoda-tc-giandotti",
    sources: "Giandotti 1934 (za Grimaldi i in. 2012)",
  },

  "tc-faa": {
    title: "FAA: czas spływu powierzchniowego",
    intro:
      "<p>Czas spływu wody po powierzchni terenu z najdalszego punktu do wpustu, bez przepływu korytem, " +
      "liczony wzorem Federal Aviation Administration do projektowania odwodnienia lotnisk.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>c</mi></msub><mo>=</mo><mn>22,213</mn><mo>·</mo>" +
      "<mrow><mo>(</mo><mn>1,1</mn><mo>−</mo><mi>C</mi><mo>)</mo></mrow><mo>·</mo>" +
      "<mfrac><msup><mi>L</mi><mn>0,5</mn></msup><msup><mi>S</mi><mrow><mn>1</mn><mo>/</mo><mn>3</mn>" +
      "</mrow></msup></mfrac></math>",
    vars: [
      { symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>", text: "czas spływu powierzchniowego", unit: "min" },
      { symbol: "<math><mi>C</mi></math>", text: "współczynnik spływu metody wymiernej, 0 &lt; C ≤ 1", unit: "–" },
      {
        symbol: "<math><mi>L</mi></math>",
        text: "długość spływu powierzchniowego, od najdalszego punktu do wpustu",
        unit: "km",
      },
      { symbol: "<math><mi>S</mi></math>", text: "średni spadek powierzchni spływu", unit: "m/m" },
    ],
    symbols: { length_km: "L", slope_m_per_m: "S", runoff_coeff: "C" },
    note:
      "<p>Dla zlewni z korytem wynik nie jest jej czasem koncentracji: ten daje Kerby–Kirpich albo Kirpich. " +
      "Większy współczynnik C, czyli powierzchnia mniej przepuszczalna, skraca czas spływu.</p>",
    guide: "metoda-tc-faa",
    sources: "FAA 1970 (AC 150/5320-5B, rys. 7 i tabela I); Fang i in. 2005 (TxDOT 0-4696-1)",
  },

  "tc-kerby": {
    title: "Kerby (1959): czas spływu po stoku",
    intro:
      "<p>Czas spływu wody cienką warstwą po powierzchni stoku do początku wyraźnego koryta. Wzór " +
      "Kerby’ego, wyprowadzony dla bardzo małych, płaskich zlewni, liczy go z długości i spadku stoku oraz " +
      "współczynnika oporu N.</p>",
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
        text: "długość spływu po stoku, do początku wyraźnego koryta",
        unit: "km",
      },
      {
        symbol: "<math><mi>N</mi></math>",
        text: "współczynnik oporu (retardacji) Kerby’ego: od 0,02 (gładka nawierzchnia) do 0,80 (gęsta trawa, las)",
        unit: "–",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text: "średni spadek stoku; poniżej 0,002 wzór bierze S + 0,0005",
        unit: "m/m",
      },
    ],
    symbols: { area_km2: "A", length_km: "L", slope_m_per_m: "S", retardance: "N" },
    note:
      "<p>Wynik to czas spływu po stoku, nie t<sub>c</sub> zlewni z korytem (ten daje Kerby–Kirpich). " +
      "Gęstsza roślinność (większe N) oraz dłuższy i łagodniejszy stok wydłużają czas spływu.</p>",
    guide: "metoda-tc-kerby",
    sources:
      "Kerby 1959 (za Roussel i in. 2005); Fang i in. 2005 (TxDOT 0-4696-1); Cleveland i in. 2012 (TxDOT " +
      "0-6382-P1); TxDOT 2019 (Hydraulic Design Manual, rozdz. 4)",
  },

  "tc-kerby_kirpich": {
    title: "Kerby–Kirpich: spływ po stoku i korytem",
    intro:
      "<p>Czas dopływu wody do przekroju zamykającego z punktu zlewni najdalszego hydraulicznie: suma czasu " +
      "spływu po stoku (wzór Kerby’ego) i czasu przepływu korytem resztą najdłuższej drogi spływu (wzór " +
      "Kirpicha ze spadkiem całej drogi).</p>",
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
        text: "długość spływu po stoku, od najdalszego punktu do początku wyraźnego koryta",
        unit: "km",
      },
      { symbol: "<math><msub><mi>S</mi><mi>sp</mi></msub></math>", text: "średni spadek stoku", unit: "m/m" },
      { symbol: "<math><mi>N</mi></math>", text: "współczynnik oporu (retardacji) Kerby’ego", unit: "–" },
      {
        symbol: "<math><mi>L</mi></math>",
        text: "długość najdłuższej drogi spływu, z odcinkiem po stoku; większa niż L<sub>sp</sub>",
        unit: "km",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text: "spadek całej tej drogi: różnica wysokości jej końców podzielona przez L",
        unit: "m/m",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>k</mi></msub></math>",
        text: "długość odcinka korytem: najdłuższa droga spływu bez odcinka po stoku",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>S</mi><mi>k</mi></msub></math>",
        text: "spadek odcinka korytem, równy spadkowi całej drogi spływu",
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
      "<p>Wynik to t<sub>c</sub> zlewni z korytem, nie sam spływ po stoku. Dłuższa i łagodniejsza droga " +
      "spływu oraz gęstsza roślinność na stoku (większe N) wydłużają t<sub>c</sub>.</p>",
    guide: "metoda-tc-kerby-kirpich",
    sources:
      "Roussel i in. 2005 (TxDOT 0-4696-2, suplement); Cleveland i in. 2012 (TxDOT 0-6382-P1); Kerby 1959; " +
      "Kirpich 1940; TxDOT 2019 (Hydraulic Design Manual, rozdz. 4)",
  },
};
