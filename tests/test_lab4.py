from decimal import Decimal

import pytest

from bank import BankSystem
from bank.procesor import ZewnetrznyProcesor
from bank.wyjatki import KontoNieIstnieje, KontoZablokowane, ProcesorNiedostepny

JAN = "1234567895"
ANNA = "9876543215"
EWA = "1111111119"
BRAK = "0000000000"
EXT = "EXT0000001"


@pytest.fixture
def bank():
    system = BankSystem()
    system.utworz_konto(JAN, "Jan", 1000)
    system.utworz_konto(ANNA, "Anna", 500)
    return system


def procesor_ok():
    return ZewnetrznyProcesor(prawdopodobienstwo_awarii=0.0)


def procesor_awaria():
    return ZewnetrznyProcesor(prawdopodobienstwo_awarii=1.0)


class TestUtworzKontoBVA:
    """Klasy równoważności i wartości brzegowe: utworz_konto."""

    def test_bva_numer_9_znakow(self):
        system = BankSystem()
        with pytest.raises(ValueError, match="Nieprawidlowy"):
            system.utworz_konto("123456789", "X", 0)

    def test_bva_numer_10_znakow(self):
        system = BankSystem()
        konto = system.utworz_konto(EWA, "Ewa", 50)
        assert konto.numer == EWA
        assert konto.wlasciciel == "Ewa"
        assert konto.saldo == Decimal("50")
        assert konto.status == "aktywne"

    def test_bva_numer_11_znakow(self):
        system = BankSystem()
        with pytest.raises(ValueError, match="Nieprawidlowy"):
            system.utworz_konto("12345678901", "X", 0)

    def test_ec_numer_zla_cyfra_kontrolna(self):
        system = BankSystem()
        with pytest.raises(ValueError, match="Nieprawidlowy"):
            system.utworz_konto("1111111110", "X", 0)

    def test_bva_saldo_zero(self):
        system = BankSystem()
        konto = system.utworz_konto(EWA, "Ewa", 0)
        assert konto.saldo == Decimal("0")

    def test_bva_saldo_tuż_powyzej_zera(self):
        system = BankSystem()
        konto = system.utworz_konto(EWA, "Ewa", Decimal("0.01"))
        assert konto.saldo == Decimal("0.01")

    def test_bva_saldo_tuż_ponizej_zera(self):
        system = BankSystem()
        konto = system.utworz_konto(EWA, "Ewa", -1)
        assert konto.saldo == Decimal("-1")


class TestPrzelewZewnetrznyBVA:
    """Klasy równoważności i wartości brzegowe: kwota w przelew_zewnetrzny."""

    def test_bva_kwota_zero(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.przelew_zewnetrzny(JAN, EXT, 0, procesor=procesor_ok())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_bva_kwota_ujemna(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.przelew_zewnetrzny(JAN, EXT, -1, procesor=procesor_ok())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_bva_kwota_jeden(self, bank):
        wynik = bank.przelew_zewnetrzny(JAN, EXT, 1, procesor=procesor_ok())
        assert wynik["status"] == "zaksiegowano"
        assert bank._pobierz_konto(JAN).saldo == Decimal("999")

    def test_bva_kwota_rowna_saldu(self, bank):
        wynik = bank.przelew_zewnetrzny(JAN, EXT, 1000, procesor=procesor_ok())
        assert wynik["status"] == "zaksiegowano"
        assert bank._pobierz_konto(JAN).saldo == Decimal("0")

    def test_bva_kwota_powyzej_salda(self, bank):
        with pytest.raises(ValueError, match="srodki"):
            bank.przelew_zewnetrzny(JAN, EXT, Decimal("1000.01"), procesor=procesor_ok())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")


class TestPrzelewZewnetrznyTablicaDecyzyjna:
    """Pokrycie reguł R1–R6 tablicy decyzyjnej z raportu lab4."""

    def test_r1_konto_nie_istnieje(self, bank):
        with pytest.raises(KontoNieIstnieje):
            bank.przelew_zewnetrzny(BRAK, EXT, 10, procesor=procesor_ok())

    def test_r2_konto_zablokowane(self, bank):
        bank.zablokuj_konto(JAN)
        with pytest.raises(KontoZablokowane):
            bank.przelew_zewnetrzny(JAN, EXT, 10, procesor=procesor_ok())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_r3_kwota_niedodatnia(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.przelew_zewnetrzny(JAN, EXT, 0, procesor=procesor_ok())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_r4_kwota_powyzej_salda(self, bank):
        with pytest.raises(ValueError, match="srodki"):
            bank.przelew_zewnetrzny(JAN, EXT, 1001, procesor=procesor_ok())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_r5_procesor_niedostepny(self, bank):
        with pytest.raises(ProcesorNiedostepny):
            bank.przelew_zewnetrzny(JAN, EXT, 10, procesor=procesor_awaria())
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_r6_sukces(self, bank):
        wynik = bank.przelew_zewnetrzny(JAN, EXT, 10, procesor=procesor_ok())
        assert wynik["status"] == "zaksiegowano"
        assert bank._pobierz_konto(JAN).saldo == Decimal("990")
