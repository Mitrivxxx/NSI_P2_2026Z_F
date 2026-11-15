# Lab 5


## 1. Test współbieżności — opis

Test sprawdza, czy niezmienniki konta są zachowane, gdy wiele wątków wykonuje operacje na tym samym koncie jednocześnie. Wątki startują razem dzięki `threading.Barrier`, więc ich wywołania się nakładają.

- **domyślny** — domyślne przełączanie wątków CPython (5 ms),
- **agresywny** — `sys.setswitchinterval(1e-6)`. Interpreter przełącza wątki znacznie częściej, więc przeplatanie się operacji wewnątrz metod jest bardziej prawdopodobne. Wariant ten nie zmienia logiki SUT, tylko zwiększa szansę na wyścig.

Log awarii (`bank/logger.py`) jest przekierowany do pliku tymczasowego, żeby nie zaśmiecać `logs/awarie.jsonl`.

| Scenariusz | Operacje | Niezmiennik |
|---|---|---|
| S1 wplac współbieżnie | 8 wątków × 500 × `wplac(1)` na koncie 1000 | saldo = 1000 + 4000; liczba wpisów `wplata` = 4000 |
| S2 wyplac poniżej zera | 20 wątków × 10 prób `wyplac(10)` na koncie 1000 | dokładnie 100 wypłat, saldo = 0 (nigdy ujemne) |
| S3 limit dzienny | 20 wątków × 50 prób `wyplac(100)` na koncie 10 000 | suma dzisiejszych wypłat ≤ 5000; dokładnie 50 wypłat |
| S4 przelew zewnętrzny | 20 wątków × 10 prób `przelew_zewnetrzny(10)` na koncie 1000, procesor z opóźnieniem 1 ms, bez awarii | dokładnie 100 przelewów, saldo = 0 |
| S5 kontrola | 8 wątków × 200 × `przelew(1)` między dwoma kontami | suma sald = 2000 (metoda `przelew` ma `self._lock`) |


## 2. Wynik wielokrotnego uruchomienia

Każdy scenariusz uruchomiono **100 razy** w każdym wariancie.

| Scenariusz | Domyślny (5 ms) | Agresywny (1 µs) | Średni czas uruchomienia (domyślny / agresywny) |
|---|:---:|:---:|---|
| S1 wplac współbieżnie | **100/100** | **100/100** | 9,3 ms / 79 ms |
| S2 wyplac poniżej zera | **100/100** | **0/100** | 31 ms / 64 ms |
| S3 limit dzienny wypłat | **100/100** | **12/100** | 212 ms / 775 ms |
| S4 przelew zewnętrzny | **0/100** | **0/100** | 40 ms / 199 ms |
| S5 kontrola (z lockiem) | **100/100** | **100/100** | 13 ms / 27 ms |


---

## 3. Czas wykonania i przepustowość

Pomiar: `python tests/pomiar_lab5.py`. Każda konfiguracja powtórzona **3 razy**, w tabeli mediana. Czas mierzony `time.perf_counter` od startu wątków do ich zakończenia.

Kalibracja: `time.sleep(0.001)` trwa średnio **2,17 ms** w tym przebiegu (Windows ma gorszą rozdzielczość), więc opóźnienie procesora w teście to realnie ok. 2,2 ms, a nie 1 ms.

### 3.1. `wplac` — 10 000 operacji (operacja w pamięci)

| Wątki | Czas (mediana) | Przepustowość | Przyspieszenie |
|:---:|---:|---:|:---:|
| 1 (sekwencyjnie) | 0,0266 s | 376 510 ops/s | 1,00× |
| 4 | 0,0224 s | 446 122 ops/s | 1,19× |
| 8 | 0,0169 s | 592 428 ops/s | 1,57× |

Saldo po każdym przebiegu: 10 000 (zgodne z oczekiwaniem).

### 3.2. `przelew_zewnetrzny` — 1 000 operacji, opóźnienie procesora 1 ms

| Wątki | Czas (mediana) | Przepustowość | Przyspieszenie |
|:---:|---:|---:|:---:|
| 1 (sekwencyjnie) | 1,818 s | 550 ops/s | 1,00× |
| 4 | 0,490 s | 2 039 ops/s | 3,71× |
| 8 | 0,254 s | 3 945 ops/s | 7,17× |

Saldo po każdym przebiegu: zgodne z oczekiwaniem (przelewy bez awarii, brak błędów).

