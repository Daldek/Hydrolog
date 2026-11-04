/**
 * Explanations (i) of „Statystyka przepływów” (plan D16): the flood frequency analysis of
 * `stats flood-frequency`, its four distributions, the measures of fit and the probability
 * plot. Trusted HTML fragments with MathML. The length of the record is checked against
 * Hydrolog's range (`typical_ranges` of `stats flood-frequency`, the result's `n_years`),
 * which the section registers with the explanations (registerInfo(statsInfo)).
 */

export const statsInfo = {
  "stats-flood-frequency": {
    title: "Analiza częstości wezbrań",
    intro:
      "<p>Polecenie <code>stats flood-frequency</code> dopasowuje do maksimów rocznych cztery rozkłady metodą największej wiarygodności i podaje kwantyle <i>Q<sub>T</sub></i> dla okresów powtarzalności <i>T</i>. Rozkłady są uporządkowane wg kryterium AIC: pierwszy jest najlepszy. Z szeregu dobowego z datami Hydrolog bierze najpierw maksima kompletnych lat hydrologicznych (XI–X); rok z brakującym dniem pomija.</p>",
    formula:
      '<math display="block"><msub><mi>Q</mi><mi>T</mi></msub><mo>=</mo><msup><mi>F</mi><mrow><mo>−</mo><mn>1</mn></mrow></msup><mo>(</mo><mn>1</mn><mo>−</mo><mi>p</mi><mo>)</mo><mo>,</mo><mspace width="1em"></mspace><mi>p</mi><mo>=</mo><mfrac><mn>1</mn><mi>T</mi></mfrac></math>',
    vars: [
      { symbol: "<math><msub><mi>Q</mi><mi>T</mi></msub></math>", text: "przepływ o okresie powtarzalności T (kwantyl rozkładu)", unit: "m³/s" },
      { symbol: "<math><mi>T</mi></math>", text: "okres powtarzalności: średnio raz na T lat", unit: "lata" },
      { symbol: "<math><mi>p</mi></math>", text: "prawdopodobieństwo przewyższenia w roku (p = 1% dla T = 100 lat)", unit: "–" },
      { symbol: "<math><mi>F</mi></math>", text: "dystrybuanta dopasowanego rozkładu", unit: "–" },
    ],
    symbols: { years: "Długość szeregu N" },
    note:
      "<p>Szereg krótszy niż zakres podany wyżej daje uwagę <code>short_record</code>, a bardzo krótki także <code>small_sample</code>. Kwantyl dla T znacznie dłuższego niż szereg jest ekstrapolacją: jego niepewność rośnie z T.</p>",
    sources:
      "KZGW (2017) Aktualizacja metodyki obliczania przepływów i opadów maksymalnych; Coles (2001) An Introduction to Statistical Modeling of Extreme Values; Hydrolog, <code>hydrolog.statistics.high_flows</code>",
  },
  "stats-distributions": {
    title: "Rozkłady maksimów rocznych",
    intro:
      "<p><b>GEV</b>, uogólniony rozkład wartości ekstremalnych: położenie <i>μ</i>, skala <i>σ</i> i kształt <i>ξ</i> (ξ = 0 to rozkład Gumbela). <b>Log-normalny</b>: logarytm przepływu ma rozkład normalny; dwa parametry, położenie 0. <b>Pearson III</b>: skośność, położenie i skala. <b>Weibull</b>: kształt, położenie i skala. Parametry szacuje <code>scipy.stats</code> (<code>genextreme</code>, <code>lognorm</code>, <code>pearson3</code>, <code>weibull_min</code>) metodą największej wiarygodności; w wyniku są w <code>parameters</code>.</p>",
    formula:
      '<math display="block"><mi>F</mi><mo>(</mo><mi>x</mi><mo>)</mo><mo>=</mo><mi>exp</mi><mrow><mo>{</mo><mo>−</mo><msup><mrow><mo>[</mo><mn>1</mn><mo>+</mo><mi>ξ</mi><mfrac><mrow><mi>x</mi><mo>−</mo><mi>μ</mi></mrow><mi>σ</mi></mfrac><mo>]</mo></mrow><mrow><mo>−</mo><mn>1</mn><mo>/</mo><mi>ξ</mi></mrow></msup><mo>}</mo></mrow></math>',
    vars: [
      { symbol: "<math><mi>μ</mi></math>", text: "parametr położenia GEV (<code>loc</code>)", unit: "m³/s" },
      { symbol: "<math><mi>σ</mi></math>", text: "parametr skali GEV (<code>scale</code>)", unit: "m³/s" },
      { symbol: "<math><mi>ξ</mi></math>", text: "parametr kształtu; <code>scipy</code> podaje <code>shape</code> = −ξ", unit: "–" },
    ],
    note: "<p>Kolor linii rozkładu jest stały: GEV, log-normalny, Pearson III i Weibull mają zawsze te same linie; najlepszy według AIC jest grubszy.</p>",
    sources: "Coles (2001), rozdz. 3; Hosking i Wallis (1997) Regional Frequency Analysis; Hydrolog, <code>FloodFrequencyAnalysis</code>",
  },
  "stats-fit": {
    title: "Zgodność dopasowania: AIC, A², KS",
    intro:
      "<p><b>AIC</b> porównuje rozkłady dopasowane do tej samej próby: mniejszy jest lepszy, a różnica poniżej 2 jest nieistotna. <b>A²</b> Andersona–Darlinga mierzy odległość dystrybuanty od empirycznej z wagą na ogonach: wartość poniżej krytycznej 2,492 (poziom 5%) to ✓. <b>KS p</b> to p-value testu Kołmogorowa–Smirnowa; jest orientacyjne (<code>ks_valid = false</code>), bo parametry oszacowano z tej samej próby.</p>",
    formula:
      '<math display="block"><mi>AIC</mi><mo>=</mo><mn>2</mn><mi>k</mi><mo>−</mo><mn>2</mn><mi>ln</mi><mover><mi>L</mi><mo>^</mo></mover></math><math display="block"><msup><mi>A</mi><mn>2</mn></msup><mo>=</mo><mo>−</mo><mi>n</mi><mo>−</mo><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><mfrac><mrow><mn>2</mn><mi>i</mi><mo>−</mo><mn>1</mn></mrow><mi>n</mi></mfrac><mrow><mo>[</mo><mi>ln</mi><mi>F</mi><mo>(</mo><msub><mi>x</mi><mi>i</mi></msub><mo>)</mo><mo>+</mo><mi>ln</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>F</mi><mo>(</mo><msub><mi>x</mi><mrow><mi>n</mi><mo>+</mo><mn>1</mn><mo>−</mo><mi>i</mi></mrow></msub><mo>)</mo><mo>)</mo><mo>]</mo></mrow></math>',
    vars: [
      { symbol: "<math><mi>k</mi></math>", text: "liczba parametrów rozkładu (2 albo 3)", unit: "–" },
      { symbol: "<math><mover><mi>L</mi><mo>^</mo></mover></math>", text: "największa wiarygodność próby", unit: "–" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba maksimów rocznych", unit: "–" },
      { symbol: "<math><msub><mi>x</mi><mi>i</mi></msub></math>", text: "maksima uszeregowane rosnąco", unit: "m³/s" },
    ],
    note:
      "<p>Brak AIC (—) znaczy, że dopasowany rozkład nie obejmuje któregoś maksimum: jego wiarygodność jest zerowa, a AIC nieskończone. Tak bywa z Weibullem, gdy położenie wypada powyżej najmniejszego maksimum. Wartości krytyczne A² dotyczą rozkładu w pełni określonego, więc i ten test jest przybliżony.</p>",
    sources: "Akaike (1974); Anderson i Darling (1954); Stephens (1974); Hydrolog, <code>hydrolog.statistics.high_flows</code>",
  },
  "stats-plot": {
    title: "Siatka Gumbela i położenie Weibulla",
    intro:
      "<p>Oś pozioma jest liniowa w zmiennej zredukowanej Gumbela <i>u</i>, więc rozkład Gumbela jest na niej prostą, a ogon wezbrań rzadkich jest rozciągnięty. Podpisy osi: prawdopodobieństwo przewyższenia <i>p</i> i okres powtarzalności <i>T</i> = 1/<i>p</i>. Punkty to maksima roczne uszeregowane malejąco, każde w położeniu Weibulla; linie przechodzą przez kwantyle policzone przez Hydrologa.</p>",
    formula:
      '<math display="block"><mi>u</mi><mo>=</mo><mo>−</mo><mi>ln</mi><mo>(</mo><mo>−</mo><mi>ln</mi><mo>(</mo><mn>1</mn><mo>−</mo><mi>p</mi><mo>)</mo><mo>)</mo><mo>,</mo><mspace width="1em"></mspace><msub><mi>p</mi><mi>i</mi></msub><mo>=</mo><mfrac><mi>i</mi><mrow><mi>n</mi><mo>+</mo><mn>1</mn></mrow></mfrac></math>',
    vars: [
      { symbol: "<math><mi>u</mi></math>", text: "zmienna zredukowana Gumbela", unit: "–" },
      { symbol: "<math><msub><mi>p</mi><mi>i</mi></msub></math>", text: "empiryczne prawdopodobieństwo przewyższenia maksimum o pozycji i", unit: "–" },
      { symbol: "<math><mi>i</mi></math>", text: "pozycja w szeregu malejącym (1 to największe maksimum)", unit: "–" },
      { symbol: "<math><mi>n</mi></math>", text: "liczba maksimów rocznych", unit: "–" },
    ],
    sources: "Weibull (1939); Gumbel (1958) Statistics of Extremes; Hydrolog, <code>EmpiricalFrequency</code>",
  },
};
