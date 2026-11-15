"""
Scenariusze wspolbieznosci dla BankSystem (Lab 5).

Wspolne dla tests/test_lab5.py (pytest) oraz skryptow pomiarowych
(tests/run_lab5_powtorzenia.py, tests/pomiar_lab5.py).

Kazdy scenariusz zwraca slownik z wynikiem i polem "ok" - True, gdy
niezmiennik zostal zachowany.
"""

import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bank import LIMIT_DZIENNY_WYPLAT, BankSystem  # noqa: E402
from bank import logger as bank_logger  # noqa: E402
from bank.procesor import ZewnetrznyProcesor  # noqa: E402

JAN = "1234567895"
ANNA = "9876543215"
EXT = "EXT0000001"


@contextmanager
def tymczasowy_log():
    """Przekierowuje log awarii do pliku tymczasowego (nie zasmiecamy logs/)."""
    with tempfile.TemporaryDirectory() as katalog:
        stary = bank_logger.SCIEZKA_LOGU
        bank_logger.SCIEZKA_LOGU = Path(katalog) / "awarie.jsonl"
        try:
            yield
        finally:
            bank_logger.SCIEZKA_LOGU = stary


@contextmanager
def interwal_przelaczania(sekundy):
    """
    Zmienia czestotliwosc przelaczania watkow przez interpreter CPython.
    None = wartosc domyslna (5 ms). Male wartosci wymuszaja czestsze
    przeplatanie sie watkow w srodku operacji i ujawniaja wyscigi.
    """
    if sekundy is None:
        yield
        return
    stary = sys.getswitchinterval()
    sys.setswitchinterval(sekundy)
    try:
        yield
    finally:
        sys.setswitchinterval(stary)


def uruchom_watki(liczba, cel):
    """Startuje `liczba` watkow naraz (Barrier) i zwraca (wyniki, bledy, czas_s)."""
    bariera = threading.Barrier(liczba)
    wyniki = [None] * liczba
    bledy = []

    def praca(i):
        try:
            bariera.wait()
            wyniki[i] = cel(i)
        except BaseException as e:  # noqa: BLE001 - raportujemy kazdy wyjatek
            bledy.append(repr(e))

    watki = [threading.Thread(target=praca, args=(i,)) for i in range(liczba)]
    start = time.perf_counter()
    for w in watki:
        w.start()
    for w in watki:
        w.join()
    return wyniki, bledy, time.perf_counter() - start


def _wynik(nazwa, interwal, ok, oczekiwane, otrzymane, czas_s, **szczegoly):
    return {
        "scenariusz": nazwa,
        "interwal_s": interwal,
        "ok": bool(ok),
        "oczekiwane": oczekiwane,
        "otrzymane": otrzymane,
        "czas_s": round(czas_s, 6),
        **szczegoly,
    }


def s1_wplac_wspolbieznie(interwal_s=None, watki=8, operacje=500):
    """S1: rownolegle wplaty 1 zl. Niezmiennik: saldo_koncowe = start + n*kwota."""
    with tymczasowy_log(), interwal_przelaczania(interwal_s):
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 1000)

        def cel(_):
            for _ in range(operacje):
                bank.wplac(JAN, 1)

        _, bledy, czas = uruchom_watki(watki, cel)
        konto = bank.konta[JAN]
        oczekiwane = Decimal(1000 + watki * operacje)
        wplaty = sum(1 for _, typ, _ in konto.historia if typ == "wplata")
        ok = not bledy and konto.saldo == oczekiwane and wplaty == watki * operacje
        return _wynik(
            "S1 wplac wspolbieznie", interwal_s, ok, str(oczekiwane), str(konto.saldo),
            czas, watki=watki, operacje_na_watek=operacje,
            utracone_aktualizacje=str(oczekiwane - konto.saldo),
            wpisy_historii=wplaty, bledy=bledy,
        )


def s2_wyplac_ponizej_zera(interwal_s=None, watki=20, proby=10, kwota=10):
    """
    S2: wiele watkow probuje wyplacic z konta o saldzie 1000 (po 10 zl).
    Poprawnie: dokladnie 100 wyplat, saldo = 0, nigdy ujemne.
    """
    with tymczasowy_log(), interwal_przelaczania(interwal_s):
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 1000)

        def cel(_):
            sukcesy = 0
            for _ in range(proby):
                try:
                    bank.wyplac(JAN, kwota)
                    sukcesy += 1
                except ValueError:
                    pass  # brak srodkow / limit - oczekiwane
            return sukcesy

        wyniki, bledy, czas = uruchom_watki(watki, cel)
        sukcesy = sum(w for w in wyniki if w is not None)
        konto = bank.konta[JAN]
        oczekiwane_sukcesy = 1000 // kwota
        ok = not bledy and konto.saldo == 0 and sukcesy == oczekiwane_sukcesy
        return _wynik(
            "S2 wyplac - saldo nie spada ponizej zera", interwal_s, ok,
            f"saldo=0, sukcesy={oczekiwane_sukcesy}",
            f"saldo={konto.saldo}, sukcesy={sukcesy}", czas,
            watki=watki, proby_na_watek=proby, kwota=kwota, bledy=bledy,
        )


