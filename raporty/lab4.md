# Lab 4 — testowanie czarnoskrzynkowe (BVA + tablica decyzyjna)

**SUT:** System zarządzania kontem bankowym (Zespół F)  
**Źródło reguł:** [`sut_dokumentacja.md`](sut_dokumentacja.md) (kontrakt, nie kod)  
**Testy:** `tests/test_lab4.py`

## Wybór metod

Na zajęciach 2 i 3 szczegółowo analizowano `wplac`, `wyplac`, `przelew`. W lab 4 wybrane **dwie inne** metody:

| Metoda | Technika |
|--------|----------|
| `utworz_konto` | klasy równoważności + wartości brzegowe |
| `przelew_zewnetrzny` | klasy równoważności + BVA + **tablica decyzyjna** |

---

## 1. Klasy równoważności i wartości brzegowe

### 1.1. `utworz_konto(numer, wlasciciel, saldo_poczatkowe)`

#### Klasy równoważności — `numer`

| Opis | Reprezentant | Oczekiwanie | Test |
|------|--------------|-------------|------|
| długość ≠ 10 | 9 / 11 znaków | `ValueError` | `test_bva_numer_9_znakow`, `…_11_znakow` |
| długość 10, zła cyfra kontrolna | `"1111111110"` | `ValueError` | `test_ec_numer_zla_cyfra_kontrolna` |
| długość 10, poprawna kontrolna | `"1111111119"` | sukces | `test_bva_numer_10_znakow` |

#### Wartości brzegowe — długość `numer` (limit: dokładnie 10)

| Brzeg | Reprezentant | Oczekiwanie | Test |
|-------|--------------|-------------|------|
| tuż poniżej | `"123456789"` (9) | `ValueError` | `test_bva_numer_9_znakow` |
| na granicy | `"1111111119"` (10) | sukces, status aktywne | `test_bva_numer_10_znakow` |
| tuż powyżej | `"12345678901"` (11) | `ValueError` | `test_bva_numer_11_znakow` |

#### Klasy równoważności — `saldo_poczatkowe`

| Opis | Reprezentant | Oczekiwanie (dokumentacja) | Test |
|------|--------------|----------------------------|------|
| saldo = 0 | `0` | sukces | `test_bva_saldo_zero` |
| saldo > 0 | `0.01` | sukces | `test_bva_saldo_tuż_powyzej_zera` |
| saldo < 0 | `−1` | nieuregulowane | `test_bva_saldo_tuż_ponizej_zera` |

#### Wartości brzegowe — `saldo_poczatkowe` (okolice zera)

| Brzeg | Reprezentant | Oczekiwanie | Test |
|-------|--------------|-------------|------|
| zero | `0` | saldo = 0 | `test_bva_saldo_zero` |
| tuż powyżej 0 | `0.01` | saldo = 0.01 | `test_bva_saldo_tuż_powyzej_zera` |
| tuż poniżej 0 | `−1` | fakt: saldo = −1 | `test_bva_saldo_tuż_ponizej_zera` |

---

### 1.2. `przelew_zewnetrzny` — parametr `kwota`

Dokumentacja: `kwota > 0` oraz `kwota ≤ saldo`.

#### Klasy równoważności

| Opis | Reprezentant | Oczekiwanie | Test |
|------|--------------|-------------|------|
| `kwota ≤ 0` | `0`, `−1` | `ValueError` | `test_bva_kwota_zero`, `…_ujemna` |
| `0 < kwota ≤ saldo` | `1`, `=saldo` | sukces | `test_bva_kwota_jeden`, `…_rowna_saldu` |
| `kwota > saldo` | `saldo+0.01` | `ValueError` | `test_bva_kwota_powyzej_salda` |

#### Wartości brzegowe

