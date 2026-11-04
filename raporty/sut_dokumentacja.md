# Dokumentacja SUT — System zarządzania kontem bankowym

**Wariant:** Zespół F  
**Repozytorium:** https://github.com/Mitrivxxx/NSI_P2_2026Z_F  
**Moduł:** `bank.BankSystem`

Dokument opisuje **kontrakt zachowania** systemu (specyfikacja black-box).  
Służy jako podstawa do klas równoważności, wartości brzegowych i tablic decyzyjnych — bez odwoływania się do implementacji.

---

## 1. Opis systemu

System utrzymuje zbiór kont bankowych i umożliwia:

- tworzenie kont,
- blokowanie / odblokowywanie,
- wpłaty i wypłaty,
- przelewy wewnętrzne (między kontami w systemie),
- przelewy zewnętrzne (przez zewnętrzny procesor płatności),
- naliczanie odsetek,
- przegląd historii w okresie,
- wyciąg miesięczny.

Kwoty i salda są wartościami pieniężnymi (dokładność do groszy przy odsetkach).

---

## 2. Pojęcia i stałe

| Pojęcie | Opis |
|---------|------|
| **Konto** | Obiekt o numerze, właścicielu, saldzie, statusie i historii operacji |
| **Status** | `"aktywne"` (domyślnie po utworzeniu) albo `"zablokowane"` |
| **Historia** | Lista wpisów `(data, typ, kwota)` |
| **LIMIT_DZIENNY_WYPLAT** | `5000` — maksymalna suma wypłat i przelewów wychodzących **danego dnia** z jednego konta |
| **Limit systemowy przelewu** | `1 000 000` — maksymalna kwota pojedynczego przelewu wewnętrznego |

### Typy wpisów w historii

| Typ | Znaczenie |
|-----|-----------|
| `wplata` | wpłata |
| `wyplata` | wypłata |
| `przelew_wychodzacy` | przelew wewnętrzny wychodzący |
| `przelew_przychodzacy` | przelew wewnętrzny przychodzący |
| `przelew_zewnetrzny` | przelew poza system |
| `odsetki` | naliczone odsetki |

### Wyjątki domenowe

| Wyjątek | Kiedy |
|---------|--------|
| `ValueError` | niepoprawne dane wejściowe (numer, kwota, limity) |
| `KontoNieIstnieje` | operacja na numerze spoza systemu |
| `KontoZablokowane` | operacja zabroniona przy statusie `"zablokowane"` |
| `ProcesorNiedostepny` | zewnętrzny procesor płatności nie odpowiada |

Przy wyjątku operacja **nie zmienia** salda (transakcja nie dochodzi do skutku).  
Wyjątki z metod publicznych są dodatkowo zapisywane do logu awarii (`logs/awarie.jsonl`).

---

## 3. Numer konta

Numer konta musi spełniać **wszystkie** warunki:

1. typ: napis (`str`),
2. długość: dokładnie **10** znaków,
3. wszystkie znaki to cyfry `0–9`,
4. cyfra kontrolna: ostatnia cyfra = \((\text{suma pierwszych 9 cyfr}) \bmod 10\).

**Przykład:** `123456789` → suma \(45\) → \(45 \bmod 10 = 5\) → numer `"1234567895"`.

Niepoprawny numer przy tworzeniu konta → `ValueError("Nieprawidlowy numer konta")`.

---

## 4. Specyfikacja metod

### 4.1. `utworz_konto(numer, wlasciciel, saldo_poczatkowe=0)`

| | |
|--|--|
| **Wejście** | `numer` — numer konta; `wlasciciel` — nazwa; `saldo_poczatkowe` — saldo startowe (domyślnie 0) |
| **Wynik sukcesu** | obiekt konta; konto jest w systemie, status `"aktywne"`, saldo = `saldo_poczatkowe` |
| **Błędy** | niepoprawny `numer` → `ValueError` |

**Warunki brzegowe / limity:** długość numeru 10; poprawna cyfra kontrolna.

---

### 4.2. `zablokuj_konto(numer)` / `odblokuj_konto(numer)`

| | `zablokuj_konto` | `odblokuj_konto` |
|--|------------------|------------------|
| **Efekt** | status → `"zablokowane"` | status → `"aktywne"` |
| **Błędy** | konto nie istnieje → `KontoNieIstnieje` | to samo |

---

### 4.3. `wplac(numer, kwota)`

