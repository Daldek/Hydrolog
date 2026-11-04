/**
 * Explanation (i) of the SCS-CN losses (plan D16, slice S3): the entry "losses-scs-cn" for the
 * options `cn`, `amc` and `ia_coefficient` of `hydrograph generate` and `scs effective`, in the
 * format of ui/info.js. The typical range of the AMC conversion, with its source, is
 * Hydrolog's (`typical_ranges`, method `scs_cn_amc`).
 */

export const lossesInfo = {
  "losses-scs-cn": {
    title: "SCS-CN: opad efektywny",
    intro:
      "<p>Straty i opad efektywny z liczby krzywej CN; CN podaje się dla przeciętnej wilgotności AMC II, " +
      "a AMC I i III go przeliczają. Polecenie <code>scs effective</code>, w hydrogramie opcje " +
      "<code>cn</code>, <code>amc</code> i <code>ia_coefficient</code>.</p>" +
      "<p>W hydrogramie P to suma opadu narastająca od początku: P<sub>e</sub> liczy się po każdym " +
      "kroku, a jego przyrosty w krokach idą do splotu z hydrogramem jednostkowym.</p>",
    formula:
      "<math display='block'><msub><mi>P</mi><mi>e</mi></msub><mo>=</mo><mfrac><msup><mrow><mo>(</mo>" +
      "<mi>P</mi><mo>−</mo><msub><mi>I</mi><mi>a</mi></msub><mo>)</mo></mrow><mn>2</mn></msup><mrow>" +
      "<mi>P</mi><mo>−</mo><msub><mi>I</mi><mi>a</mi></msub><mo>+</mo><mi>S</mi></mrow></mfrac>" +
      "<mspace width='1em'></mspace><mtext>dla</mtext><mspace width='0.4em'></mspace><mi>P</mi>" +
      "<mo>&gt;</mo><msub><mi>I</mi><mi>a</mi></msub><mo>;</mo><mspace width='1em'></mspace>" +
      "<msub><mi>P</mi><mi>e</mi></msub><mo>=</mo><mn>0</mn><mspace width='0.6em'></mspace>" +
      "<mtext>dla</mtext><mspace width='0.4em'></mspace><mi>P</mi><mo>≤</mo><msub><mi>I</mi><mi>a</mi>" +
      "</msub></math>" +
      "<math display='block'><mi>S</mi><mo>=</mo><mfrac><mn>25400</mn><mi>CN</mi></mfrac><mo>−</mo>" +
      "<mn>254</mn><mspace width='1.5em'></mspace><msub><mi>I</mi><mi>a</mi></msub><mo>=</mo><mi>λ</mi>" +
      "<mo>·</mo><mi>S</mi></math>" +
      "<math display='block'><msub><mi>CN</mi><mtext>I</mtext></msub><mo>=</mo><mfrac><mi>CN</mi>" +
      "<mrow><mn>2,281</mn><mo>−</mo><mn>0,01281</mn><mo>·</mo><mi>CN</mi></mrow></mfrac></math>" +
      "<math display='block'><msub><mi>CN</mi><mtext>III</mtext></msub><mo>=</mo><mfrac><mi>CN</mi>" +
      "<mrow><mn>0,427</mn><mo>+</mo><mn>0,00573</mn><mo>·</mo><mi>CN</mi></mrow></mfrac></math>",
    vars: [
      {
        symbol: "<math><mi>P</mi></math>",
        text:
          "opad: suma narastająca od początku opadu (w <code>scs effective</code> z " +
          "<code>precipitation_mm</code> – suma całego opadu)",
        unit: "mm",
      },
      {
        symbol: "<math><msub><mi>P</mi><mi>e</mi></msub></math>",
        text: "opad efektywny (odpływ bezpośredni)",
        unit: "mm",
      },
      {
        symbol: "<math><mi>S</mi></math>",
        text: "retencja maksymalna zlewni; dla CN = 100: S = 0 i cały opad odpływa",
        unit: "mm",
      },
      {
        symbol: "<math><msub><mi>I</mi><mi>a</mi></msub></math>",
        text: "straty początkowe: intercepcja, retencja w zagłębieniach terenu i wsiąkanie przed początkiem odpływu",
        unit: "mm",
      },
      {
        symbol: "<math><mi>λ</mi></math>",
        text: "współczynnik strat początkowych, <code>ia_coefficient</code>, 0 &lt; λ ≤ 1; domyślnie 0,2",
        unit: "–",
      },
      {
        symbol: "<math><mi>CN</mi></math>",
        text:
          "liczba krzywej dla AMC II, 1–100 (może być ułamkowa): <code>cn</code> zlewni albo opcja " +
          "<code>cn</code>; przy <code>amc</code> I lub III Hydrolog liczy CN<sub>I</sub> albo " +
          "CN<sub>III</sub>, zaokrągla do liczby całkowitej i ogranicza do 1–100",
        unit: "–",
      },
    ],
    symbols: { cn: "CN (AMC I i III)" },
    note:
      "<p>λ = 0,2 to standard NRCS, dla którego skalibrowano tablice CN (TR-55, NEH 630); inny λ daje " +
      "uwagę w wyniku. Proponowanej wartości 0,05 (Hawkins i in. 2002; Woodward i in. 2003) NRCS nie " +
      "przyjęło: wymagałaby innych wartości CN. Wzory przeliczenia AMC przybliżają tabelę NEH 630 w " +
      "zakresie stosowania podanym wyżej; Hydrolog stosuje je dla każdego CN, a poza tym zakresem daje uwagę. " +
      "Przy odpływie poniżej ok. 13 mm metoda jest mniej dokładna.</p>",
    sources:
      "USDA-SCS 1986 (TR-55); USDA-NRCS 2004 (NEH 630-10); Hawkins i in. 1985 (za Ponce i Hawkins 1996); " +
      "Hawkins i in. 2002; Woodward i in. 2003; opis polecenia <code>scs effective</code>",
  },
};
