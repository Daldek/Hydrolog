/**
 * Explanations (i) of the routing methods of Sieć (plan D16): what each method does with
 * the wave, its formula in MathML, its variables and its sources, from Hydrolog's
 * docs/COMPUTATION_PATHS.md (3.9). Ids: "routing.<method>", as the reach's method is named
 * in hydrolog-network/1; a reservoir is "routing.level-pool". Trusted repository text,
 * set as HTML by ui/info.js. The bounds of Muskingum's X are those of the network's schema,
 * which Sieć registers with the explanation.
 */

export const routing = {
  "routing.lag": {
    title: "Lag: przesunięcie fali w czasie",
    intro:
      "<p>Odcinek opóźnia hydrogram dopływu o stały czas <i>T</i><sub>lag</sub> i go nie spłaszcza, jak model Lag w HEC-HMS: dla krótkiego odcinka o znanym czasie przepływu. Opóźnienie, które nie jest całkowitą liczbą kroków, jest interpolowane liniowo, co nieco spłaszcza ostre szczyty (uwaga <code>lag_interpolated</code>).</p>",
    formula:
      '<math display="block"><mi>O</mi><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><mi>I</mi><mo>(</mo><mi>t</mi><mo>−</mo><msub><mi>T</mi><mtext>lag</mtext></msub><mo>)</mo></math>',
    vars: [
      { symbol: "<math><mi>I</mi></math>", text: "dopływ (hydrogram węzła powyżej)", unit: "m³/s" },
      { symbol: "<math><mi>O</mi></math>", text: "odpływ z odcinka", unit: "m³/s" },
      { symbol: "<math><msub><mi>T</mi><mtext>lag</mtext></msub></math>", text: "opóźnienie, <code>lag_min</code>", unit: "min" },
    ],
    sources: "HEC-HMS Technical Reference Manual, model Lag; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.9.2",
  },
  "routing.muskingum": {
    title: "Muskingum: magazynowanie klinowe",
    intro:
      "<p>Woda w odcinku to graniastosłup <i>K O</i> i klin <i>K X</i> (<i>I</i> − <i>O</i>); równanie ciągłości w kroku Δ<i>t</i> z regułą trapezów daje rekurencję, której wagi sumują się do 1. <i>X</i> = 0 to zbiornik liniowy (największe tłumienie), <i>X</i> = 0,5 przenosi falę bez tłumienia. Odcinek dzieli się na <i>N</i> pododcinków o <i>K</i>/<i>N</i> tak, by wszystkie wagi były nieujemne: 2<i>KX</i>/Δ<i>t</i> ≤ <i>N</i> ≤ 2<i>K</i>(1 − <i>X</i>)/Δ<i>t</i>; więcej pododcinków tłumi mniej.</p>",
    formula:
      '<math display="block"><mi>S</mi><mo>=</mo><mi>K</mi><mo>[</mo><mi>X</mi><mi>I</mi><mo>+</mo><mo>(</mo><mn>1</mn><mo>−</mo><mi>X</mi><mo>)</mo><mi>O</mi><mo>]</mo></math>' +
      '<math display="block"><msub><mi>O</mi><mi>t</mi></msub><mo>=</mo><msub><mi>C</mi><mn>0</mn></msub><msub><mi>I</mi><mi>t</mi></msub><mo>+</mo><msub><mi>C</mi><mn>1</mn></msub><msub><mi>I</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub><mo>+</mo><msub><mi>C</mi><mn>2</mn></msub><msub><mi>O</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub></math>' +
      '<math display="block"><msub><mi>C</mi><mn>0</mn></msub><mo>=</mo><mfrac><mrow><mi>Δ</mi><mi>t</mi><mo>−</mo><mn>2</mn><mi>K</mi><mi>X</mi></mrow><mi>D</mi></mfrac><mo>,</mo><msub><mi>C</mi><mn>1</mn></msub><mo>=</mo><mfrac><mrow><mi>Δ</mi><mi>t</mi><mo>+</mo><mn>2</mn><mi>K</mi><mi>X</mi></mrow><mi>D</mi></mfrac><mo>,</mo><msub><mi>C</mi><mn>2</mn></msub><mo>=</mo><mfrac><mrow><mn>2</mn><mi>K</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>X</mi><mo>)</mo><mo>−</mo><mi>Δ</mi><mi>t</mi></mrow><mi>D</mi></mfrac><mo>,</mo><mi>D</mi><mo>=</mo><mn>2</mn><mi>K</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>X</mi><mo>)</mo><mo>+</mo><mi>Δ</mi><mi>t</mi></math>',
    vars: [
      { symbol: "<math><mi>K</mi></math>", text: "czas przepływu fali przez odcinek, <code>k_min</code>", unit: "min" },
      { symbol: "<math><mi>X</mi></math>", text: "współczynnik wagowy, <code>x</code>", unit: "–" },
      { symbol: "<math><mi>S</mi></math>", text: "woda zmagazynowana w odcinku", unit: "m³" },
      { symbol: "<math><msub><mi>C</mi><mn>0</mn></msub><mo>,</mo><msub><mi>C</mi><mn>1</mn></msub><mo>,</mo><msub><mi>C</mi><mn>2</mn></msub></math>", text: "wagi dopływu bieżącego, dopływu poprzedniego i odpływu poprzedniego", unit: "–" },
    ],
    symbols: { x: "X" },
    sources:
      "McCarthy (1938); Chow, Maidment, Mays, <i>Applied Hydrology</i> (1988), rozdz. 8; HEC-HMS, model Muskingum; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.9.3",
  },
  "routing.muskingum-cunge": {
    title: "Muskingum-Cunge: współczynniki z koryta",
    intro:
      "<p>Cunge (1969) zrównał dyfuzję numeryczną schematu Muskingum z dyfuzją fizyczną fali: <i>K</i> i <i>X</i> kroku Δ<i>x</i> wynikają z prędkości fali <i>c</i>, szerokości zwierciadła <i>T</i>, spadku dna <i>S</i><sub>0</sub> i przepływu odniesienia <i>Q</i> (domyślnie szczytu dopływu). Prędkość i szerokość podaje się wprost albo wynikają z przekroju (prostokąt, trapez, trójkąt) i wzoru Manninga. Odcinek o długości <i>L</i> dzieli się na równe kroki Δ<i>x</i>; gdy hydrogram rośnie za szybko, krok czasowy jest zagęszczany (uwaga <code>timestep_refined</code>).</p>",
    formula:
      '<math display="block"><mi>K</mi><mo>=</mo><mfrac><mrow><mi>Δ</mi><mi>x</mi></mrow><mi>c</mi></mfrac><mo>,</mo><mspace width="1em"></mspace><mi>X</mi><mo>=</mo><mfrac><mn>1</mn><mn>2</mn></mfrac><mrow><mo>(</mo><mn>1</mn><mo>−</mo><mfrac><mi>Q</mi><mrow><mi>T</mi><msub><mi>S</mi><mn>0</mn></msub><mi>c</mi><mi>Δ</mi><mi>x</mi></mrow></mfrac><mo>)</mo></mrow></math>',
    vars: [
      { symbol: "<math><mi>c</mi></math>", text: "prędkość fali przy przepływie odniesienia, <code>celerity_m_per_s</code>", unit: "m/s" },
      { symbol: "<math><mi>T</mi></math>", text: "szerokość zwierciadła, <code>top_width_m</code>", unit: "m" },
      { symbol: "<math><msub><mi>S</mi><mn>0</mn></msub></math>", text: "spadek dna, <code>slope_m_per_m</code>", unit: "m/m" },
      { symbol: "<math><mi>Q</mi></math>", text: "przepływ odniesienia, <code>reference_discharge_m3s</code>", unit: "m³/s" },
      { symbol: "<math><mi>Δ</mi><mi>x</mi></math>", text: "krok drogi, część długości <code>length_km</code>", unit: "m" },
    ],
    sources: "Cunge (1969); NRCS NEH-630 rozdz. 17; HEC-HMS, model Muskingum-Cunge; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.9.4",
  },
  "routing.cascade": {
    title: "Kaskada zbiorników liniowych",
    intro:
      "<p>Odcinek to <i>n</i> jednakowych zbiorników liniowych <i>S</i> = <i>K O</i> połączonych szeregowo (Nash, 1957); <i>n</i> nie musi być całkowite. Odpowiedź na impuls jednostkowy to gęstość rozkładu gamma, a średnie opóźnienie fali to <i>n K</i>: <i>n</i> = 1 tłumi najbardziej, duże <i>n</i> tylko opóźnia. <i>K</i> podaje się wprost albo wynika z długości i prędkości fali, <i>K</i> = <i>L</i>/(<i>n c</i>). Hydrolog liczy dokładnym jądrem, więc każdy krok czasowy jest dozwolony.</p>",
    formula:
      '<math display="block"><mi>u</mi><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><mfrac><msup><mrow><mo>(</mo><mi>t</mi><mo>/</mo><mi>K</mi><mo>)</mo></mrow><mrow><mi>n</mi><mo>−</mo><mn>1</mn></mrow></msup><mrow><mi>K</mi><mi>Γ</mi><mo>(</mo><mi>n</mi><mo>)</mo></mrow></mfrac><msup><mi>e</mi><mrow><mo>−</mo><mi>t</mi><mo>/</mo><mi>K</mi></mrow></msup></math>',
    vars: [
      { symbol: "<math><mi>n</mi></math>", text: "liczba zbiorników, <code>n</code>", unit: "–" },
      { symbol: "<math><mi>K</mi></math>", text: "stała jednego zbiornika, <code>k_min</code>", unit: "min" },
      { symbol: "<math><mi>L</mi><mo>,</mo><mi>c</mi></math>", text: "długość odcinka i prędkość fali, zamiast <code>k_min</code>", unit: "km, m/s" },
    ],
    sources: "Nash (1957); Kalinin i Milyukov; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.9.5",
  },
  "routing.level-pool": {
    title: "Level-pool: zbiornik i krzywa pojemność–odpływ",
    intro:
      "<p>Zbiornik (albo odcinek) ma jedną pojemność dla każdego odpływu: tabela wierszy (<i>S</i>, <i>O</i>), z rzędną lub bez, jest jego jedynym parametrem (metoda Pulsa, krzywa robocza). Równanie ciągłości z regułą trapezów stawia nieznane <i>S</i> i <i>O</i> po jednej stronie; odpływ czyta się z krzywej roboczej interpolacją liniową tabeli, więc objętość się zgadza. Tabela nie jest ekstrapolowana: fala ponad ostatni wiersz to błąd <code>table_exceeded</code>. Pododcinki (każdy z <i>S</i>/<i>N</i>) tłumią mniej; 1 to zbiornik.</p>",
    formula:
      '<math display="block"><mfrac><msub><mi>S</mi><mn>2</mn></msub><mrow><mi>Δ</mi><mi>t</mi></mrow></mfrac><mo>+</mo><mfrac><msub><mi>O</mi><mn>2</mn></msub><mn>2</mn></mfrac><mo>=</mo><mfrac><mrow><msub><mi>I</mi><mn>1</mn></msub><mo>+</mo><msub><mi>I</mi><mn>2</mn></msub></mrow><mn>2</mn></mfrac><mo>+</mo><mfrac><msub><mi>S</mi><mn>1</mn></msub><mrow><mi>Δ</mi><mi>t</mi></mrow></mfrac><mo>−</mo><mfrac><msub><mi>O</mi><mn>1</mn></msub><mn>2</mn></mfrac></math>',
    vars: [
      { symbol: "<math><mi>S</mi></math>", text: "pojemność, <code>storage_m3</code>", unit: "m³" },
      { symbol: "<math><mi>O</mi></math>", text: "odpływ, <code>outflow_m3s</code>", unit: "m³/s" },
      { symbol: "<math><mi>I</mi></math>", text: "dopływ", unit: "m³/s" },
      { symbol: "<math><mi>Δ</mi><mi>t</mi></math>", text: "krok czasowy sieci", unit: "min" },
    ],
    sources: "NRCS NEH-630 rozdz. 17; HEC-HMS, model Modified Puls; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.9.6",
  },
};