def s3_limit_dzienny(interwal_s=None, watki=20, proby=50, kwota=100):
    """
    S3: wiele watkow wyplaca 100 zl z konta o duzym saldzie.
    Limit dzienny 5000 => dokladnie 50 wyplat. Niezmiennik: suma dzisiejszych
    wyplat <= LIMIT_DZIENNY_WYPLAT.
    """
    with tymczasowy_log(), interwal_przelaczania(interwal_s):
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 10000)

        def cel(_):
            sukcesy = 0
            for _ in range(proby):
                try:
                    bank.wyplac(JAN, kwota)
                    sukcesy += 1
                except ValueError:
                    pass  # przekroczony limit dzienny - oczekiwane
            return sukcesy

        wyniki, bledy, czas = uruchom_watki(watki, cel)
        sukcesy = sum(w for w in wyniki if w is not None)
        konto = bank.konta[JAN]
        dzis = date.today()
        suma_dzis = sum(
            kwota_w for data_w, typ, kwota_w in konto.historia
            if data_w == dzis and typ in ("wyplata", "przelew_wychodzacy")
        )
        oczekiwane_sukcesy = LIMIT_DZIENNY_WYPLAT // kwota
        ok = not bledy and suma_dzis <= LIMIT_DZIENNY_WYPLAT and sukcesy == oczekiwane_sukcesy
        return _wynik(
            "S3 limit dzienny wyplat", interwal_s, ok,
            f"suma<={LIMIT_DZIENNY_WYPLAT}, sukcesy={oczekiwane_sukcesy}",
            f"suma={suma_dzis}, sukcesy={sukcesy}", czas,
            watki=watki, proby_na_watek=proby, kwota=kwota, bledy=bledy,
        )


def s4_przelew_zewnetrzny(interwal_s=None, watki=20, proby=10, kwota=10, opoznienie_s=0.001):
    """
    S4: rownolegle przelewy zewnetrzne z saldo 1000 i opoznieniem procesora.
    Procesor nie zawodzi (p=0). Poprawnie: 100 przelewow, saldo = 0.
    """
    with tymczasowy_log(), interwal_przelaczania(interwal_s):
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 1000)
        procesor = ZewnetrznyProcesor(prawdopodobienstwo_awarii=0.0, opoznienie_s=opoznienie_s)

        def cel(_):
            sukcesy = []
            for _ in range(proby):
                try:
                    wynik = bank.przelew_zewnetrzny(JAN, EXT, kwota, procesor=procesor)
                    sukcesy.append(wynik["numer_referencyjny"])
                except ValueError:
                    pass  # brak srodkow - oczekiwane
            return sukcesy

        wyniki, bledy, czas = uruchom_watki(watki, cel)
        refy = [r for w in wyniki if w for r in w]
        konto = bank.konta[JAN]
        oczekiwane_sukcesy = 1000 // kwota
        ok = not bledy and konto.saldo == 0 and len(refy) == oczekiwane_sukcesy
        return _wynik(
            "S4 przelew_zewnetrzny - saldo nie spada ponizej zera", interwal_s, ok,
            f"saldo=0, sukcesy={oczekiwane_sukcesy}",
            f"saldo={konto.saldo}, sukcesy={len(refy)}", czas,
            watki=watki, proby_na_watek=proby, kwota=kwota,
            opoznienie_s=opoznienie_s, refy_unikalne=len(set(refy)),
            bledy=bledy,
        )


def s5_przelew_wewnetrzny_kontrola(interwal_s=None, watki=8, proby=200, kwota=1):
    """
    S5 (kontrola): rownolegle przelewy wewnetrzne miedzy dwoma kontami.
    Metoda `przelew` jest chroniona self._lock, wiec suma sald powinna
    pozostac stala.
    """
    with tymczasowy_log(), interwal_przelaczania(interwal_s):
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 1000)
        bank.utworz_konto(ANNA, "Anna", 1000)

        def cel(i):
            zrodlo, cel_konto = (JAN, ANNA) if i % 2 == 0 else (ANNA, JAN)
            for _ in range(proby):
                bank.przelew(zrodlo, cel_konto, kwota)

        _, bledy, czas = uruchom_watki(watki, cel)
        suma = bank.konta[JAN].saldo + bank.konta[ANNA].saldo
        ok = not bledy and suma == 2000
        return _wynik(
            "S5 przelew wewnetrzny (kontrola, z lockiem)", interwal_s, ok,
            "suma sald=2000", f"suma sald={suma}", czas,
            watki=watki, proby_na_watek=proby, kwota=kwota, bledy=bledy,
        )


SCENARIUSZE = [
    s1_wplac_wspolbieznie,
    s2_wyplac_ponizej_zera,
    s3_limit_dzienny,
    s4_przelew_zewnetrzny,
    s5_przelew_wewnetrzny_kontrola,
]

INTERWALY = [None, 1e-6]
