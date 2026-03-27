# Raport Hydrologiczny: Zlewnia miejska

**Data wygenerowania:** 2026-03-22
**Wygenerowano przez:** Hydrolog v0.6.2

---


## 3. Hietogram Opadu

Hietogram przedstawia rozkład czasowy opadu. Poniżej zamieszczono parametry
opadu oraz jego rozkład w kolejnych krokach czasowych.


### 3.1 Parametry opadu

| Parametr | Wartość | Jednostka |
|:---------|--------:|:---------:|
| Opad całkowity P | 28.00 | mm |
| Czas trwania | 15.0 | min |
| Krok czasowy | 1.0 | min |
| Liczba kroków | 15 | - |
| Średnia intensywność | 112.00 | mm/h |
| Intensywność szczytowa | 269.37 | mm/h |
| Czas szczytu | 4.0 | min |

**Typ rozkładu:** Rozkład Beta

### 3.2 Rozkład czasowy

| Czas [min] | P [mm] | P kum. [mm] | Intensywność [mm/h] |
|--------:|------:|------:|------:|
| 1.0 | 1.62 | 1.62 | 97.26 |
| 2.0 | 3.65 | 5.27 | 219.24 |
| 3.0 | 4.48 | 9.75 | 268.58 |
| 4.0 | 4.49 | 14.24 | 269.37 |
| 5.0 | 4.01 | 18.25 | 240.69 |
| 6.0 | 3.29 | 21.54 | 197.13 |
| 7.0 | 2.49 | 24.03 | 149.31 |
| 8.0 | 1.74 | 25.77 | 104.42 |
| 9.0 | 1.11 | 26.88 | 66.77 |
| 10.0 | 0.64 | 27.52 | 38.25 |
| 11.0 | 0.32 | 27.83 | 18.95 |
| 12.0 | 0.13 | 27.96 | 7.59 |
| 13.0 | 0.04 | 27.99 | 2.15 |
| 14.0 | 0.01 | 28.00 | 0.30 |
| 15.0 | 0.00 | 28.00 | 0.00 |

## 4. Opad Efektywny (SCS-CN)

Metoda SCS-CN (Soil Conservation Service - Curve Number) służy do obliczania
opadu efektywnego na podstawie charakterystyki zlewni wyrażonej liczbą CN.
Opad efektywny to ta część opadu, która bezpośrednio zasila odpływ powierzchniowy.


### 4.1 Parametry metody

- Curve Number dla AMC-II: **CN = 79**
- Warunki wilgotnościowe: **AMC-II** (warunki normalne/przeciętne)
- CN używany w obliczeniach: **CN = 79**

### 4.2 Retencja maksymalna

Retencja maksymalna S określa zdolność retencyjną zlewni:

$$S = \frac{25400}{CN} - 254 = \frac{25400}{79} - 254 = 67.52 \text{ mm}$$

### 4.3 Abstrakcja początkowa

Abstrakcja początkowa obejmuje intercepcję, zwilżenie powierzchni i retencję w zagłębieniach terenu:

$$I_a = \lambda \cdot S = 0.2 \cdot 67.52 = 13.50 \text{ mm}$$

### 4.4 Opad efektywny

Dla opadu całkowitego P = 28.00 mm:

$$P_e = \frac{(P - I_a)^2}{P - I_a + S} = \frac{(28.00 - 13.50)^2}{28.00 - 13.50 + 67.52} = \frac{14.50^2}{82.02} = 2.56 \text{ mm}$$

### 4.5 Rozkład opadu efektywnego w czasie

| Czas [min] | P [mm] | P kum. [mm] | Pe [mm] | Pe kum. [mm] |
|--------:|------:|------:|------:|------:|
| 1.0 | 1.62 | 1.62 | 0.00 | 0.00 |
| 2.0 | 3.65 | 5.27 | 0.00 | 0.00 |
| 3.0 | 4.48 | 9.75 | 0.00 | 0.00 |
| 4.0 | 4.49 | 14.24 | 0.01 | 0.01 |
| 5.0 | 4.01 | 18.25 | 0.30 | 0.31 |
| 6.0 | 3.29 | 21.54 | 0.54 | 0.85 |
| 7.0 | 2.49 | 24.03 | 0.56 | 1.42 |
| 8.0 | 1.74 | 25.77 | 0.47 | 1.88 |
| 9.0 | 1.11 | 26.88 | 0.33 | 2.21 |
| 10.0 | 0.64 | 27.52 | 0.20 | 2.41 |
| 11.0 | 0.32 | 27.83 | 0.10 | 2.51 |
| 12.0 | 0.13 | 27.96 | 0.04 | 2.55 |
| 13.0 | 0.04 | 27.99 | 0.01 | 2.56 |
| 14.0 | 0.01 | 28.00 | 0.00 | 2.56 |
| 15.0 | 0.00 | 28.00 | 0.00 | 2.56 |

**Podsumowanie:**