**Interpretacja:** dla operacji w pamięci nie ma stabilnego przyspieszenia. CPython z GIL wykonuje kod Pythona naraz tylko w jednym wątku. Wyniki `wplac` zmieniają się między przebiegami (w poprzednim pomiarze 0,96–0,98×, w obecnym 1,19× i 1,57×), więc różnice traktujemy jako szum pomiarowy. Dla operacji z oczekiwaniem (symulowane I/O przez `sleep`, który zwalnia GIL) przepustowość rośnie prawie liniowo: 3,71× dla 4 wątków (ok. 93% wydajności) i 7,17× dla 8 wątków (ok. 90%). Wynik dla rzeczywistego I/O może się różnić.

---

## 4. Niespójności wykryte przez testy współbieżności

### 4.1. S2 i S3 — wypłaty przekraczają saldo i limit dzienny (`wyplac`)

**Obserwacja:** przy wariancie agresywnym saldo spada poniżej zera (np. −130 przy poprawnym 0; 113 wypłat zamiast 100). W S3 suma dzisiejszych wypłat przekracza 5000 (np. 5200 przy 52 wypłatach zamiast 50).

**Przyczyna:** `wyplac` sprawdza saldo (`kwota > konto.saldo`) i limit dzienny (`_suma_dzisiejszych_wyplat(konto) + kwota > LIMIT`), a dopiero potem odejmuje kwotę (`konto.saldo -= kwota`). Metoda nie używa `self._lock`. Dwa wątki mogą przejść sprawdzenie na tym samym stanie konta, zanim którykolwiek odejmie kwotę.

**Warunki wystąpienia:**
- co najmniej kilka wątków wypłaca z tego samego konta w tym samym czasie,
- okno między sprawdzeniem a odjęciem jest wystarczająco długie: w wariancie agresywnym naruszenie występuje w większości uruchomień (S2: 100/100 uruchomień niezaliczonych; S3: 88/100), w domyślnym nie występuje w tej serii (S2: 0/100 niezaliczonych; S3: 0/100). W poprzedniej serii pomiarów S3 w wariancie domyślnym miała 1/100 naruszeń (suma 5100 przy 51 wypłatach), więc przy domyślnym interwale naruszenie jest możliwe, ale rzadkie.

### 4.2. S4 — przelew zewnętrzny powoduje ujemne saldo (`przelew_zewnetrzny`)

**Obserwacja:** przy 20 wątkach i saldzie 1000 wykonano 119 przelewów (zamiast 100), saldo wyszło −190. W wariancie domyślnym **0/100 uruchomień zaliczonych**; w zapisanych przykładach wynik był identyczny (−190 / 119). W wariancie agresywnym saldo wychodziło od −80 do −150 (przykłady z zapisu).

**Przyczyna:** metoda sprawdza saldo, następnie wywołuje procesor (`wyslij_przelew`, który śpi 1 ms), a dopiero potem odejmuje kwotę. W tym oknie wszystkie wątki widzą to samo saldo 1000 i każdy przechodzi kontrolę.

**Warunki wystąpienia:** wystarczy równoległość większa niż `saldo / kwota` w czasie jednego wywołania procesora. Nie zależy od interwału przełączania wątków — czas oczekiwania w procesorze jest wystarczający. To najsilniejszy wynik z całej serii.

**Dodatkowa obserwacja (jedno uruchomienie pytest):** `ZewnetrznyProcesor.licznik_wywolan += 1` nie jest chroniony. W domyślnym uruchomieniu 119 udanych przelewów miało tylko **100 unikalnych** numerów referencyjnych (19 duplikatów). W agresywnym: 111 przelewów, 35 unikalnych numerów. Oznacza to, że zewnętrzny system rozliczeniowy dostałby identyfikatory, które się powtarzają.

---

## 5. Wnioski

**Czy testy niefunkcjonalne ujawniły coś, czego nie wykryły testy funkcjonalne z zajęć nr 4?**

**Tak.** Testy funkcjonalne z lab 4 (`tests/test_lab4.py`) i z zajęć 2–3 (`tests/test_operacje.py`) — łącznie 51 testów — przechodzą w całości (sprawdzone przed startem prac, `51 passed`). Wszystkie wywołują metody jednowątkowo, pojedynczo, na świeżym stanie. Nie mogą więc zobaczyć:

1. **Wypłat ponad saldo i ponad limit dzienny** przy równoległym dostępie (S2, S3). Testy brzegowe dla limitu 5000 sprawdzają poprawnie jedno wywołanie; nie sprawdzają, że suma z wielu wywołań równoległych pozostaje w limicie.
2. **Ujemnego salda w przelewie zewnętrznym** (S4). Tablica decyzyjna z lab 4 (reguła R4/R6) zakłada, że sprawdzenie salda i odjęcie kwoty dzieje się atomowo — w jednowątkowym teście ten warunek zawsze jest spełniony.
3. **Duplikatów numerów referencyjnych** procesora (obserwacja z S4). Test `test_r6_sukces` sprawdza tylko status i saldo.



