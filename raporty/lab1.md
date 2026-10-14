SUT: System zarządzania kontem bankowym (Zespół F) — konta, wpłaty, wypłaty, przelewy, odsetki, wyciągi.

Repozytorium: https://github.com/Mitrivxxx/NSI_P2_2026Z_F

Awarie znalezione dziś (z awarie.jsonl):

1. ValueError, dotkliwość niska.
   utworz_konto odrzuca zły numer, a wplac, wyplac i przelew odrzucają kwotę równą zero lub ujemną. wyplac kończy się też przy braku środków, a przelew przy kwocie powyżej 1 mln. To działanie zgodne z regułami, nie utrata danych.

2. KontoNieIstnieje, dotkliwość niska.
   wplac, wyplac, przelew, przelew_zewnetrzny, zablokuj_konto, odblokuj_konto, nalicz_odsetki, historia_w_okresie i wyciag_miesieczny przerywają się, gdy numeru nie ma w systemie.

3. KontoZablokowane, dotkliwość niska.
   wyplac na koncie o statusie „zablokowane” jest zatrzymywana, zanim zejdą środki.

4. InvalidOperation, dotkliwość średnia.
   wplac z kwotą „abc” oraz nalicz_odsetki ze stopą „sto” kończą się wewnętrznym błędem Decimal, zamiast kontrolowanym ValueError.

5. TypeError, dotkliwość średnia.
   nalicz_odsetki z liczbą miesięcy podaną jako tekst oraz historia_w_okresie z datami jako tekst nie są obsługiwane jako błąd danych. Wyjątek wychodzi z Pythona, nie z walidacji systemu.

6. ProcesorNiedostepny, dotkliwość wysoka.
   przelew_zewnetrzny przerywa się, gdy zewnętrzny procesor płatności nie odpowiada. Jest jedna próba, bez ponowienia, więc przelew w tym wywołaniu nie dochodzi do skutku.

Wskaźniki:

Liczba wywołań = 30
(tyle przypadków w logger_bledow).

Liczba awarii = 30
(każde z tych wywołań zapisało wyjątek w awarie.jsonl).

MTTF = czas od startu testów do ostatniej awarii / liczba awarii
MTTF = 0,00610 s / 30 = 0,000203 s ≈ 0,00020 s

Gęstość = liczba awarii / KLOC
KLOC = 199 linii kodu SUT / 1000 = 0,199
Gęstość = 30 / 0,199 = 150,8 ≈ 151 usterek/KLOC

Wniosek: najbardziej ryzykowne są przelewy zewnętrzne — jedna próba przez procesor, który pada losowo, bez ponowienia.