| Warunek | Zachowanie |
|---------|------------|
| konto nie istnieje | `KontoNieIstnieje` |
| `kwota ≤ 0` | `ValueError` („Kwota wplaty musi byc dodatnia”) |
| konto istnieje, `kwota > 0` | saldo += kwota; wpis `wplata`; zwraca nowe saldo |

**Uwagi:** status konta (blokada) **nie blokuje** wpłaty.  
**Brzegi kwoty:** `0`, wartości ujemne (odrzucone); najmniejsza poprawna kwota dodatnia (np. `1` / `0.01`).

---

### 4.4. `wyplac(numer, kwota)`

Operacja dozwolona tylko gdy **jednocześnie**:

1. konto istnieje,
2. status = `"aktywne"`,
3. `kwota > 0`,
4. `kwota ≤ saldo`,
5. \(\text{suma dzisiejszych wypłat i przelewów wychodzących} + \text{kwota} \le 5000\).

| Niespełniony warunek | Wyjątek |
|----------------------|---------|
| (1) | `KontoNieIstnieje` |
| (2) | `KontoZablokowane` |
| (3) | `ValueError` (kwota musi być dodatnia) |
| (4) | `ValueError` (niewystarczające środki) |
| (5) | `ValueError` (przekroczono dzienny limit wypłat) |

**Sukces:** saldo -= kwota; wpis `wyplata`; zwraca nowe saldo.

**Do limitu dziennego wliczają się** operacje z **dzisiejszą** datą o typie `wyplata` oraz `przelew_wychodzacy`.  
Wpłaty, odsetki, przelewy przychodzące i operacje z poprzednich dni **nie** zmniejszają dostępnego limitu.

**Brzegi:**

| Warunek | Wartości |
|---------|----------|
| kwota | `-1`, `0`, `1` |
| vs saldo | `saldo` (OK), `saldo + ε` (błąd) |
| vs limit 5000 | suma + kwota = `5000` (OK), `5000 + ε` (błąd) |

---

### 4.5. `przelew(numer_z, numer_do, kwota)`

Przelew wewnętrzny: z konta źródłowego na docelowe **w tym samym systemie**.

Warunki sukcesu (łącznie):

1. `numer_z` istnieje,
2. `numer_do` istnieje,
3. konto źródłowe ma status `"aktywne"`,
4. `kwota > 0`,
5. `kwota ≤ saldo` konta źródłowego,
6. `kwota ≤ 1 000 000`.

| Niespełniony warunek | Wyjątek |
|----------------------|---------|
| (1) lub (2) | `KontoNieIstnieje` |
| (3) | `KontoZablokowane` |
| (4) | `ValueError` (kwota musi być dodatnia) |
| (5) | `ValueError` (niewystarczające środki na koncie źródłowym) |
| (6) | `ValueError` (przelew przekracza dzienny limit systemowy) |

**Sukces:** saldo źródła −= kwota, saldo celu += kwota; wpisy `przelew_wychodzacy` / `przelew_przychodzacy`; zwraca saldo konta źródłowego.

**Uwagi:**

- status konta **docelowego** nie jest sprawdzany przy przelewie wewnętrznym,
- przelew wychodzący **wlicza się** do limitu dziennego wypłat przy kolejnych `wyplac`,
- kwota równa saldu jest dozwolona; kwota równa `1 000 000` jest dozwolona; `1 000 001` — nie.

**Brzegi:** `-1`, `0`, `1`; `saldo` / `saldo+ε`; `1_000_000` / `1_000_001`.

---

### 4.6. `przelew_zewnetrzny(numer_z, numer_konta_docelowego_zewn, kwota, procesor=None)`

Przelew na konto **spoza** systemu, realizowany przez zewnętrzny procesor płatności.

Warunki sukcesu:

1. konto źródłowe istnieje,
2. status źródła = `"aktywne"`,
3. `kwota > 0`,
4. `kwota ≤ saldo`,
5. procesor przyjmuje przelew (nie zgłasza niedostępności).

| Niespełniony warunek | Wyjątek |
|----------------------|---------|
| (1) | `KontoNieIstnieje` |
| (2) | `KontoZablokowane` |
| (3) | `ValueError` (kwota musi być dodatnia) |
| (4) | `ValueError` (niewystarczające środki) |
| (5) | `ProcesorNiedostepny` |

**Sukces:** saldo −= kwota; wpis `przelew_zewnetrzny`; zwraca wynik procesora  
(`{"status": "zaksiegowano", "numer_referencyjny": ...}`).

