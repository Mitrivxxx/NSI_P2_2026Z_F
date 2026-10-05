import random
import time

from wyjatki import ProcesorNiedostepny


class ZewnetrznyProcesor:
    """
    Symulacja zewnetrznego systemu rozliczeniowego (np. izby rozliczeniowej
    miedzybankowej), przez ktory ida przelewy wychodzace poza system.

    Zawodzi losowo z zadanym prawdopodobienstwem -- celowo, do cwiczen
    z mechanizmami odpornosci (retry, circuit breaker, redundancja) w P5.
    To NIE jest wstrzynieta usterka do znalezienia -- to jest swiadomie
    "kruchy" punkt integracji, ktory zespoly maja wzmocnic.
    """

    def __init__(self, prawdopodobienstwo_awarii=0.3, opoznienie_s=0.0, generator=None):
        self.prawdopodobienstwo_awarii = prawdopodobienstwo_awarii
        self.opoznienie_s = opoznienie_s
        self._generator = generator or random.Random()
        self.licznik_wywolan = 0

    def wyslij_przelew(self, numer_konta_docelowego, kwota):
        self.licznik_wywolan += 1
        if self.opoznienie_s:
            time.sleep(self.opoznienie_s)
        if self._generator.random() < self.prawdopodobienstwo_awarii:
            raise ProcesorNiedostepny("Zewnetrzny procesor platnosci nie odpowiada")
        return {"status": "zaksiegowano", "numer_referencyjny": f"REF{self.licznik_wywolan:06d}"}
