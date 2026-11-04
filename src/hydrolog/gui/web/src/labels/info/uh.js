/**
 * Explanations (i) of the unit hydrograph models (plan D16, slice S3): the entries "uh-<model>"
 * for the four values of `uh_model` of `hydrograph generate` (SCS, Nash with the Lutz method of
 * `uh nash`, Clark, Snyder), in the format of ui/info.js. They keep the symbols of the
 * parameters only: the typical ranges, with their sources, are Hydrolog's (`typical_ranges`
 * of `hydrograph generate` and, for Lutz, of `uh nash`).
 */

export const uhInfo = {
  "uh-scs": {
    title: "Hydrogram jednostkowy SCS (NRCS)",
    intro:
      "<p>Bezwymiarowy hydrogram NRCS (tablica 33 punktów q/q<sub>p</sub> od t/t<sub>p</sub>, do " +
      "5·t<sub>p</sub>; Mockus 1957), skalowany czasem do szczytu t<sub>p</sub> i przepływem " +
      "szczytowym q<sub>p</sub>. Polecenie <code>uh scs</code>, w hydrogramie <code>uh_model = scs</code> " +
      "(domyślny); wymaga t<sub>c</sub>: <code>tc_min</code> albo metody <code>tc_method</code>.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>lag</mi></msub><mo>=</mo><mn>0,6</mn><mo>·</mo>" +
      "<msub><mi>t</mi><mi>c</mi></msub><mspace width='1.2em'></mspace><msub><mi>t</mi><mi>p</mi></msub>" +
      "<mo>=</mo><mfrac><mi>Δt</mi><mn>2</mn></mfrac><mo>+</mo><msub><mi>t</mi><mi>lag</mi></msub>" +
      "<mspace width='1.2em'></mspace><msub><mi>q</mi><mi>p</mi></msub><mo>=</mo><mn>0,208</mn><mo>·</mo>" +
      "<mfrac><mi>A</mi><msub><mi>t</mi><mi>p</mi></msub></mfrac></math>" +
      "<math display='block'><mi>u</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow><mo>=</mo>" +
      "<msub><mi>q</mi><mi>p</mi></msub><mo>·</mo><mi>φ</mi><mrow><mo>(</mo><mfrac><mi>t</mi>" +
      "<msub><mi>t</mi><mi>p</mi></msub></mfrac><mo>)</mo></mrow><mo>,</mo><mspace width='1em'></mspace>" +
      "<mn>0</mn><mo>≤</mo><mfrac><mi>t</mi><msub><mi>t</mi><mi>p</mi></msub></mfrac><mo>≤</mo><mn>5</mn></math>",
    vars: [
      {
        symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>",
        text: "czas koncentracji (krok 2): <code>tc_min</code> albo z metody <code>tc_method</code>",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>lag</mi></msub></math>",
        text: "opóźnienie: od środka ciężkości opadu efektywnego do szczytu",
        unit: "min",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy <code>timestep_min</code>, zarazem czas trwania opadu jednostkowego",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>p</mi></msub></math>",
        text: "czas do szczytu hydrogramu jednostkowego (we wzorze na q<sub>p</sub> w godzinach)",
        unit: "min",
      },
      { symbol: "<math><mi>A</mi></math>", text: "powierzchnia zlewni, <code>area_km2</code>", unit: "km²" },
      {
        symbol: "<math><msub><mi>q</mi><mi>p</mi></msub></math>",
        text: "przepływ szczytowy hydrogramu jednostkowego",
        unit: "m³/s na 1 mm",
      },
      {
        symbol: "<math><mi>φ</mi></math>",
        text: "rzędna q/q<sub>p</sub> tablicy NRCS dla t/t<sub>p</sub>, interpolowana liniowo; poza tablicą 0",
        unit: "–",
      },
    ],
    symbols: { area_km2: "A" },
    note:
      "<p>Krok Δt ma swój zakres względem t<sub>p</sub> (objaśnienie kroku czasowego). Każda metoda " +
      "t<sub>c</sub> nadaje się do SCS, przy czym FAA i Kerby tylko dla małych zlewni bez wyraźnego " +
      "koryta (dają czas spływu po stoku).</p>",
    sources:
      "Mockus 1957 (za NEH 630-16); USDA-SCS 1986 (TR-55); USDA-NRCS 2007 (NEH 630-16); Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.1; opis polecenia <code>uh scs</code>",
  },

  "uh-nash": {
    title: "Nash: kaskada zbiorników liniowych",
    intro:
      "<p>Zlewnia jako n jednakowych zbiorników liniowych o stałej K, połączonych szeregowo (Nash 1957). " +
      "W hydrogramie <code>uh_model = nash</code> z <code>nash_n</code> i <code>nash_k_min</code>: " +
      "podanymi (skalibrowanymi) albo policzonymi metodą Lutza przez <code>uh nash</code> z pól zlewni; " +
      "t<sub>c</sub> nie jest używany.</p>",
    formula:
      "<math display='block'><mi>u</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow><mo>=</mo><mfrac>" +
      "<mn>1</mn><mrow><mi>K</mi><mo>·</mo><mi mathvariant='normal'>Γ</mi><mrow><mo>(</mo><mi>n</mi>" +
      "<mo>)</mo></mrow></mrow></mfrac><mo>·</mo><msup><mrow><mo>(</mo><mfrac><mi>t</mi><mi>K</mi>" +
      "</mfrac><mo>)</mo></mrow><mrow><mi>n</mi><mo>−</mo><mn>1</mn></mrow></msup><mo>·</mo>" +
      "<msup><mi>e</mi><mrow><mo>−</mo><mi>t</mi><mo>/</mo><mi>K</mi></mrow></msup></math>" +
      "<math display='block'><msub><mi>t</mi><mi>lag</mi></msub><mo>=</mo><mi>n</mi><mo>·</mo><mi>K</mi>" +
      "</math>" +
      "<math display='block'><msub><mi>t</mi><mi>p</mi></msub><mo>=</mo><msub><mi>P</mi><mn>1</mn></msub>" +
      "<mo>·</mo><msup><mrow><mo>(</mo><mfrac><mrow><mi>L</mi><mo>·</mo><msub><mi>L</mi><mi>c</mi></msub>" +
      "</mrow><msup><mi>J</mi><mn>1,5</mn></msup></mfrac><mo>)</mo></mrow><mn>0,26</mn></msup><mo>·</mo>" +
      "<msup><mi>e</mi><mrow><mo>−</mo><mn>0,016</mn><mo>·</mo><mi>U</mi></mrow></msup><mo>·</mo>" +
      "<msup><mi>e</mi><mrow><mn>0,004</mn><mo>·</mo><mi>W</mi></mrow></msup></math>" +
      "<math display='block'><msub><mi>P</mi><mn>1</mn></msub><mo>=</mo><mn>3,989</mn><mo>·</mo>" +
      "<msub><mi>n</mi><mi>M</mi></msub><mo>+</mo><mn>0,028</mn><mspace width='1.2em'></mspace>" +
      "<msub><mi>u</mi><mi>p</mi></msub><mo>=</mo><mfrac><mn>0,66</mn><msubsup><mi>t</mi><mi>p</mi>" +
      "<mn>1,04</mn></msubsup></mfrac></math>" +
      "<math display='block'><msub><mi>t</mi><mi>p</mi></msub><mo>·</mo><msub><mi>u</mi><mi>p</mi></msub>" +
      "<mo>=</mo><mfrac><mrow><msup><mrow><mo>(</mo><mi>n</mi><mo>−</mo><mn>1</mn><mo>)</mo></mrow>" +
      "<mi>n</mi></msup><mo>·</mo><msup><mi>e</mi><mrow><mo>−</mo><mrow><mo>(</mo><mi>n</mi><mo>−</mo>" +
      "<mn>1</mn><mo>)</mo></mrow></mrow></msup></mrow><mrow><mi mathvariant='normal'>Γ</mi><mrow>" +
      "<mo>(</mo><mi>n</mi><mo>)</mo></mrow></mrow></mfrac><mspace width='1.2em'></mspace><mi>K</mi>" +
      "<mo>=</mo><mfrac><msub><mi>t</mi><mi>p</mi></msub><mrow><mi>n</mi><mo>−</mo><mn>1</mn></mrow>" +
      "</mfrac></math>",
    vars: [
      {
        symbol: "<math><mi>n</mi></math>",
        text: "liczba zbiorników (parametr kształtu, może być ułamkowa), <code>nash_n</code>",
        unit: "–",
      },
      {
        symbol: "<math><mi>K</mi></math>",
        text: "stała magazynowania zbiornika, <code>nash_k_min</code>",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>lag</mi></msub></math>",
        text:
          "opóźnienie: środek ciężkości hydrogramu chwilowego, wynik kaskady, nie założenie; szczyt " +
          "hydrogramu chwilowego wypada w (n − 1)·K dla n &gt; 1",
        unit: "min",
      },
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "Lutz: długość cieku głównego od działu wodnego do przekroju zamykającego; ze zlewni " +
          "<code>channel_length_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>c</mi></msub></math>",
        text:
          "Lutz: długość cieku od przekroju do punktu najbliższego środka ciężkości zlewni, nie większa " +
          "niż L; ze zlewni <code>Lc_km</code>",
        unit: "km",
      },
      {
        symbol: "<math><mi>J</mi></math>",
        text: "Lutz: średni spadek cieku głównego; ze zlewni <code>channel_slope_m_per_m</code>",
        unit: "m/m",
      },
      {
        symbol: "<math><msub><mi>n</mi><mi>M</mi></msub></math>",
        text:
          "Lutz: współczynnik szorstkości Manninga koryta; ze zlewni <code>manning_n</code>",
        unit: "s·m^(−1/3)",
      },
      {
        symbol: "<math><mi>U</mi></math>",
        text: "Lutz: udział terenów zurbanizowanych; ze zlewni <code>urban_pct</code>, bez niego 0",
        unit: "%",
      },
      {
        symbol: "<math><mi>W</mi></math>",
        text: "Lutz: udział lasów; ze zlewni <code>forest_pct</code>, bez niego 0",
        unit: "%",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>p</mi></msub></math>",
        text:
          "Lutz: czas do szczytu hydrogramu chwilowego; K = t<sub>p</sub>/(n − 1) wychodzi w godzinach, " +
          "Hydrolog podaje je w minutach",
        unit: "h",
      },
      {
        symbol: "<math><msub><mi>u</mi><mi>p</mi></msub></math>",
        text: "Lutz: rzędna szczytu hydrogramu chwilowego",
        unit: "1/h",
      },
    ],
    symbols: { n: "n", k_min: "K", area_km2: "A (Lutz)" },
    note:
      "<p>Zalecane: n i K skalibrowane albo z metody Lutza (zlewnie niekontrolowane). n i K z " +
      "t<sub>c</sub> przez t<sub>lag</sub> = 0,6·t<sub>c</sub> to założenie hydrogramu SCS, nie modelu " +
      "Nasha; Hydrolog oznacza tę drogę jako przestarzałą i hydrogram jej nie oferuje. Metoda Lutza " +
      "wymaga L, L<sub>c</sub> ≤ L, J i n<sub>M</sub> (U i W domyślnie 0); n szuka w przedziale 1,1–20, " +
      "a bez rozwiązania kończy się błędem. KZGW 2017 podaje ją dla niekontrolowanych zlewni " +
      "quasi-naturalnych (o małym uszczelnieniu) jako alternatywę dla modelu Snydera. Hydrogram " +
      "jednostkowy dla kroku Δt powstaje z krzywej S hydrogramu chwilowego i jest skalowany " +
      "powierzchnią A.</p>",
    sources:
      "Nash 1957; Lutz 1984 (za KZGW 2017); KZGW 2017; Chow i in. 1988; Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.2 i 5.1; opis polecenia <code>uh nash</code>",
  },

  "uh-clark": {
    title: "Clark: translacja i zbiornik liniowy",
    intro:
      "<p>Hydrogram chwilowy Clarka (1945): translacja przez krzywą czas–powierzchnia zlewni eliptycznej " +
      "(HEC-HMS), potem zbiornik liniowy o stałej retencji R. Polecenie <code>uh clark</code>, w " +
      "hydrogramie <code>uh_model = clark</code>; wymaga t<sub>c</sub> (czasu translacji) oraz " +
      "<code>clark_r_min</code> albo <code>clark_r_tc_ratio</code>.</p>",
    formula:
      "<math display='block'><msub><mi>A</mi><mi>cum</mi></msub><mo>=</mo><mn>1,414</mn><mo>·</mo>" +
      "<msup><mi>τ</mi><mn>1,5</mn></msup><mspace width='0.6em'></mspace><mtext>dla</mtext>" +
      "<mspace width='0.4em'></mspace><mi>τ</mi><mo>≤</mo><mn>0,5</mn><mo>,</mo>" +
      "<mspace width='1.2em'></mspace><mi>τ</mi><mo>=</mo><mfrac><mi>t</mi><msub><mi>t</mi><mi>c</mi>" +
      "</msub></mfrac></math>" +
      "<math display='block'><msub><mi>A</mi><mi>cum</mi></msub><mo>=</mo><mn>1</mn><mo>−</mo>" +
      "<mn>1,414</mn><mo>·</mo><msup><mrow><mo>(</mo><mn>1</mn><mo>−</mo><mi>τ</mi><mo>)</mo></mrow>" +
      "<mn>1,5</mn></msup><mspace width='0.6em'></mspace><mtext>dla</mtext>" +
      "<mspace width='0.4em'></mspace><mn>0,5</mn><mo>&lt;</mo><mi>τ</mi><mo>&lt;</mo><mn>1</mn></math>" +
      "<math display='block'><msub><mi>A</mi><mi>cum</mi></msub><mo>=</mo><mn>1</mn>" +
      "<mspace width='0.6em'></mspace><mtext>dla</mtext><mspace width='0.4em'></mspace><mi>τ</mi>" +
      "<mo>≥</mo><mn>1</mn></math>" +
      "<math display='block'><msub><mi>O</mi><mi>i</mi></msub><mo>=</mo><msub><mi>O</mi><mrow><mi>i</mi>" +
      "<mo>−</mo><mn>1</mn></mrow></msub><mo>+</mo><msub><mi>C</mi><mn>1</mn></msub><mo>·</mo><mrow>" +
      "<mo>(</mo><msub><mi>I</mi><mi>i</mi></msub><mo>+</mo><msub><mi>I</mi><mrow><mi>i</mi><mo>−</mo>" +
      "<mn>1</mn></mrow></msub><mo>−</mo><mn>2</mn><mo>·</mo><msub><mi>O</mi><mrow><mi>i</mi><mo>−</mo>" +
      "<mn>1</mn></mrow></msub><mo>)</mo></mrow></math>" +
      "<math display='block'><msub><mi>C</mi><mn>1</mn></msub><mo>=</mo><mfrac><mi>Δt</mi><mrow>" +
      "<mn>2</mn><mo>·</mo><mi>R</mi><mo>+</mo><mi>Δt</mi></mrow></mfrac></math>",
    vars: [
      {
        symbol: "<math><msub><mi>t</mi><mi>c</mi></msub></math>",
        text: "czas koncentracji, w modelu Clarka czas translacji (krok 2)",
        unit: "min",
      },
      {
        symbol: "<math><mi>τ</mi></math>",
        text: "czas względny t/t<sub>c</sub>",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>A</mi><mi>cum</mi></msub></math>",
        text: "skumulowany udział powierzchni zlewni, z której woda dotarła do przekroju",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>I</mi><mi>i</mi></msub><mo>,</mo><msub><mi>O</mi><mi>i</mi></msub></math>",
        text:
          "dopływ do zbiornika (przyrosty A<sub>cum</sub> w krokach) i odpływ z niego w i-tym kroku; " +
          "odpływ jest normowany do objętości 1",
        unit: "–",
      },
      {
        symbol: "<math><mi>R</mi></math>",
        text:
          "stała retencji zbiornika liniowego (S = R·O): <code>clark_r_min</code> albo " +
          "<code>clark_r_tc_ratio</code> · t<sub>c</sub>",
        unit: "min",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy <code>timestep_min</code>, zarazem czas trwania opadu jednostkowego; najwyżej 2R",
        unit: "min",
      },
    ],
    symbols: { r_tc_ratio: "R/tc" },
    note:
      "<p>R/t<sub>c</sub> jest małe w zlewniach stromych i zurbanizowanych (mała retencja), duże w " +
      "płaskich i podmokłych (duża retencja); źródło zakresu podaje te klasy. Krok Δt dłuższy niż " +
      "2R dałby ujemne rzędne, więc Hydrolog zgłasza błąd. Hydrogram jednostkowy dla kroku Δt " +
      "powstaje z krzywej S hydrogramu chwilowego. Każda metoda t<sub>c</sub> nadaje się do modelu " +
      "Clarka; FAA i Kerby – tylko dla małych zlewni bez wyraźnego koryta.</p>",
    sources:
      "Clark 1945; USACE, HEC-HMS Technical Reference Manual; Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.3; opis polecenia <code>uh clark</code>",
  },

  "uh-snyder": {
    title: "Snyder: syntetyczny hydrogram jednostkowy",
    intro:
      "<p>Opóźnienie i szczyt z długości cieku i położenia środka ciężkości zlewni (Snyder 1938), z " +
      "własnym równaniem opóźnienia. Polecenie <code>uh snyder</code>, w hydrogramie " +
      "<code>uh_model = snyder</code> z opcjami <code>snyder_*</code>; t<sub>c</sub> nie jest używany.</p>",
    formula:
      "<math display='block'><msub><mi>t</mi><mi>L</mi></msub><mo>=</mo><msub><mi>C</mi><mi>t</mi>" +
      "</msub><mo>·</mo><msup><mrow><mo>(</mo><mi>L</mi><mo>·</mo><msub><mi>L</mi><mi>c</mi></msub>" +
      "<mo>)</mo></mrow><mn>0,3</mn></msup><mspace width='1.2em'></mspace><msub><mi>t</mi><mi>D</mi>" +
      "</msub><mo>=</mo><mfrac><msub><mi>t</mi><mi>L</mi></msub><mn>5,5</mn></mfrac></math>" +
      "<math display='block'><msub><mi>t</mi><mi>LR</mi></msub><mo>=</mo><msub><mi>t</mi><mi>L</mi></msub>" +
      "<mo>+</mo><mn>0,25</mn><mo>·</mo><mrow><mo>(</mo><mi>Δt</mi><mo>−</mo><msub><mi>t</mi><mi>D</mi>" +
      "</msub><mo>)</mo></mrow><mspace width='1.2em'></mspace><msub><mi>t</mi><mi>pR</mi></msub><mo>=</mo>" +
      "<msub><mi>t</mi><mi>LR</mi></msub><mo>+</mo><mfrac><mi>Δt</mi><mn>2</mn></mfrac></math>" +
      "<math display='block'><msub><mi>q</mi><mi>pR</mi></msub><mo>=</mo><mn>0,275</mn><mo>·</mo>" +
      "<msub><mi>C</mi><mi>p</mi></msub><mo>·</mo><mfrac><mi>A</mi><msub><mi>t</mi><mi>LR</mi></msub>" +
      "</mfrac><mspace width='1.2em'></mspace><msub><mi>t</mi><mi>b</mi></msub><mo>=</mo><mn>0,556</mn>" +
      "<mo>·</mo><mfrac><mi>A</mi><msub><mi>q</mi><mi>pR</mi></msub></mfrac></math>",
    vars: [
      {
        symbol: "<math><mi>L</mi></math>",
        text:
          "długość cieku głównego od działu wodnego do przekroju zamykającego, " +
          "<code>snyder_length_km</code>; w GUI puste pole bierze <code>channel_length_km</code> zlewni",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>c</mi></msub></math>",
        text:
          "długość cieku od przekroju do punktu najbliższego środka ciężkości zlewni, " +
          "<code>snyder_centroid_length_km</code>; w GUI puste pole bierze <code>Lc_km</code> zlewni",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>C</mi><mi>t</mi></msub></math>",
        text: "współczynnik czasowy w postaci metrycznej, <code>snyder_ct</code>; domyślnie 1,5",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>C</mi><mi>p</mi></msub></math>",
        text: "współczynnik szczytowy, <code>snyder_cp</code>; domyślnie 0,6",
        unit: "–",
      },
      { symbol: "<math><msub><mi>t</mi><mi>L</mi></msub></math>", text: "opóźnienie zlewni", unit: "h" },
      {
        symbol: "<math><msub><mi>t</mi><mi>D</mi></msub></math>",
        text: "standardowy czas trwania opadu",
        unit: "h",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text:
          "krok czasowy <code>timestep_min</code>, we wzorach w godzinach; w hydrogramie czas trwania " +
          "opadu jednostkowego D = Δt",
        unit: "h",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>LR</mi></msub><mo>,</mo><msub><mi>t</mi><mi>pR</mi></msub></math>",
        text: "opóźnienie i czas do szczytu dla D = Δt",
        unit: "h",
      },
      { symbol: "<math><mi>A</mi></math>", text: "powierzchnia zlewni, <code>area_km2</code>", unit: "km²" },
      {
        symbol: "<math><msub><mi>q</mi><mi>pR</mi></msub></math>",
        text: "przepływ szczytowy dla D = Δt",
        unit: "m³/s na 1 mm",
      },
      { symbol: "<math><msub><mi>t</mi><mi>b</mi></msub></math>", text: "podstawa hydrogramu", unit: "h" },
    ],
    symbols: { ct: "Ct", cp: "Cp", area_km2: "A" },
    note:
      "<p>Model nie używa t<sub>c</sub>: nie podawaj mu wyników grupy <code>tc</code>; podany " +
      "t<sub>c</sub> Hydrolog pomija z uwagą w wyniku. W hydrogramie D = krok Δt, więc opóźnienie, czas " +
      "do szczytu i szczyt są przeliczone na ten czas trwania (t<sub>LR</sub>, t<sub>pR</sub>, " +
      "q<sub>pR</sub> wg HEC-HMS). Kształt to krzywa gamma (n = 3,7) ze szczytem w t<sub>pR</sub>, " +
      "obcięta na t<sub>b</sub> i unormowana do 1 mm, dlatego C<sub>p</sub> zmienia szczyt tylko " +
      "nieznacznie, przez długość podstawy. C<sub>t</sub> i C<sub>p</sub> bierze się z kalibracji w " +
      "zlewniach tego samego regionu; C<sub>t</sub> w postaci metrycznej to 0,75 × C<sub>t</sub> " +
      "Snydera.</p>",
    sources:
      "Snyder 1938 (za Chow i in. 1988); Chow i in. 1988; USACE 2000 (HEC-HMS); Hydrolog, " +
      "<code>docs/COMPUTATION_PATHS.md</code> 3.4 i 5.2; opis polecenia <code>uh snyder</code>",
  },
};
