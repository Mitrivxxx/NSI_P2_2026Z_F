# Lab 2 — testy strukturalne

Zakres: `wplac`, `wyplac`, `przelew`.

## Metody i przypadki

Po uzupełnieniu:

- `wplac` — 4
- `wyplac` — 10
- `przelew` — 10

Razem 24. Pierwszy pomiar szedł na 17 przypadkach (`wplac` 2, `wyplac` 8, `przelew` 7).

## Pokrycie (instrukcje, gałęzie)

Instrukcje to wykonywalne linie ciała metody. Nie wchodzą w to `def`, dekorator ani puste linie. Każda taka linia, w tym `if`, `raise`, `with` i `return`, liczy się jako jedna.

Gałęzie to wyjścia z `if`. Jeden `if` daje dwie: warunek prawdziwy i fałszywy. Linia `with` jest instrukcją, ale gałęzi nie dodaje.

W kodzie jest 37 instrukcji (7 + 13 + 17) i 18 gałęzi (2 + 8 + 8).

Przed uzupełnieniem (`pytest tests/test_operacje.py --cov=bank.system --cov-branch`, 17 testów):

- `wplac`: instrukcje 6/7, gałęzie 1/2. Brak linii 62 (`raise` przy `kwota <= 0`).
- `wyplac`: instrukcje 11/13, gałęzie 6/8. Brak linii 71 (konto zablokowane) i 78 (przekroczony limit dzienny).
- `przelew`: instrukcje 15/17, gałęzie 6/8. Brak linii 89 (zablokowane konto źródłowe) i 96 (kwota powyżej 1 mln).

Razem 32/37 instrukcji i 13/18 gałęzi.

Dopisane przypadki: wpłata równa zero i ujemna, wypłata z konta zablokowanego, przekroczenie limitu dziennego wypłat, przelew ze zablokowanego konta źródłowego, przelew powyżej limitu 1 mln oraz przelew wychodzący wliczany do limitu wypłat.

Po uzupełnieniu (24 testy, to samo polecenie):

- `wplac`: 7/7, gałęzie 2/2
- `wyplac`: 13/13, gałęzie 8/8
- `przelew`: 17/17, gałęzie 8/8

Razem 37/37 instrukcji i 18/18 gałęzi.

## Świadomie pominięte

W tych trzech metodach nie ma niepokrytych linii ani gałęzi. Poza zakresem zostały pozostałe metody systemu (tworzenie kont, odsetki, wyciągi, przelew zewnętrzny).

## Wniosek

Tak. Przy zablokowanym koncie źródłowym `przelew` zgłasza `Konto {numer_z} jest zablokowane` — podwójne nawiasy w f-stringu, więc numer konta nie wchodzi do komunikatu. W `wyplac` ten sam przypadek wstawia numer.
