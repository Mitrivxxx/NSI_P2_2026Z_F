"""
System zarzadzania kontem bankowym
Wariant: Zespol F

Reczne testowanie: python3 main.py
Numer = 10 cyfr, ostatnia = (suma pierwszych 9) % 10
  123456789 -> suma 45 -> cyfra 5 -> "1234567895"
"""

from pathlib import Path

from bank import BankSystem
from testy import logger_bledow


if __name__ == "__main__":
    bank = BankSystem()

    konto = bank.utworz_konto("1234567895", "Jan Kowalski", 1000)
    print("start:", konto.saldo)

    bank.wplac("1234567895", 500)
    print("po wplacie:", konto.saldo)

    bank.wyplac("1234567895", 200)
    print("po wyplacie:", konto.saldo)

    try:
        bank.utworz_konto("123", "X")
    except ValueError as e:
        print("OK (oczekiwane): zlapany", type(e).__name__, "-", e)
        print("log awarii:", Path("awarie.jsonl").resolve())

    print("\n" + "=" * 50)
    print("30 testow logger_bledow")
    print("=" * 50)
    logger_bledow()
