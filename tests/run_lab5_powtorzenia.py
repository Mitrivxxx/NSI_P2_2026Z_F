"""
Wielokrotne uruchomienie scenariuszy wspolbieznosci (Lab 5).

Uzycie:
    python tests/run_lab5_powtorzenia.py [N]        (domyslnie N=100)

Dla kazdego scenariusza i kazdego interwalu przelaczania watkow wykonuje
N niezaleznych uruchomien, zlicza przejscia (ok) i zapisuje wyniki do
tests/wyniki_lab5_powtorzenia.json.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lab5_scenariusze import INTERWALY, SCENARIUSZE  # noqa: E402

WYJSCIE = Path(__file__).resolve().parent / "wyniki_lab5_powtorzenia.json"
PRZYKLADY_BLEDOW = 3


def nazwa_interwalu(interwal):
    return "domyslny (5 ms)" if interwal is None else f"agresywny ({interwal} s)"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    raport = []
    for scenariusz in SCENARIUSZE:
        for interwal in INTERWALY:
            przejscia = 0
            czasy = []
            przyklady = []
            start = time.perf_counter()
            for _ in range(n):
                wynik = scenariusz(interwal_s=interwal)
                czasy.append(wynik["czas_s"])
                if wynik["ok"]:
                    przejscia += 1
                elif len(przyklady) < PRZYKLADY_BLEDOW:
                    przyklady.append({
                        "oczekiwane": wynik["oczekiwane"],
                        "otrzymane": wynik["otrzymane"],
                    })
            calkowity = time.perf_counter() - start
            pozycja = {
                "scenariusz": wynik["scenariusz"],
                "interwal": nazwa_interwalu(interwal),
                "przejscia": przejscia,
                "N": n,
                "sredni_czas_run_s": round(sum(czasy) / n, 6),
                "calkowity_czas_s": round(calkowity, 3),
                "przyklady_bledow": przyklady,
            }
            raport.append(pozycja)
            print(
                f"{pozycja['scenariusz']:<55} {pozycja['interwal']:<24} "
                f"{przejscia}/{n}  sr.czas={pozycja['sredni_czas_run_s']}s"
            )

    WYJSCIE.write_text(json.dumps(raport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nZapisano: {WYJSCIE}")


if __name__ == "__main__":
    main()