| Parametr | Wartość |
|:---------|--------:|
| Opad całkowity P | 28.00 mm |
| Retencja maksymalna S | 67.52 mm |
| Abstrakcja początkowa Ia | 13.50 mm |
| **Opad efektywny Pe** | **2.56 mm** |

## 5. Hydrogram Jednostkowy

Hydrogram jednostkowy przedstawia odpowiedź zlewni na jednostkowy opad efektywny
(1 mm) o określonym czasie trwania. Służy do transformacji opadu efektywnego
w hydrogram odpływu metodą splotu (konwolucji).


### 5.1 Model

**Model kaskady zbiorników Nasha (IUH)**

### 5.2 Parametry modelu

- Powierzchnia zlewni: A = 3.46 km²
- Liczba zbiorników: n = 1.32
- Stała zbiornika: K = 30.7 min = 0.511 h
- Czas opóźnienia: tlag = n × K = 40.3 min

**Chwilowy hydrogram jednostkowy (IUH):**

**Metoda estymacji parametrów: regresja dla zlewni zurbanizowanych (Rao, Delleur, Sarma 1972)**

**Parametry wejściowe:**

| Parametr | Wartość | Jednostka |
|:---------|--------:|:---------:|
| Powierzchnia zlewni A | 3.460 | km² |
| Wskaźnik urbanizacji U | 0.310 | - |
| Opad efektywny H | 2.562 | mm |
| Czas trwania opadu D | 0.2500 | h |

**Krok 1: Czas opóźnienia $t_L$**

$$t_L = 1{,}28 \cdot A^{0{,}46} \cdot (1+U)^{-1{,}66} \cdot H^{-0{,}27} \cdot D^{0{,}37} \text{ [h]}$$

$$t_L = 1{,}28 \cdot 3.460^{0{,}46} \cdot 1.310^{-1{,}66} \cdot 2.562^{-0{,}27} \cdot 0.2500^{0{,}37} = 0.6721 \text{ h}$$

**Krok 2: Stała zbiornika $k$**

$$k = 0{,}56 \cdot A^{0{,}39} \cdot (1+U)^{-0{,}62} \cdot H^{-0{,}11} \cdot D^{0{,}22} \text{ [h]}$$

$$k = 0{,}56 \cdot 3.460^{0{,}39} \cdot 1.310^{-0{,}62} \cdot 2.562^{-0{,}11} \cdot 0.2500^{0{,}22} = 0.5109 \text{ h} = 30.65 \text{ min}$$

**Krok 3: Liczba zbiorników $N$**

$$N = \frac{t_L}{k}$$

$$N = \frac{0.6721}{0.5109} = 1.316$$

*Źródło: Rao, R.A.; Delleur, J.W.; Sarma, B.S.P. (1972). Conceptual Hydrologic Models for Urbanizing Basins. Journal of the Hydraulics Division, ASCE, 98(HY7), 1205–1220.*

**Wzór IUH Nasha (wyznaczone parametry):**

**Wzór IUH Nasha:**

$$u(t) = \frac{1}{K \cdot \Gamma(n)} \cdot \left(\frac{t}{K}\right)^{n-1} \cdot e^{-t/K}$$

**Parametry modelu:**

- $n$ = 1.32 (liczba zbiorników)
- $K$ = 30.7 min = 0.511 h (stała zbiornika)
- $t_{lag}$ = n × K = 40.3 min

**Czas do szczytu IUH:**

$$t_p = (n - 1) \cdot K = (1.32 - 1) \cdot 30.7 = 9.7 \text{ min}$$

### 5.4 Rzędne hydrogramu jednostkowego

| Czas [min] | q [m³/s/mm] |
|--------:|--------:|
| 0.0 | 0.0000 |
| 1.0 | 0.4208 |
| 2.1 | 0.8416 |
| 3.1 | 1.2624 |
| 4.2 | 1.6832 |
| 5.2 | 2.1040 |
| 6.2 | 2.5247 |
| 7.3 | 2.9455 |
| 8.3 | 3.3663 |
| 9.4 | 3.7871 |
| 10.4 | 4.2079 |
| 11.5 | 4.6287 |
| 12.5 | 4.7465 |
| 13.5 | 4.6413 |
| 14.6 | 4.5361 |
| 15.6 | 4.4309 |
| 16.7 | 4.3257 |
| 17.7 | 4.2205 |
| 18.8 | 4.1153 |
| 19.8 | 4.0101 |
| 20.8 | 3.9049 |
| 21.9 | 3.7997 |
| 22.9 | 3.6946 |
| 24.0 | 3.5894 |
| 25.0 | 3.4842 |

**Charakterystyki hydrogramu jednostkowego:**

| Parametr | Wartość |
|:---------|--------:|
| Czas do szczytu tp | 11.9 min |
| Przepływ szczytowy qp | 4.8071 m³/s/mm |
| Powierzchnia zlewni A | 3.46 km² |

## 6. Splot Dyskretny (Konwolucja)

