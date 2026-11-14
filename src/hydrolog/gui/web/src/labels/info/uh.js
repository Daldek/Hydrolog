/**
 * Explanations (i) of the unit hydrograph models of „Hydrogram zlewni” and Sieć (Nogat DEV-15.14):
 * the entries "uh-<model>" for SCS, Nash (n and K given or estimated by Lutz), Clark and Snyder,
 * in the format of ui/info.js: a definition, the formula with its symbols and units, how to
 * read the result and the sources; each links (`guide`) its subsection of the guide's chapter
 * „Metody obliczeń”, which holds the longer explanation. They keep the symbols of the
 * parameters only: the typical ranges, with their sources, are Hydrolog's (`typical_ranges` of
 * `hydrograph generate`, Lutz's area among them).
 */

export const uhInfo = {
  "uh-scs": {
    title: "Hydrogram jednostkowy SCS (NRCS)",
    intro:
      "<p>Odpływ bezpośredni z 1&nbsp;mm opadu efektywnego spadłego w czasie Δt, o stałym kształcie " +
      "bezwymiarowego hydrogramu NRCS (Mockus 1957), skalowanym czasem do szczytu t<sub>p</sub> z czasu " +
      "koncentracji t<sub>c</sub> i przepływem szczytowym q<sub>p</sub>.</p>",
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
        text: "czas koncentracji zlewni: z wybranej metody albo podany",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>lag</mi></msub></math>",
        text: "opóźnienie: od środka ciężkości opadu efektywnego do szczytu",
        unit: "min",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy, zarazem czas trwania opadu jednostkowego",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>p</mi></msub></math>",
        text: "czas do szczytu hydrogramu jednostkowego (we wzorze na q<sub>p</sub> w godzinach)",
        unit: "min",
      },
      { symbol: "<math><mi>A</mi></math>", text: "powierzchnia zlewni", unit: "km²" },
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
      "<p>Rzędne to przepływ na 1&nbsp;mm opadu efektywnego: q<sub>p</sub> = 5&nbsp;m³/s na 1&nbsp;mm daje " +
      "50&nbsp;m³/s z 10&nbsp;mm w jednym kroku. Dłuższy t<sub>c</sub> opóźnia i obniża szczyt, bo objętość " +
      "zostaje ta sama.</p>",
    guide: "metoda-uh-scs",
    sources: "Mockus 1957 (za NEH 630-16); USDA-SCS 1986 (TR-55); USDA-NRCS 2007 (NEH 630-16)",
  },

  "uh-nash": {
    title: "Nash: kaskada zbiorników liniowych",
    intro:
      "<p>Hydrogram chwilowy kaskady n jednakowych zbiorników liniowych o stałej magazynowania K (Nash " +
      "1957). n i K pochodzą z kalibracji albo, w zlewni niekontrolowanej, z metody Lutza: z cieku " +
      "głównego, szorstkości koryta oraz udziału lasów i zabudowy.</p>",
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
        text: "liczba zbiorników (parametr kształtu, może być ułamkowa)",
        unit: "–",
      },
      {
        symbol: "<math><mi>K</mi></math>",
        text: "stała magazynowania zbiornika",
        unit: "min",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>lag</mi></msub></math>",
        text: "opóźnienie: środek ciężkości hydrogramu chwilowego; jego szczyt wypada w (n − 1)·K dla n &gt; 1",
        unit: "min",
      },
      {
        symbol: "<math><mi>L</mi></math>",
        text: "Lutz: długość cieku głównego od działu wodnego do przekroju, czyli najdłuższej drogi spływu",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>c</mi></msub></math>",
        text: "Lutz: długość cieku od przekroju do punktu najbliższego środka ciężkości zlewni, nie większa niż L",
        unit: "km",
      },
      {
        symbol: "<math><mi>J</mi></math>",
        text: "Lutz: średni spadek cieku głównego, czyli najdłuższej drogi spływu",
        unit: "m/m",
      },
      {
        symbol: "<math><msub><mi>n</mi><mi>M</mi></msub></math>",
        text: "Lutz: współczynnik szorstkości Manninga koryta",
        unit: "s·m^(−1/3)",
      },
      {
        symbol: "<math><mi>U</mi></math>",
        text: "Lutz: udział terenów zurbanizowanych; bez danych 0",
        unit: "%",
      },
      {
        symbol: "<math><mi>W</mi></math>",
        text: "Lutz: udział lasów; bez danych 0",
        unit: "%",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>p</mi></msub></math>",
        text: "Lutz: czas do szczytu hydrogramu chwilowego; K = t<sub>p</sub>/(n − 1) wychodzi w godzinach",
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
      "<p>Dłuższe t<sub>lag</sub> = n·K daje szczyt niższy i późniejszy, a większe n przy tym samym " +
      "t<sub>lag</sub> skupia hydrogram wokół szczytu. Czas koncentracji nie wpływa na wynik.</p>",
    guide: "metoda-uh-nash",
    sources: "Nash 1957; Lutz 1984 (za KZGW 2017); KZGW 2017 (zał. 2); Chow i in. 1988",
  },

  "uh-clark": {
    title: "Clark: translacja i zbiornik liniowy",
    intro:
      "<p>Hydrogram chwilowy Clarka (1945): opad efektywny dopływa do przekroju w czasie translacji " +
      "t<sub>c</sub> według krzywej czas–powierzchnia zlewni, a potem przechodzi przez zbiornik liniowy o " +
      "stałej retencji R, który spłaszcza i opóźnia odpływ.</p>",
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
        text: "czas koncentracji, w modelu Clarka czas translacji",
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
        text: "dopływ do zbiornika (przyrost A<sub>cum</sub> w kroku) i odpływ z niego, normowany do objętości 1",
        unit: "–",
      },
      {
        symbol: "<math><mi>R</mi></math>",
        text: "stała retencji zbiornika liniowego (S = R·O): podana albo R/t<sub>c</sub> razy t<sub>c</sub>",
        unit: "min",
      },
      {
        symbol: "<math><mi>Δt</mi></math>",
        text: "krok czasowy, zarazem czas trwania opadu jednostkowego; najwyżej 2R",
        unit: "min",
      },
    ],
    symbols: { r_tc_ratio: "R/tc" },
    note:
      "<p>Większe R/t<sub>c</sub> daje szczyt niższy i późniejszy. Stosunek jest mały w zlewniach stromych " +
      "i zurbanizowanych, duży w płaskich i podmokłych, które dłużej zatrzymują wodę.</p>",
    guide: "metoda-uh-clark",
    sources: "Clark 1945; USACE, HEC-HMS Technical Reference Manual",
  },

  "uh-snyder": {
    title: "Snyder: syntetyczny hydrogram jednostkowy",
    intro:
      "<p>Syntetyczny hydrogram jednostkowy Snydera (1938) z własnym równaniem opóźnienia: opóźnienie " +
      "t<sub>L</sub> z długości L i L<sub>c</sub> oraz współczynnika C<sub>t</sub>, szczyt ze współczynnika " +
      "C<sub>p</sub>, oba przeliczone na czas trwania opadu równy krokowi Δt.</p>",
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
        text: "długość cieku głównego od działu wodnego do przekroju zamykającego",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>L</mi><mi>c</mi></msub></math>",
        text: "długość cieku od przekroju do punktu najbliższego środka ciężkości zlewni",
        unit: "km",
      },
      {
        symbol: "<math><msub><mi>C</mi><mi>t</mi></msub></math>",
        text: "współczynnik czasowy w jednostkach SI: 0,75 współczynnika Snydera w jednostkach angielskich",
        unit: "–",
      },
      {
        symbol: "<math><msub><mi>C</mi><mi>p</mi></msub></math>",
        text: "współczynnik szczytowy",
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
        text: "krok czasowy, zarazem czas trwania opadu jednostkowego D (we wzorach w godzinach)",
        unit: "h",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>LR</mi></msub><mo>,</mo><msub><mi>t</mi><mi>pR</mi></msub></math>",
        text: "opóźnienie i czas do szczytu dla D = Δt",
        unit: "h",
      },
      { symbol: "<math><mi>A</mi></math>", text: "powierzchnia zlewni", unit: "km²" },
      {
        symbol: "<math><msub><mi>q</mi><mi>pR</mi></msub></math>",
        text: "przepływ szczytowy dla D = Δt",
        unit: "m³/s na 1 mm",
      },
      {
        symbol: "<math><msub><mi>t</mi><mi>b</mi></msub></math>",
        text: "podstawa trójkąta o szczycie q<sub>pR</sub> i objętości 1&nbsp;mm; hydrogram trwa dłużej",
        unit: "h",
      },
    ],
    symbols: { ct: "Ct", cp: "Cp", area_km2: "A" },
    note:
      "<p>Większy C<sub>t</sub> opóźnia i obniża szczyt, większy C<sub>p</sub> go podnosi; objętość " +
      "hydrogramu zostaje równa 1&nbsp;mm. Model nie używa czasu koncentracji t<sub>c</sub>.</p>",
    guide: "metoda-uh-snyder",
    sources:
      "Snyder 1938 (za Chow i in. 1988); Chow i in. 1988; USACE 2000 (HEC-HMS); Asquith i Roussel 2007 " +
      "(USGS SIR 2007-5243)",
  },
};