**Właściwości integracji (kontrakt):**

- **jedna próba** wysyłki — bez ponawiania,
- brak circuit breakera / redundancji (wzmocnienie to zadanie osobnego bloku),
- jeśli `procesor` nie podano, używany jest domyślny procesor (może zawodzić losowo).

**Brzegi kwoty:** jak przy wypłacie (`0`, `1`, równe saldu, ponad saldo).

---

### 4.7. `nalicz_odsetki(numer, roczna_stopa_procentowa, miesiace)`

| | |
|--|--|
| **Wejście** | konto, roczna stopa w %, liczba miesięcy (całkowita) |
| **Wzór** | miesięcznie: \(\text{odsetki} = \mathrm{round}(\text{saldo} \cdot \frac{\text{stopa}}{12 \cdot 100},\, 2)\) (zaokrąglenie half-up); saldo += odsetki; powtórz `miesiace` razy |
| **Sukces** | zwraca saldo po naliczeniu; wpisy typu `odsetki` |
| **Błędy** | konto nie istnieje → `KontoNieIstnieje`; niepoprawny typ stopy / miesięcy → błąd konwersji / typu |

**Brzegi:** `miesiace = 0` (brak zmiany); `miesiace = 1`; stopa `0`.

---

### 4.8. `historia_w_okresie(numer, od, do)`

| | |
|--|--|
| **Wejście** | numer konta; `od`, `do` — daty (`date`) |
| **Wynik** | lista wpisów historii, dla których `od ≤ data ≤ do` |
| **Błędy** | konto nie istnieje → `KontoNieIstnieje` |

**Brzegi dat:** operacja w dniu `od`, w dniu `do`, dzień przed `od`, dzień po `do`.  
Pusty wynik, gdy w zakresie nie ma operacji.

---

### 4.9. `wyciag_miesieczny(numer, rok, miesiac)`

| | |
|--|--|
| **Wejście** | numer, rok, miesiąc (1–12) |
| **Wynik** | słownik `{"wplaty", "wyplaty", "saldo_koncowe"}` |
| **wplaty** | suma typów: `wplata`, `przelew_przychodzacy`, `odsetki` w danym miesiącu |
| **wyplaty** | suma typów: `wyplata`, `przelew_wychodzacy` w danym miesiącu |
| **saldo_koncowe** | bieżące saldo konta |
| **Błędy** | konto nie istnieje → `KontoNieIstnieje` |

---

## 5. Zewnętrzny procesor płatności

Klasa `ZewnetrznyProcesor`:

- symuluje izbę rozliczeniową / bramkę przelewów zewnętrznych,
- parametr `prawdopodobienstwo_awarii` (domyślnie `0.3`) — przy wylosowanej awarii rzuca `ProcesorNiedostepny`,
- opcjonalne opóźnienie `opoznienie_s`,
- to **świadomie kruchy** punkt integracji, nie ukryta usterka do „znalezienia” w kodzie.

W testach deterministycznych należy przekazywać własny procesor (np. awaria zawsze / nigdy).

---

## 6. Podsumowanie limitów i brzegów

| Obszar | Limit / warunek | Brzegi do testów |
|--------|-----------------|------------------|
| Numer konta | długość 10, cyfry, kontrolna | 9 / 10 / 11 znaków; zła kontrolna; litery |
| Kwota (wpłata, wypłata, przelewy) | `> 0` | `-1`, `0`, `1` |
| Wypłata / przelew vs saldo | `≤ saldo` | `saldo`, `saldo+ε` |
| Limit dzienny wypłat | suma dnia + kwota `≤ 5000` | `5000`, `5000+ε` |
| Przelew wewnętrzny | kwota `≤ 1 000 000` | `1e6`, `1e6+1` |
| Historia | `od ≤ data ≤ do` | równość `od`/`do`, poza zakresem |
| Odsetki | `miesiace` powtórzeń | `0`, `1` |

---

## 7. Metody a zależność od wielu warunków

Metody szczególnie nadające się do **tablicy decyzyjnej**:

- `wyplac` — istnienie, status, kwota, saldo, limit dzienny,
- `przelew` — dwa konta, status źródła, kwota, saldo, limit 1 mln,
- `przelew_zewnetrzny` — istnienie, status, kwota, saldo, dostępność procesora.

---

*Dokumentacja kontraktowa SUT (Zespół F). Aktualizować przy zmianie reguł biznesowych.*