| Brzeg | Reprezentant | Oczekiwanie | Test |
|-------|--------------|-------------|------|
| zero | `0` | `ValueError` | `test_bva_kwota_zero` |
| tuż poniżej 0 | `−1` | `ValueError` | `test_bva_kwota_ujemna` |
| najmniejsza dodatnia | `1` | sukces | `test_bva_kwota_jeden` |
| równa saldu | `1000` | sukces, saldo 0 | `test_bva_kwota_rowna_saldu` |
| tuż ponad saldo | `1000.01` | `ValueError` | `test_bva_kwota_powyzej_salda` |

---

## 2. Tablica decyzyjna — `przelew_zewnetrzny`

Zachowanie zależy od kilku warunków jednocześnie (sekcja 4.6 dokumentacji).  
Tablica ograniczona: jedna niespełniona przyczyna na regułę + reguła sukcesu.

| Warunek | konto nie istnieje | konto zablokowane | kwota ≤ 0 | kwota > saldo | procesor niedostępny | wszystkie warunki OK |
|---------|--------------------|-------------------|-----------|---------------|----------------------|----------------------|
| konto źródłowe istnieje | N | T | T | T | T | T |
| status = `"aktywne"` | — | N | T | T | T | T |
| `kwota > 0` | — | — | N | T | T | T |
| `kwota ≤ saldo` | — | — | — | N | T | T |
| procesor dostępny | — | — | — | — | N | T |
| **Wynik** | `KontoNieIstnieje` | `KontoZablokowane` | `ValueError` (kwota) | `ValueError` (środki) | `ProcesorNiedostepny` | sukces |
| **Saldo** | bez zmian | bez zmian | bez zmian | bez zmian | bez zmian | −kwota |

| Co oznacza | Test |
|------------|------|
| konto nie istnieje | `test_r1_konto_nie_istnieje` |
| konto zablokowane | `test_r2_konto_zablokowane` |
| kwota ≤ 0 | `test_r3_kwota_niedodatnia` |
| kwota > saldo | `test_r4_kwota_powyzej_salda` |
| procesor niedostępny | `test_r5_procesor_niedostepny` |
| wszystkie warunki OK | `test_r6_sukces` |

---

## 3. Rozbieżności dokumentacja ↔ zachowanie

| # | Opis | Dokumentacja | Faktyczne zachowanie | Ocena |
|---|------|--------------|----------------------|--------|
| 1 | Saldo początkowe ujemne | Nie zabrania ani nie wymaga `≥ 0` | `utworz_konto(..., -1)` tworzy konto z saldem `-1` | **Luka w specyfikacji** |
| 2 | Ponowne `utworz_konto` tym samym numerem | Brak reguły unikalności | Drugie wywołanie **nadpisuje** poprzednie konto | **Luka w specyfikacji** |
| 3 | Brzegi kwoty przelewu zewnętrznego | `kwota > 0`, `kwota ≤ saldo` | 0/−1/saldo+ε → błąd; 1 i =saldo → sukces | **Zgodne** |
| 4 | Tablica decyzyjna | wyjątki jak w sekcji 4.6 | typy wyjątków zgodne; przy błędzie saldo bez zmian | **Zgodne** |

---

## 4. Wnioski: podejście czarnoskrzynkowe vs testy strukturalne

1. **Luki w kontrakcie** — ujemne saldo startowe i brak unikalności numeru widać dopiero przy pytaniu „co mówi dokumentacja?”; white-box sprawdza gałęzie kodu, a nie kompletność specyfikacji.
2. **Kwota przy limicie salda** — para `saldo` / `saldo+0.01` pokazuje dokładną granicę akceptacji, nie tylko „jakiś błąd przy za dużej kwocie”.
3. **Tablica decyzyjna** — łączy warunki (status + kwota + procesor), których izolowane testy strukturalne często nie składają w pełny scenariusz; niedostępność procesora to zachowanie integracyjne niewidoczne w samym pokryciu linii SUT.

**Podsumowanie:** BVA i tablica decyzyjna uzupełniają pokrycie strukturalne o zgodność z limitami ze specyfikacji i ujawniają niedopowiedzenia dokumentacji.
