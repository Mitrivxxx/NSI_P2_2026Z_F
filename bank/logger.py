import functools
import json
import time
from pathlib import Path

SCIEZKA_LOGU = Path(__file__).resolve().parent.parent / "logs" / "awarie.jsonl"


def niezawodnosc_logger(log_path=None):
    """
    Dekorator: przy wyjatku zapisuje wpis awarii do pliku JSONL i ponownie
    rzuca ten sam wyjatek (nie zmieniamy zachowania funkcji).
    """
    def dekorator(funkcja):
        @functools.wraps(funkcja)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return funkcja(*args, **kwargs)
            except Exception as e:
                # args[0] przy metodzie to self (BankSystem) — w logu zostaje repr
                wpis = {
                    "timestamp": time.time(),
                    "funkcja": funkcja.__name__,
                    "args": repr(args),
                    "kwargs": repr(kwargs),
                    "typ_bledu": type(e).__name__,
                    "komunikat": str(e),
                    "czas_do_awarii_s": time.time() - start,
                }
                sciezka = Path(log_path) if log_path is not None else SCIEZKA_LOGU
                sciezka.parent.mkdir(parents=True, exist_ok=True)
                with open(sciezka, "a", encoding="utf-8") as f:
                    f.write(json.dumps(wpis, ensure_ascii=False) + "\n")
                raise
        return wrapper
    return dekorator
