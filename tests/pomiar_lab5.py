"""
Pomiar czasu wykonania i przepustowosci operacji BankSystem (Lab 5).

Uzycie:
    python tests/pomiar_lab5.py

Porownuje wariant sekwencyjny (1 watek) z rownoleglym (4 i 8 watkow)
dla dwoch typow operacji:
- wplac           - operacja w pamieci (ograniczona przez GIL),
- przelew_zewnetrzny z opoznieniem procesora 1 ms (operacja z oczekiwaniem I/O).

Kazda konfiguracja jest powtarzana REPETYCJE razy; w raporcie podajemy mediane.
Wyniki zapisywane sa do tests/wyniki_lab5_pomiar.json.
"""

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lab5_scenariusze import (  # noqa: E402
    JAN,
    EXT,
    tymczasowy_log,
    uruchom_watki,
)
from bank import BankSystem  # noqa: E402
from bank.procesor import ZewnetrznyProcesor  # noqa: E402

WYJSCIE = Path(__file__).resolve().parent / "wyniki_lab5_pomiar.json"

OPERACJE_PAMIEC = 10_000
OPERACJE_IO = 1_000
OPOZNIENIE_S = 0.001
WATKI = [1, 4, 8]
REPETYCJE = 3


def kalibracja_sleep(n=200):
    """Rzeczywisty czas time.sleep(1 ms) w tym systemie (Windows ma gorsza rozdzielczosc)."""
    start = time.perf_counter()
    for _ in range(n):
        time.sleep(OPOZNIENIE_S)
    return (time.perf_counter() - start) / n


def pomiar_wplac(liczba_watkow):
    with tymczasowy_log():
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 0)
        na_watek = OPERACJE_PAMIEC // liczba_watkow

        def cel(_):
            for _ in range(na_watek):
                bank.wplac(JAN, 1)

        _, bledy, czas = uruchom_watki(liczba_watkow, cel)
        wykonane = na_watek * liczba_watkow
        saldo = bank.konta[JAN].saldo
        return {
            "operacje": wykonane,
            "czas_s": czas,
            "przepustowosc_ops_s": wykonane / czas,
            "saldo_oczekiwane": wykonane,
            "saldo_otrzymane": int(saldo),
            "bledy": len(bledy),
        }


def pomiar_przelew_zewnetrzny(liczba_watkow):
    with tymczasowy_log():
        bank = BankSystem()
        bank.utworz_konto(JAN, "Jan", 10**9)
        procesor = ZewnetrznyProcesor(prawdopodobienstwo_awarii=0.0, opoznienie_s=OPOZNIENIE_S)
        na_watek = OPERACJE_IO // liczba_watkow

        def cel(_):
            for _ in range(na_watek):
                bank.przelew_zewnetrzny(JAN, EXT, 1, procesor=procesor)

        _, bledy, czas = uruchom_watki(liczba_watkow, cel)
        wykonane = na_watek * liczba_watkow
        saldo = bank.konta[JAN].saldo
        return {
            "operacje": wykonane,
            "czas_s": czas,
            "przepustowosc_ops_s": wykonane / czas,
            "saldo_oczekiwane": 10**9 - wykonane,
            "saldo_otrzymane": int(saldo),
            "bledy": len(bledy),
        }


def zmierz(nazwa, funkcja):
    wyniki = {}
    for watki in WATKI:
        proby = [funkcja(watki) for _ in range(REPETYCJE)]
        mediana_czas = statistics.median(p["czas_s"] for p in proby)
        mediana_przep = statistics.median(p["przepustowosc_ops_s"] for p in proby)
        wyniki[watki] = {
            "operacje": proby[0]["operacje"],
            "mediana_czas_s": round(mediana_czas, 4),
            "min_czas_s": round(min(p["czas_s"] for p in proby), 4),
            "max_czas_s": round(max(p["czas_s"] for p in proby), 4),
            "mediana_przepustowosc_ops_s": round(mediana_przep, 1),
            "saldo_oczekiwane": proby[0]["saldo_oczekiwane"],
            "saldo_otrzymane_kolejne_proby": [p["saldo_otrzymane"] for p in proby],
            "bledy": sum(p["bledy"] for p in proby),
        }
        print(
            f"{nazwa:<22} watki={watki:<2} operacje={proby[0]['operacje']:<6} "
            f"mediana_czas={mediana_czas:.4f}s "
            f"przepustowosc={mediana_przep:,.0f} ops/s "
            f"saldo={[p['saldo_otrzymane'] for p in proby]} "
            f"(oczek.={proby[0]['saldo_oczekiwane']})"
        )
    return wyniki


def main():
    sleep_real = kalibracja_sleep()
    print(f"Kalibracja: time.sleep(0.001) trwa srednio {sleep_real * 1000:.3f} ms\n")
    dane = {
        "kalibracja_sleep_s": round(sleep_real, 6),
        "wplac": zmierz("wplac (pamiec)", pomiar_wplac),
        "przelew_zewnetrzny": zmierz("przelew_zewn. (IO)", pomiar_przelew_zewnetrzny),
    }
    WYJSCIE.write_text(json.dumps(dane, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nZapisano: {WYJSCIE}")


if __name__ == "__main__":
    main()
