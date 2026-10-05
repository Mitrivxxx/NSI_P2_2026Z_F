from datetime import date
from decimal import Decimal


class Konto:
    def __init__(self, numer, wlasciciel, saldo_poczatkowe=0):
        self.numer = numer
        self.wlasciciel = wlasciciel
        self.saldo = Decimal(str(saldo_poczatkowe))
        self.historia = []
        self.status = "aktywne"

    def dodaj_wpis(self, typ, kwota, data_operacji=None):
        if data_operacji is None:
            data_operacji = date.today()
        self.historia.append((data_operacji, typ, kwota))
