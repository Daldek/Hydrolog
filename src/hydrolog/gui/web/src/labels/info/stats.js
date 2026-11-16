/**
 * Explanations (i) of „Statystyka przepływów”, by Nogat DEV-15.14: the flood frequency
 * analysis, its four distributions and fit methods, the measures of fit, the probability
 * plot and the homogeneity tests; each a definition, its formula in MathML with its symbols
 * and units, how to read it and the literature, and `guide`, the subsection of the guide's
 * chapter „Metody obliczeń” that holds the longer explanation. Trusted HTML fragments. The
 * length of the record is checked against Hydrolog's range (`typical_ranges` of `stats
 * flood-frequency`, the result's `n_years`), which the section registers with the
 * explanations (registerInfo(statsInfo)).
 */

export const statsInfo = {
  "stats-flood-frequency": {
    title: "Analiza częstości wezbrań",
    intro:
      "<p>Przepływy maksymalne o zadanym okresie powtarzalności <i>T</i>, liczone z rozkładów prawdopodobieństwa " +
      "dopasowanych do maksimów rocznych. Kwantyl <i>Q<sub>T</sub></i> jest przewyższany w każdym roku z prawdopodobieństwem " +
      "<i>p</i> = 1/<i>T</i>.</p>",
    formula:
      '<math display="block"><msub><mi>Q</mi><mi>T</mi></msub><mo>=</mo><msup><mi>F</mi><mrow><mo>−</mo><mn>1</mn></mrow></msup><mo>(</mo><mn>1</mn><mo>−</mo><mi>p</mi><mo>)</mo><mo>,</mo><mspace width="1em"></mspace><mi>p</mi><mo>=</mo><mfrac><mn>1</mn><mi>T</mi></mfrac></math>',
    vars: [
      { symbol: "<math><msub><mi>Q</mi><mi>T</mi></msub></math>", text: "przepływ o okresie powtarzalności T: kwantyl dopasowanego rozkładu", unit: "m³/s" },
      { symbol: "<math><mi>T</mi></math>", text: "okres powtarzalności: przepływ przewyższany średnio raz na T lat", unit: "lata" },
      { symbol: "<math><mi>p</mi></math>", text: "prawdopodobieństwo przewyższenia w roku (1&nbsp;% dla T = 100 lat)", unit: "–" },
      { symbol: "<math><mi>F</mi></math>", text: "dystrybuanta dopasowanego rozkładu", unit: "–" },
    ],
    symbols: { years: "Długość szeregu N" },
    note:
      "<p>Q&nbsp;1% jest przewyższany średnio raz na 100 lat, ale w każdym roku z prawdopodobieństwem 1&nbsp;%. Kwantyl " +
      "dla <i>T</i> dużo dłuższego niż szereg to ekstrapolacja, tym mniej pewna, im dłuższe <i>T</i>.</p>",
    guide: "metoda-stats-flood-frequency",
    sources:
      "KZGW 2017 (Aktualizacja metodyki obliczania przepływów i opadów maksymalnych); " +
      "Coles 2001 (An Introduction to Statistical Modeling of Extreme Values)",
  },
  "stats-distributions": {
    title: "Rozkłady maksimów rocznych",
    intro:
      "<p>Cztery rozkłady maksimów rocznych: GEV (uogólniony rozkład wartości ekstremalnych), log-normalny o dwóch " +
      "parametrach oraz trójparametrowe Pearson III i Weibull. Wzór to dystrybuanta GEV; <i>ξ</i> = 0 daje rozkład Gumbela.</p>",
    formula:
      '<math display="block"><mi>F</mi><mo>(</mo><mi>x</mi><mo>)</mo><mo>=</mo><mi>exp</mi><mrow><mo>{</mo><mo>−</mo><msup><mrow><mo>[</mo><mn>1</mn><mo>+</mo><mi>ξ</mi><mfrac><mrow><mi>x</mi><mo>−</mo><mi>μ</mi></mrow><mi>σ</mi></mfrac><mo>]</mo></mrow><mrow><mo>−</mo><mn>1</mn><mo>/</mo><mi>ξ</mi></mrow></msup><mo>}</mo></mrow></math>',
    vars: [
      { symbol: "<math><mi>F</mi><mo>(</mo><mi>x</mi><mo>)</mo></math>", text: "dystrybuanta: prawdopodobieństwo, że maksimum roczne nie przekroczy x", unit: "–" },
      { symbol: "<math><mi>x</mi></math>", text: "przepływ", unit: "m³/s" },
      { symbol: "<math><mi>μ</mi></math>", text: "parametr położenia", unit: "m³/s" },
      { symbol: "<math><mi>σ</mi></math>", text: "parametr skali", unit: "m³/s" },
      { symbol: "<math><mi>ξ</mi></math>", text: "parametr kształtu", unit: "–" },
    ],
    note:
      "<p>Przy <i>ξ</i> &gt; 0 kwantyle rosną z <i>T</i> szybciej niż w rozkładzie Gumbela (ciężki ogon), a przy " +
      "<i>ξ</i> &lt; 0 przepływ ma górną granicę. Rozkłady o podobnym AIC mogą dać różne kwantyle dla długich <i>T</i>.</p>",
    guide: "metoda-stats-distributions",
    sources:
      "Coles 2001 (An Introduction to Statistical Modeling of Extreme Values, rozdz. 3); " +
      "Hosking i Wallis 1997 (Regional Frequency Analysis)",
  },
  "stats-fit-method": {
    title: "Metoda estymacji parametrów",
    intro:
      "<p>Sposób szacowania parametrów rozkładów z maksimów rocznych: L-momenty (domyślnie), największa wiarygodność, " +
      "momenty albo najmniejsze kwadraty. Wzór to L-momenty próby.</p>",
    formula:
      '<math display="block"><msub><mi>λ</mi><mn>1</mn></msub><mo>=</mo><msub><mi>b</mi><mn>0</mn></msub><mo>,</mo><mspace width="1em"></mspace><msub><mi>λ</mi><mn>2</mn></msub><mo>=</mo><mn>2</mn><msub><mi>b</mi><mn>1</mn></msub><mo>−</mo><msub><mi>b</mi><mn>0</mn></msub><mo>,</mo><mspace width="1em"></mspace><msub><mi>τ</mi><mn>3</mn></msub><mo>=</mo><mfrac><mrow><mn>6</mn><msub><mi>b</mi><mn>2</mn></msub><mo>−</mo><mn>6</mn><msub><mi>b</mi><mn>1</mn></msub><mo>+</mo><msub><mi>b</mi><mn>0</mn></msub></mrow><msub><mi>λ</mi><mn>2</mn></msub></mfrac></math>',
    vars: [
      { symbol: "<math><msub><mi>b</mi><mi>r</mi></msub></math>", text: "nieobciążone momenty ważone prawdopodobieństwem próby uszeregowanej rosnąco, r = 0, 1, 2", unit: "m³/s" },
      { symbol: "<math><msub><mi>λ</mi><mn>1</mn></msub><mo>,</mo><msub><mi>λ</mi><mn>2</mn></msub></math>", text: "pierwszy i drugi L-moment: położenie i rozrzut próby", unit: "m³/s" },
      { symbol: "<math><msub><mi>τ</mi><mn>3</mn></msub></math>", text: "L-skośność: asymetria próby", unit: "–" },
    ],
    note:
      "<p>L-momenty są mniej czułe na pojedyncze duże maksima i stabilniejsze na krótkich szeregach niż największa " +
      "wiarygodność, a najmniejsze kwadraty idą za największymi maksimami. Dla rzadkich wezbrań metody mogą dać różne " +
      "kwantyle.</p>",
    guide: "metoda-stats-fit-method",
    sources: "Hosking i Wallis 1997 (Regional Frequency Analysis)",
  },
  "stats-fit": {
    title: "Zgodność dopasowania: AIC, A², KS",
    intro:
      "<p>Miary zgodności rozkładu z maksimami rocznymi: kryterium AIC porównuje kombinacje rozkładu i metody, " +
      "a A² Andersona–Darlinga i KS p testu Kołmogorowa–Smirnowa mierzą odległość od rozkładu empirycznego.</p>",
    formula:
      '<math display="block"><mi>AIC</mi><mo>=</mo><mn>2</mn><mi>k</mi><mo>−</mo><mn>2</mn><mi>ln</mi><mover><mi>L</mi><mo>^</mo></mover></math><math display="block"><msup><mi>A</mi><mn>2</mn></msup><mo>=</mo><mo>−</mo><mi>n</mi><mo>−</mo><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><mfrac><mrow><mn>2</mn><mi>i</mi><mo>−</mo><mn>1</mn></mrow><mi>n</mi></mfrac><mrow><mo>[</mo><mi>ln</mi><mi>F</mi><mo>(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>)</mo><mo>+</mo><mi>ln</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>F</mi><mo>(</mo><msub><mi>x</mi><mrow><mi>n</mi><mo>+</mo><mn>1</mn><mo>−</mo><mi>i</mi></mrow></msub><mo>)</mo><mo>)</mo><mo>]</mo></mrow></math>',
    vars: [
      { symbol: "<math><mi>k</mi></math>", text: "liczba parametrów rozkładu: 2 albo 3", unit: "–" },
      { symbol: "<math><mover><mi>L</mi><mo>^</mo></mover></math>", text: "wiarygodność próby przy dopasowanych parametrach", unit: "–" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba maksimów rocznych", unit: "–" },
      { symbol: "<math><msub><mi>x</mi><mi>i</mi></msub></math>", text: "maksima uszeregowane rosnąco", unit: "m³/s" },
      { symbol: "<math><mi>F</mi></math>", text: "dystrybuanta dopasowanego rozkładu", unit: "–" },
    ],
    note:
      "<p>Mniejsze AIC jest lepsze, różnica poniżej 2 nie rozstrzyga, a brak AIC (—) znaczy, że rozkład nie obejmuje " +
      "któregoś maksimum. ✓ to A² poniżej wartości krytycznej dla 5&nbsp;%; oba testy są przybliżone.</p>",
    guide: "metoda-stats-fit",
    sources:
      "Akaike 1974; Burnham i Anderson 2002 (Model Selection and Multimodel Inference); Anderson i Darling 1954; " +
      "Stephens 1974",
  },
  "stats-plot": {
    title: "Siatka Gumbela i położenie Weibulla",
    intro:
      "<p>Wykres prawdopodobieństwa przewyższenia na siatce Gumbela: oś pozioma jest liniowa w zmiennej zredukowanej " +
      "<i>u</i>, a jej podpisy to <i>p</i> i <i>T</i> = 1/<i>p</i>. Punkty to maksima roczne w położeniu Weibulla, " +
      "linie to rozkłady.</p>",
    formula:
      '<math display="block"><mi>u</mi><mo>=</mo><mo>−</mo><mi>ln</mi><mo>(</mo><mo>−</mo><mi>ln</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>p</mi><mo>)</mo><mo>)</mo><mo>,</mo><mspace width="1em"></mspace><msub><mi>p</mi><mi>i</mi></msub><mo>=</mo><mfrac><mi>i</mi><mrow><mi>n</mi><mo>+</mo><mn>1</mn></mrow></mfrac></math>',
    vars: [
      { symbol: "<math><mi>u</mi></math>", text: "zmienna zredukowana Gumbela", unit: "–" },
      { symbol: "<math><mi>p</mi></math>", text: "prawdopodobieństwo przewyższenia w roku", unit: "–" },
      { symbol: "<math><msub><mi>p</mi><mi>i</mi></msub></math>", text: "empiryczne prawdopodobieństwo przewyższenia maksimum o pozycji i", unit: "–" },
      { symbol: "<math><mi>i</mi></math>", text: "pozycja w szeregu malejącym (1 to największe maksimum)", unit: "–" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba maksimów rocznych", unit: "–" },
    ],
    note:
      "<p>Rozkład Gumbela jest tu prostą, a linia wygięta ku górze ma cięższy ogon. Dobrze dopasowana linia biegnie blisko " +
      "punktów, zwłaszcza największych; największe z <i>n</i> maksimów stoi przy <i>T</i> = <i>n</i> + 1 lat.</p>",
    guide: "metoda-stats-plot",
    sources: "Weibull 1939; Gumbel 1958 (Statistics of Extremes)",
  },
  "stats-homogeneity": {
    title: "Jednorodność ciągu: testy Manna-Whitneya, Kołmogorowa-Smirnowa i Pettitta",
    intro:
      "<p>Sprawdzenie, czy maksima roczne pochodzą z jednego rozkładu, jak zakłada analiza częstości: testy " +
      "Manna-Whitneya i Kołmogorowa-Smirnowa porównują połowy szeregu, a test Pettitta szuka roku zmiany.</p>",
    formula:
      '<math display="block"><msub><mi>U</mi><mi>t</mi></msub><mo>=</mo><mn>2</mn><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>t</mi></munderover><msub><mi>r</mi><mi>i</mi></msub><mo>−</mo><mi>t</mi><mo>(</mo><mi>n</mi><mo>+</mo><mn>1</mn><mo>)</mo><mo>,</mo><mspace width="1em"></mspace><mi>K</mi><mo>=</mo><munder><mi>max</mi><mi>t</mi></munder><mo>|</mo><msub><mi>U</mi><mi>t</mi></msub><mo>|</mo></math><math display="block"><mi>p</mi><mo>≈</mo><mn>2</mn><mi>exp</mi><mo>(</mo><mo>−</mo><mfrac><mrow><mn>6</mn><msup><mi>K</mi><mn>2</mn></msup></mrow><mrow><msup><mi>n</mi><mn>3</mn></msup><mo>+</mo><msup><mi>n</mi><mn>2</mn></msup></mrow></mfrac><mo>)</mo></math>',
    vars: [
      { symbol: "<math><msub><mi>U</mi><mi>t</mi></msub></math>", text: "statystyka Pettitta dla podziału po t pierwszych wartościach", unit: "–" },
      { symbol: "<math><msub><mi>r</mi><mi>i</mi></msub></math>", text: "ranga wartości i w całym szeregu (przy remisach średnia ranga)", unit: "–" },
      { symbol: "<math><mi>K</mi></math>", text: "statystyka testu Pettitta: największe |U<sub>t</sub>|", unit: "–" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba maksimów rocznych", unit: "–" },
      { symbol: "<math><mi>p</mi></math>", text: "przybliżone p testu Pettitta, najwyżej 1, trafne dla p ≤ 0,5", unit: "–" },
    ],
    note:
      "<p>Test odrzuca jednorodność, gdy <i>p</i> &lt; 0,05; przyczyną bywa zbiornik, regulacja koryta albo przeniesiony " +
      "wodowskaz. „Jednorodny” znaczy, że test nie znalazł różnicy: krótki szereg rzadko daje odrzucenie.</p>",
    guide: "metoda-stats-homogeneity",
    sources:
      "Mann i Whitney 1947; Smirnov 1939; " +
      "Pettitt 1979 (A non-parametric approach to the change-point problem)",
  },
};