Hydrogram odpływu bezpośredniego obliczany jest jako splot dyskretny (konwolucja)
opadu efektywnego z hydrogramem jednostkowym.


### 6.1 Wzór

**Splot dyskretny (konwolucja):**

$$Q(n) = \sum_{m=1}^{\min(n,M)} P_e(m) \cdot UH(n - m + 1)$$

gdzie:
- $Q(n)$ - przepływ w kroku czasowym n [m³/s]
- $P_e(m)$ - opad efektywny w kroku m [mm]
- $UH(k)$ - rzędna hydrogramu jednostkowego [m³/s/mm]
- $M$ - liczba kroków opadu

### 6.2 Opis procedury

Procedura splotu dyskretnego:

1. Opad efektywny Pe(t) dzielony jest na przyrosty w kolejnych krokach czasowych
2. Każdy przyrost opadu generuje odpływ proporcjonalny do hydrogramu jednostkowego
3. Odpływy cząstkowe są sumowane (superpozycja) dając wynikowy hydrogram

**Parametry procedury:**

| Parametr | Wartość |
|:---------|--------:|
| Liczba kroków opadu efektywnego (M) | 15 |
| Liczba rzędnych hydrogramu jednostkowego (N) | 181 |
| Liczba kroków wynikowego hydrogramu | 195 |
| Krok czasowy Δt | 1.0 min |
| Całkowity czas trwania hydrogramu | 195.0 min |

**Uwaga:** Długość wynikowego hydrogramu = M + N - 1 kroków czasowych.

## 7. Wyniki - Hydrogram Odpływu

Poniżej przedstawiono charakterystyki obliczonego hydrogramu odpływu bezpośredniego.

### 7.1 Charakterystyki

| Charakterystyka | Wartość | Jednostka |
|:----------------|--------:|:---------:|
| Przepływ szczytowy Qmax | 2.71 | m³/s |
| Czas do szczytu tp | 17.0 | min |
| Objętość odpływu V | 8,814 | m³ |

### 7.2 Szereg czasowy

| Czas [min] | Q [m³/s] |
|--------:|--------:|
| 0.0 | 0.000 |
| 1.0 | 0.000 |
| 2.0 | 0.000 |
| 3.0 | 0.000 |
| 4.0 | 0.004 |
| 5.0 | 0.168 |
| 6.0 | 0.529 |
| 7.0 | 0.991 |
| 8.0 | 1.452 |
| 9.0 | 1.848 |
| 10.0 | 2.153 |
| 11.0 | 2.369 |
| 12.0 | 2.511 |
| 13.0 | 2.602 |
| 14.0 | 2.657 |
| 15.0 | 2.691 |
| 16.0 | 2.708 |
| 17.0 | 2.713 |
| 18.0 | 2.709 |
| 19.0 | 2.697 |
| ... | ... |
| 176.0 | 0.037 |
| 177.0 | 0.036 |
| 178.0 | 0.035 |
| 179.0 | 0.034 |
| 180.0 | 0.033 |
| 181.0 | 0.032 |
| 182.0 | 0.031 |
| 183.0 | 0.030 |
| 184.0 | 0.029 |
| 185.0 | 0.025 |
| 186.0 | 0.019 |
| 187.0 | 0.012 |
| 188.0 | 0.007 |
| 189.0 | 0.004 |
| 190.0 | 0.002 |
| 191.0 | 0.001 |
| 192.0 | 0.000 |
| 193.0 | 0.000 |
| 194.0 | 0.000 |

*Tabela skrócona (195 wierszy)*

## 8. Bilans Wodny

Bilans wodny przedstawia podział opadu całkowitego na poszczególne składniki:
abstrakcję początkową, infiltrację oraz opad efektywny (odpływ).


### 8.1 Podsumowanie bilansu

| Składnik bilansu | Wartość [mm] | Udział [%] |
|:-----------------|-------------:|-----------:|
| Opad całkowity P | 28.00 | 100.0 |
| Abstrakcja początkowa Ia | 13.50 | 48.2 |
| Infiltracja F | 11.93 | 42.6 |
| **Opad efektywny Pe** | **2.56** | **9.2** |

### 8.2 Współczynnik odpływu

$$C = \frac{P_e}{P} = \frac{2.56}{28.00} = 0.092$$

**Weryfikacja objętościowa:**

- Objętość opadu efektywnego: $V_{Pe}$ = Pe × A = 2.56 mm × 3.46 km² = 8,865 m³
- Objętość z hydrogramu: $V_Q$ = 8,814 m³
- Bilans: ✓ zgodność (0.58% różnicy)

---

**Podsumowanie bilansu wodnego:**

| | Wartość |
|:--|--------:|
| Opad całkowity P | 28.00 mm |
| Opad efektywny Pe | 2.56 mm |
| Straty (Ia + F) | 25.44 mm |
| Współczynnik odpływu C | 0.092 (9.2%) |
| Objętość odpływu V | 8,814 m³ |