/**
 * Explanations (i) of the routing methods of Sieć, by Nogat DEV-15.14: what each method
 * does with the wave (a definition), its formula in MathML with its symbols and units, how
 * to read the outflow and the literature; `guide` names the subsection of the guide's
 * chapter „Metody obliczeń” that holds the longer explanation (windows, sub-reaches, the
 * table's rules). The facts are those of docs/COMPUTATION_PATHS.md (3.9). Ids:
 * "routing.<method>", as the reach's method is named in hydrolog-network/1; a reservoir is
 * "routing.level-pool". Trusted repository text, set as HTML by ui/info.js. The bounds of
 * Muskingum's X are those of the network's schema, which Sieć registers with the explanation.
 */

export const routing = {
  "routing.lag": {
    title: "Lag: przesunięcie fali w czasie",
    intro:
      "<p>Odcinek przenosi falę bez zmiany kształtu: odpływ powtarza dopływ po stałym czasie <i>T</i><sub>lag</sub>. " +
      "Metoda dla krótkiego odcinka o znanym czasie przepływu, który prawie nie spłaszcza fali.</p>",
    formula:
      '<math display="block"><mi>O</mi><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><mi>I</mi><mo>(</mo><mi>t</mi><mo>−</mo><msub><mi>T</mi><mtext>lag</mtext></msub><mo>)</mo></math>',
    vars: [
      { symbol: "<math><mi>I</mi></math>", text: "dopływ: hydrogram węzła powyżej", unit: "m³/s" },
      { symbol: "<math><mi>O</mi></math>", text: "odpływ z odcinka", unit: "m³/s" },
      { symbol: "<math><msub><mi>T</mi><mtext>lag</mtext></msub></math>", text: "opóźnienie: czas przepływu fali przez odcinek", unit: "min" },
    ],
    note:
      "<p>Przy opóźnieniu równym wielokrotności kroku czasowego szczyt odpływu jest równy szczytowi dopływu, tylko " +
      "późniejszy o <i>T</i><sub>lag</sub>. Inne opóźnienie jest interpolowane liniowo między rzędnymi, co obniża " +
      "ostry szczyt.</p>",
    sources: "USACE 2024 (HEC-HMS Technical Reference Manual, model Lag)",
  },
  "routing.muskingum": {
    title: "Muskingum: magazynowanie klinowe",
    intro:
      "<p>Woda w odcinku to graniastosłup <i>K O</i> i klin <i>K X</i> (<i>I</i> − <i>O</i>). Równanie ciągłości w kroku " +
      "Δ<i>t</i> daje odpływ jako ważoną sumę dopływu bieżącego, dopływu poprzedniego i odpływu poprzedniego.</p>",
    formula:
      '<math display="block"><mi>S</mi><mo>=</mo><mi>K</mi><mo>[</mo><mi>X</mi><mi>I</mi><mo>+</mo><mo>(</mo><mn>1</mn><mo>−</mo><mi>X</mi><mo>)</mo><mi>O</mi><mo>]</mo></math>' +
      '<math display="block"><msub><mi>O</mi><mi>t</mi></msub><mo>=</mo><msub><mi>C</mi><mn>0</mn></msub><msub><mi>I</mi><mi>t</mi></msub><mo>+</mo><msub><mi>C</mi><mn>1</mn></msub><msub><mi>I</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>+</mo><msub><mi>C</mi><mn>2</mn></msub><msub><mi>O</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub></math>' +
      '<math display="block"><msub><mi>C</mi><mn>0</mn></msub><mo>=</mo><mfrac><mrow><mi>Δ</mi><mi>t</mi><mo>−</mo><mn>2</mn><mi>K</mi><mi>X</mi></mrow><mi>D</mi></mfrac><mo>,</mo><msub><mi>C</mi><mn>1</mn></msub><mo>=</mo><mfrac><mrow><mi>Δ</mi><mi>t</mi><mo>+</mo><mn>2</mn><mi>K</mi><mi>X</mi></mrow><mi>D</mi></mfrac><mo>,</mo><msub><mi>C</mi><mn>2</mn></msub><mo>=</mo><mfrac><mrow><mn>2</mn><mi>K</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>X</mi><mo>)</mo><mo>−</mo><mi>Δ</mi><mi>t</mi></mrow><mi>D</mi></mfrac><mo>,</mo><mi>D</mi><mo>=</mo><mn>2</mn><mi>K</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>X</mi><mo>)</mo><mo>+</mo><mi>Δ</mi><mi>t</mi></math>',
    vars: [
      { symbol: "<math><mi>K</mi></math>", text: "czas przepływu fali przez odcinek, w przybliżeniu jego długość przez prędkość fali", unit: "min" },
      { symbol: "<math><mi>X</mi></math>", text: "współczynnik wagowy, od 0 do 0,5", unit: "–" },
      { symbol: "<math><mi>S</mi></math>", text: "woda zmagazynowana w odcinku", unit: "m³" },
      { symbol: "<math><mi>I</mi><mo>,</mo><mi>O</mi></math>", text: "dopływ i odpływ; indeks t to krok bieżący, t − 1 poprzedni", unit: "m³/s" },
      { symbol: "<math><msub><mi>C</mi><mn>0</mn></msub><mo>,</mo><msub><mi>C</mi><mn>1</mn></msub><mo>,</mo><msub><mi>C</mi><mn>2</mn></msub></math>", text: "wagi dopływu bieżącego, dopływu poprzedniego i odpływu poprzedniego; sumują się do 1", unit: "–" },
      { symbol: "<math><mi>Δ</mi><mi>t</mi></math>", text: "krok czasowy", unit: "min" },
    ],
    symbols: { x: "X" },
    note:
      "<p>Średnie opóźnienie fali to <i>K</i>. <i>X</i> = 0 to zbiornik liniowy, który spłaszcza falę najbardziej, " +
      "<i>X</i> = 0,5 przenosi ją bez spłaszczenia, a podział odcinka na więcej pododcinków spłaszcza ją mniej.</p>",
    guide: "metoda-routing-muskingum",
    sources:
      "McCarthy 1938; Chow i in. 1988 (Applied Hydrology, rozdz. 8); " +
      "USACE 2024 (HEC-HMS Technical Reference Manual, model Muskingum)",
  },
  "routing.muskingum-cunge": {
    title: "Muskingum-Cunge: współczynniki z koryta",
    intro:
      "<p>Metoda Muskingum, której <i>K</i> i <i>X</i> wynikają z prędkości fali, szerokości zwierciadła i spadku dna przy " +
      "przepływie odniesienia, tak by spłaszczenie fali w obliczeniu było równe jej dyfuzji w korycie.</p>",
    formula:
      '<math display="block"><mi>K</mi><mo>=</mo><mfrac><mrow><mi>Δ</mi><mi>x</mi></mrow><mi>c</mi></mfrac><mo>,</mo><mspace width="1em"></mspace><mi>X</mi><mo>=</mo><mfrac><mn>1</mn><mn>2</mn></mfrac><mrow><mo>(</mo><mn>1</mn><mo>−</mo><mfrac><mi>Q</mi><mrow><mi>T</mi><msub><mi>S</mi><mn>0</mn></msub><mi>c</mi><mi>Δ</mi><mi>x</mi></mrow></mfrac><mo>)</mo></mrow></math>',
    vars: [
      { symbol: "<math><mi>K</mi></math>", text: "czas przepływu fali przez krok drogi Δx", unit: "s" },
      { symbol: "<math><mi>X</mi></math>", text: "współczynnik wagowy; może być ujemny", unit: "–" },
      { symbol: "<math><mi>c</mi></math>", text: "prędkość fali przy przepływie odniesienia: podana albo z przekroju i wzoru Manninga", unit: "m/s" },
      { symbol: "<math><mi>T</mi></math>", text: "szerokość zwierciadła wody przy przepływie odniesienia", unit: "m" },
      { symbol: "<math><msub><mi>S</mi><mn>0</mn></msub></math>", text: "spadek dna odcinka", unit: "m/m" },
      { symbol: "<math><mi>Q</mi></math>", text: "przepływ odniesienia, domyślnie szczyt dopływu", unit: "m³/s" },
      { symbol: "<math><mi>Δ</mi><mi>x</mi></math>", text: "krok drogi: długość odcinka podzielona na równe części", unit: "m" },
    ],
    note:
      "<p>Mały spadek dna i duży przepływ na metr szerokości zwierciadła spłaszczają falę silniej (<i>X</i> maleje, także " +
      "poniżej 0), a wolniejsza fala bardziej ją opóźnia.</p>",
    guide: "metoda-routing-muskingum-cunge",
    sources:
      "Cunge 1969; USDA-NRCS 2014 (NEH 630, rozdz. 17); " +
      "USACE 2024 (HEC-HMS Technical Reference Manual, model Muskingum-Cunge)",
  },
  "routing.cascade": {
    title: "Kaskada zbiorników liniowych",
    intro:
      "<p>Odcinek to <i>n</i> jednakowych zbiorników liniowych połączonych szeregowo; w każdym woda <i>S</i> = <i>K O</i>. " +
      "Odpowiedź na impuls jednostkowy dopływu to rozkład gamma o średnim opóźnieniu <i>n K</i>.</p>",
    formula:
      '<math display="block"><mi>u</mi><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><mfrac><msup><mrow><mo>(</mo><mi>t</mi><mo>/</mo><mi>K</mi><mo>)</mo></mrow><mrow><mi>n</mi><mo>−</mo><mn>1</mn></mrow></msup><mrow><mi>K</mi><mi>Γ</mi><mo>(</mo><mi>n</mi><mo>)</mo></mrow></mfrac><msup><mi>e</mi><mrow><mo>−</mo><mi>t</mi><mo>/</mo><mi>K</mi></mrow></msup></math>',
    vars: [
      { symbol: "<math><mi>u</mi><mo>(</mo><mi>t</mi><mo>)</mo></math>", text: "odpowiedź odcinka na impuls jednostkowy dopływu", unit: "1/min" },
      { symbol: "<math><mi>t</mi></math>", text: "czas od impulsu", unit: "min" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba zbiorników, nie musi być całkowita", unit: "–" },
      { symbol: "<math><mi>K</mi></math>", text: "stała jednego zbiornika: podana albo K = L/(n c)", unit: "min" },
      { symbol: "<math><mi>L</mi><mo>,</mo><mi>c</mi></math>", text: "długość odcinka i prędkość fali, gdy K nie jest podane", unit: "km, m/s" },
      { symbol: "<math><mi>Γ</mi></math>", text: "funkcja gamma", unit: "–" },
    ],
    note:
      "<p>Przy tym samym opóźnieniu <i>n K</i> jeden zbiornik spłaszcza falę najbardziej, a duże <i>n</i> prawie tylko ją " +
      "przesuwa. Odpływ jest liczony dokładnie przy każdym kroku czasowym, bez dzielenia kroku.</p>",
    guide: "metoda-routing-cascade",
    sources:
      "Nash 1957; Kalinin i Milyukov 1957 (za Szilagyi i in. 2005); " +
      "Ponce 1980 (Linear reservoirs and numerical diffusion)",
  },
  "routing.level-pool": {
    title: "Level-pool: zbiornik i krzywa pojemność–odpływ",
    intro:
      "<p>Zbiornik albo odcinek, w którym każdemu odpływowi odpowiada jedna pojemność według tabeli " +
      "pojemność–odpływ. Odpływ wynika z równania ciągłości i krzywej roboczej <i>S</i>/Δ<i>t</i> + <i>O</i>/2 " +
      "(zmodyfikowana metoda Pulsa).</p>",
    formula:
      '<math display="block"><mfrac><msub><mi>S</mi><mn>2</mn></msub><mrow><mi>Δ</mi><mi>t</mi></mrow></mfrac><mo>+</mo><mfrac><msub><mi>O</mi><mn>2</mn></msub><mn>2</mn></mfrac><mo>=</mo><mfrac><mrow><msub><mi>I</mi><mn>1</mn></msub><mo>+</mo><msub><mi>I</mi><mn>2</mn></msub></mrow><mn>2</mn></mfrac><mo>+</mo><mfrac><msub><mi>S</mi><mn>1</mn></msub><mrow><mi>Δ</mi><mi>t</mi></mrow></mfrac><mo>−</mo><mfrac><msub><mi>O</mi><mn>1</mn></msub><mn>2</mn></mfrac></math>',
    vars: [
      { symbol: "<math><mi>S</mi></math>", text: "pojemność: woda w zbiorniku; indeks 1 to początek kroku, 2 jego koniec", unit: "m³" },
      { symbol: "<math><mi>O</mi></math>", text: "odpływ", unit: "m³/s" },
      { symbol: "<math><mi>I</mi></math>", text: "dopływ", unit: "m³/s" },
      { symbol: "<math><mi>Δ</mi><mi>t</mi></math>", text: "krok czasowy", unit: "min" },
    ],
    note:
      "<p>Im większa pojemność przy danym odpływie, tym niższy i późniejszy szczyt; w pojedynczym zbiorniku przypada on, " +
      "gdy odpływ zrówna się z dopływem. Fala ponad ostatni wiersz tabeli przerywa obliczenie.</p>",
    guide: "metoda-routing-level-pool",
    sources:
      "USDA-NRCS 2014 (NEH 630, rozdz. 17); " +
      "USACE 2024 (HEC-HMS Technical Reference Manual, model Modified Puls)",
  },
};
