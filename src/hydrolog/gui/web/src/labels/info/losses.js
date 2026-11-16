/**
 * Explanation (i) of the SCS-CN losses, by Nogat DEV-15.14: the entry "losses-scs-cn" for CN,
 * AMC and λ of `hydrograph generate` and `scs effective`, in the format of ui/info.js, linking
 * (`guide`) its subsection of the guide's chapter „Metody obliczeń”. The typical range of the
 * AMC conversion, with its source, is Hydrolog's (`typical_ranges`, method `scs_cn_amc`).
 */

export const lossesInfo = {
  "losses-scs-cn": {
    title: "SCS-CN: opad efektywny",
    intro:
      "<p>Opad efektywny P<sub>e</sub> to część opadu, która odpływa po powierzchni terenu; reszta wsiąka w " +
      "glebę lub zostaje zatrzymana przez roślinność i zagłębienia terenu. Metoda SCS-CN liczy go z liczby " +
      "krzywej CN dla przeciętnej wilgotności gleby (AMC II).</p>",
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
        text: "opad całkowity; w hietogramie suma narastająca od początku opadu",
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
        text: "współczynnik strat początkowych, 0 &lt; λ ≤ 1; standardowo 0,2",
        unit: "–",
      },
      {
        symbol: "<math><mi>CN</mi></math>",
        text: "liczba krzywej odpływu dla AMC II, 1–100; dla AMC I i III przeliczona i zaokrąglona do jedności",
        unit: "–",
      },
    ],
    symbols: { cn: "CN (AMC I i III)" },
    note:
      "<p>Im wyższy CN, tym większa część opadu odpływa: przy CN = 80 z opadu 50&nbsp;mm odpływa około " +
      "14&nbsp;mm. Sucha gleba (AMC I) obniża CN, mokra (AMC III) go podwyższa.</p>",
    guide: "metoda-losses-scs-cn",
    sources:
      "USDA-SCS 1986 (TR-55); USDA-NRCS 2004 (NEH 630, rozdz. 10); Hawkins i in. 1985 (za Ponce i Hawkins " +
      "1996)",
  },
};
