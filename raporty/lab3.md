# Lab 3 — testy mutacyjne

Testowaliśmy `bank/system.py` zestawem `tests/test_operacje.py` (pytest-gremlins).

```bash
pytest --gremlins --gremlin-targets=bank/system.py --gremlin-report=console,html tests/test_operacje.py
```

## 1. Mutation score przed i po

| | zabite | przeżyły | score |
|---|---:|---:|---:|
| przed (start labu) | 35/65 | 30 | **53,85%** |
| po (po dopisaniu testów) | 48/65 | 17 | **73,85%** |

Wzrost o ok. 20 punktów procentowych. Szczegóły: `coverage/gremlins/index.html`.

## 2. Przetrwali mutanci (analiza 5)

| # | gdzie | co zmieniono | klasa | uzasadnienie |
|---|---|---|---|---|
| 1 | `wplac` | warunek „kwota ≤ 0” → „≤ 1” | brakujący test | Mutant odrzuca poprawną wpłatę 1 zł. Testy sprawdzały 0, wartości ujemne i większe kwoty — nie samą jedynkę. |
| 2 | `wyplac` | to samo | brakujący test | Brak udanej wypłaty równej 1. |
| 3 | `przelew` | to samo | brakujący test | Brak udanego przelewu na kwotę 1. |
| 4 | `przelew` | „kwota > saldo” → „≥ saldo” | brakujący test | Przelew całego salda jest dozwolony. Dla wypłaty taki przypadek był, dla przelewu — nie. |
| 5 | sprawdzanie numeru konta | zamiast `False` zwracane `None` | **equivalent** | Kod pyta tylko „czy numer OK?”. W Pythonie `None` i `False` obie oznaczają „nie” — zachowanie systemu bez zmian. |

Equivalent łącznie: **1** (poz. 5). Pozostałe 4 to luki w testach (brak przypadków brzegowych).

## 3. Dopisane testy i zabijane mutanty

| dopisany test | co sprawdza | jakiego mutanta zabija |
|---|---|---|
| wpłata kwoty 1 | udana wpłata 1 zł | zaostrzony warunek kwoty w `wplac` |
| wypłata kwoty 1 | udana wypłata 1 zł | to samo w `wyplac` |
| przelew kwoty 1 | udany przelew 1 zł | to samo w `przelew` |
| przelew równy saldu | przelew całego salda | zamiana `>` na `≥` przy saldzie |
| `utworz_konto` zwraca konto | wynik nie jest pusty | usunięcie wartości zwracanej |
| zły numer konta | za krótki / litery → błąd | poluzowana walidacja numeru |
| naliczanie odsetek | dokładne nowe saldo | zamiany `*`/`/` oraz pusty wynik |
| historia poza zakresem | pusta lista dla wczoraj | błędne porównania dat |

Equivalent (poz. 5) **nie zabijamy** — żaden sensowny test nie odróżni go od oryginału.

## 4. Wnioski (mutacje vs pokrycie)

W Lab 2 pokrycie `wplac` / `wyplac` / `przelew` było **100%** linii i gałęzi, a mutation score i tak startował od **~54%**.

Pokrycie mówi tylko: „ten fragment kodu się wykonał”. Mutacje pytają: „czy test zauważy, gdy ktoś zmieni logikę?”. Wyszło to, czego coverage nie pokazuje:

- brak testu na kwotę 1 (gałąź „zła kwota” była już pokryta przez 0 i −1);
- brak przelewu równego saldu (przy wypłacie taki test był);
- słabe sprawdzenie wyników (`return`) i metod obok operacji (tworzenie konta, odsetki).

Equivalent też nie widać w pokryciu — obie metryki go „przepuszczają”. Wniosek: wysokie pokrycie ≠ mocne testy; mutacje uzupełniają lukę jakościową.
