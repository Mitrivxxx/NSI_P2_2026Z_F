import random
from datetime import date

from bank import BankSystem
from procesor import ZewnetrznyProcesor


def _wykonaj_wywolanie(nr, opis, fn):
    print(f"\n=== {nr}. {opis} ===")
    try:
        wynik = fn()
        print("WYNIK:", wynik)
    except Exception as e:
        print("WYJATEK:", type(e).__name__, "-", e)


def logger_bledow():
    bank = BankSystem()
    bank.utworz_konto("1234567895", "Jan Kowalski", 1000)
    bank.utworz_konto("9876543215", "Anna Nowak", 100)
    bank.utworz_konto("1111111119", "Piotr Wisniewski", 50)
    bank.wplac("1234567895", 1)
    bank.zablokuj_konto("1111111119")
    proc_awaria = ZewnetrznyProcesor(prawdopodobienstwo_awarii=1.0, generator=random.Random(1))

    przypadki = [
        (1, "utworz_konto — numer za krotki", lambda: bank.utworz_konto("123", "X")),
        (2, "utworz_konto — 11 cyfr", lambda: bank.utworz_konto("12345678901", "X")),
        (3, "utworz_konto — zla cyfra kontrolna", lambda: bank.utworz_konto("1234567890", "X")),
        (4, "utworz_konto — znaki inne niz cyfry", lambda: bank.utworz_konto("abcdefghij", "X")),
        (5, "wplac — konto nie istnieje", lambda: bank.wplac("0000000000", 100)),
        (6, "wplac — kwota 0", lambda: bank.wplac("1234567895", 0)),
        (7, "wplac — kwota ujemna", lambda: bank.wplac("1234567895", -10)),
        (8, "wplac — kwota nie jest liczba", lambda: bank.wplac("1234567895", "abc")),
        (9, "wyplac — konto nie istnieje", lambda: bank.wyplac("9999999999", 10)),
        (10, "wyplac — kwota 0", lambda: bank.wyplac("1234567895", 0)),
        (11, "wyplac — kwota wieksza niz saldo", lambda: bank.wyplac("1234567895", 999999)),
        (12, "wyplac — konto zablokowane", lambda: bank.wyplac("1111111119", 10)),
        (13, "przelew — konto zrodlowe nie istnieje", lambda: bank.przelew("0000000000", "9876543215", 10)),
        (14, "przelew — konto docelowe nie istnieje", lambda: bank.przelew("1234567895", "2222222222", 10)),
        (15, "przelew — kwota ujemna", lambda: bank.przelew("1234567895", "9876543215", -5)),
        (16, "przelew — powyzej limitu 1 mln", lambda: bank.przelew("1234567895", "9876543215", 1_000_001)),
        (17, "przelew_zewnetrzny — konto nie istnieje", lambda: bank.przelew_zewnetrzny("0000000000", "EXT0000001", 10, procesor=proc_awaria)),
        (18, "przelew_zewnetrzny — kwota 0", lambda: bank.przelew_zewnetrzny("9876543215", "EXT0000001", 0, procesor=proc_awaria)),
        (19, "przelew_zewnetrzny — procesor niedostepny", lambda: bank.przelew_zewnetrzny("9876543215", "EXT0000001", 10, procesor=proc_awaria)),
        (20, "zablokuj_konto — konto nie istnieje", lambda: bank.zablokuj_konto("0000000000")),
        (21, "zablokuj_konto — numer None", lambda: bank.zablokuj_konto(None)),
        (22, "odblokuj_konto — konto nie istnieje", lambda: bank.odblokuj_konto("5555555555")),
        (23, "odblokuj_konto — numer jako liczba", lambda: bank.odblokuj_konto(1234567895)),
        (24, "nalicz_odsetki — konto nie istnieje", lambda: bank.nalicz_odsetki("0000000000", 5, 1)),
        (25, "nalicz_odsetki — stopa nie jest liczba", lambda: bank.nalicz_odsetki("9876543215", "sto", 1)),
        (26, "nalicz_odsetki — miesiace jako tekst", lambda: bank.nalicz_odsetki("9876543215", 5, "dwa")),
        (27, "historia_w_okresie — konto nie istnieje", lambda: bank.historia_w_okresie("0000000000", date(2026, 1, 1), date(2026, 12, 31))),
        (28, "historia_w_okresie — daty jako tekst", lambda: bank.historia_w_okresie("1234567895", "2026-01-01", "2026-12-31")),
        (29, "wyciag_miesieczny — konto nie istnieje", lambda: bank.wyciag_miesieczny("0000000000", 2026, 10)),
        (30, "wyciag_miesieczny — numer konta jako liczba", lambda: bank.wyciag_miesieczny(1234567895, 2026, 10)),
    ]

    for nr, opis, fn in przypadki[:15]:
        _wykonaj_wywolanie(nr, opis, fn)

    bank.wplac("1234567895", 2_000_000)

    for nr, opis, fn in przypadki[15:]:
        _wykonaj_wywolanie(nr, opis, fn)

    print("\n--- koniec 30 testow logger_bledow ---")
