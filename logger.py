import functools
import json
import time


def niezawodnosc_logger(log_path="awarie.jsonl"):
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
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(wpis, ensure_ascii=False) + "\n")
                raise
        return wrapper
    return dekorator
