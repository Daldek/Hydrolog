# Hydrologia stosowana z Hydrologiem

Podręcznik dla studentów, inżynierów i nauczycieli akademickich: zasady działania modeli i
wzorów, z których korzysta Hydrolog, znaczenie zmiennych, zakresy stosowalności, typowe
zastosowania, interpretacja wyników i przykłady na rzeczywistych danych z Polski.

Tekst jest udostępniony na licencji [CC BY 4.0](LICENSE.md): wolno go kopiować, zmieniać i
włączać do własnych skryptów i materiałów dydaktycznych, z podaniem autorstwa („Hydrologia
stosowana z Hydrologiem”, Piotr de Bever i współautorzy, https://github.com/Daldek/Hydrolog).
Kod Hydrologa pozostaje na licencji MIT.

## Jak czytać

- Każdy rozdział zaczyna się od idei fizycznej i założeń, potem podaje wzory z pełnym opisem
  zmiennych i jednostek, zakres stosowalności, typowe zastosowania i błędy, a kończy przykładem.
- Wzory, stałe i zakresy w ramkach oznaczonych jako generowane pochodzą wprost ze specyfikacji
  formuł w kodzie Hydrologa (standard Nogat CMP); nie są przepisywane ręcznie, więc zawsze
  odpowiadają temu, co program liczy.
- Przykład przewodni: zlewnia Kamiennika po przekrój w Świerzawie (dorzecze Kaczawy),
  37,22 km². Prowadzi przez cały łańcuch obliczeń: od charakterystyk zlewni do hydrogramu
  projektowego.
- Każdy przykład podaje polecenie Hydrologa, którym można go powtórzyć.

## Spis treści

1. Zlewnia i jej charakterystyki: powierzchnia, długości, spadki, wskaźniki kształtu, krzywa
   hipsograficzna, sieć rzeczna (rzędowość Strahlera i Shreve’a), gęstość sieci.
2. Opad: opad obszarowy (średnia arytmetyczna, wieloboki Thiessena, IDW, izohiety), opady
   maksymalne o określonym czasie trwania i prawdopodobieństwie przewyższenia PMAXTP
   (IMGW-PIB; to kwantyle, nie opad maksymalny prawdopodobny PMP), hietogramy projektowe
   (blokowy, trójkątny, Beta, Euler typu II).
3. Opad efektywny: metoda SCS-CN (retencja, straty początkowe, warunki wilgotnościowe AMC),
   tablice CN, grupy hydrologiczne gleb (HSG) i klasy uziarnienia USDA.
4. Czas koncentracji: definicje i wzory (Kirpich, NRCS, Giandotti, FAA, Kerby, Kerby–Kirpich),
   zakresy stosowalności, porównanie wyników.
5. Hydrogram jednostkowy: system liniowy i splot; modele SCS, Snydera, Nasha (z parametrami
   Lutza) i Clarka; hydrogram odpływu bezpośredniego i bilans objętości.
6. Transformacja fali wezbraniowej: Muskingum, Muskingum–Cunge, zbiornik (metoda Pulsa),
   kaskada zbiorników liniowych, przesunięcie w czasie; sieć rzeczna; warunki stabilności.
7. Przepływy maksymalne prawdopodobne: rozkłady (GEV, log-normalny, Pearsona typu III,
   Weibulla), estymacja (momenty, L-momenty, największa wiarygodność), formuły pozycji
   wykreślnych, testy zgodności, prawdopodobieństwo przewyższenia i okres powtarzalności.
8. Przepływy charakterystyczne i niżówki: WWQ…NNQ, krzywe czasu trwania, niżówki i deficyty,
   przepływ bazowy (filtr Lyne’a–Hollicka, BFI), recesja.
9. Reżim i zmienność: współczynniki Pardégo, typy reżimu według Dynowskiej, sezonowość
   (statystyka kołowa), analiza harmoniczna, krzywa natężenia przepływu.
10. Jednorodność i trend: testy Manna–Kendalla, Sena, Pettitta, Manna–Whitneya,
    Kołmogorowa–Smirnowa; jak interpretować wynik testu.
11. Wskaźniki meteorologiczne: normy i kompletność danych według WMO, wskaźniki opadowe
    (ETCCDI, PCI, sezonowość), SPI, klasyfikacja Kaczorowskiej, dni charakterystyczne i
    stopniodni, pokrywa śnieżna, ciągi dni suchych i mokrych, współczynnik hydrotermiczny
    Sielianinowa.
12. Studia przypadków na danych rzeczywistych: hydrogram projektowy zlewni Kamiennika;
    statystyka przepływów i opadów stacji IMGW-PIB.

Dodatki: A. Oznaczenia i jednostki · B. Słowniczek polsko-angielski · C. Bibliografia ·
D. Jak Hydrolog sprawdza poprawność wzorów · E. Polecenia Hydrologa a rozdziały podręcznika.

## Stan

W przygotowaniu (plan Nogat `docs/plans/2026-11-18-computation-standard.md`, krok 8).
Rozdziały powstają na podstawie przeglądu literatury przeprowadzonego dla każdej rodziny
wzorów; źródła niedostępne w otwartym dostępie są wymienione w bibliografii z adnotacją.
