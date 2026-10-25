from datetime import date, timedelta
from decimal import Decimal

import pytest

from bank import LIMIT_DZIENNY_WYPLAT, BankSystem
from bank.wyjatki import KontoNieIstnieje, KontoZablokowane

JAN = "1234567895"
ANNA = "9876543215"
BRAK = "0000000000"


@pytest.fixture
def bank():
    system = BankSystem()
    system.utworz_konto(JAN, "Jan", 1000)
    system.utworz_konto(ANNA, "Anna", 500)
    return system

class TestWplac:
    def test_dodaje_kwote_do_salda_i_historii(self, bank):
        saldo = bank.wplac(JAN, Decimal("250.50"))

        konto = bank._pobierz_konto(JAN)
        assert saldo == Decimal("1250.50")
        assert konto.saldo == Decimal("1250.50")
        assert konto.historia[-1] == (date.today(), "wplata", Decimal("250.50"))

    def test_konto_nie_istnieje(self, bank):
        with pytest.raises(KontoNieIstnieje, match="nie istnieje"):
            bank.wplac(BRAK, 10)

    def test_kwota_zero(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.wplac(JAN, 0)
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_kwota_ujemna(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.wplac(JAN, -1)

    def test_kwota_jeden(self, bank):
        assert bank.wplac(JAN, 1) == Decimal("1001")


class TestWyplac:
    def test_pomniejsza_saldo_i_zapisuje_historie(self, bank):
        saldo = bank.wyplac(JAN, 200)

        konto = bank._pobierz_konto(JAN)
        assert saldo == Decimal("800")
        assert konto.historia[-1] == (date.today(), "wyplata", Decimal("200"))

    def test_wyplata_rowna_saldu(self, bank):
        assert bank.wyplac(JAN, 1000) == Decimal("0")

    def test_konto_nie_istnieje(self, bank):
        with pytest.raises(KontoNieIstnieje, match="nie istnieje"):
            bank.wyplac(BRAK, 10)

    def test_konto_zablokowane(self, bank):
        bank.zablokuj_konto(JAN)
        with pytest.raises(KontoZablokowane, match="zablokowane"):
            bank.wyplac(JAN, 10)
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_kwota_zero(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.wyplac(JAN, 0)

    def test_kwota_ujemna(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.wyplac(JAN, -5)

    def test_niewystarczajace_srodki(self, bank):
        with pytest.raises(ValueError, match="Niewystarczajace srodki"):
            bank.wyplac(JAN, Decimal("1000.01"))

    def test_limit_dzienny_rowny_limitowi_przechodzi(self, bank):
        bank.wplac(JAN, 5000)
        assert bank.wyplac(JAN, LIMIT_DZIENNY_WYPLAT) == Decimal("1000")

    def test_przekroczony_limit_dzienny(self, bank):
        bank.wplac(JAN, 6000)
        bank.wyplac(JAN, 4000)
        with pytest.raises(ValueError, match="dzienny limit"):
            bank.wyplac(JAN, 1001)
        assert bank._pobierz_konto(JAN).saldo == Decimal("3000")

    def test_wplata_i_stara_wyplata_nie_wchodza_do_limitu(self, bank):
        bank.wplac(JAN, 1000)
        konto = bank._pobierz_konto(JAN)
        konto.historia.append((date.today() - timedelta(days=1), "wyplata", Decimal("5000")))
        assert bank.wyplac(JAN, 1500) == Decimal("500")

    def test_kwota_jeden(self, bank):
        assert bank.wyplac(JAN, 1) == Decimal("999")


class TestPrzelew:
    def test_przenosi_srodki_i_zapisuje_obie_strony(self, bank):
        saldo_z = bank.przelew(JAN, ANNA, Decimal("100.25"))

        zrodlo = bank._pobierz_konto(JAN)
        cel = bank._pobierz_konto(ANNA)
        assert saldo_z == Decimal("899.75")
        assert cel.saldo == Decimal("600.25")
        assert zrodlo.historia[-1] == (date.today(), "przelew_wychodzacy", Decimal("100.25"))
        assert cel.historia[-1] == (date.today(), "przelew_przychodzacy", Decimal("100.25"))

    def test_konto_zrodlowe_nie_istnieje(self, bank):
        with pytest.raises(KontoNieIstnieje, match="nie istnieje"):
            bank.przelew(BRAK, ANNA, 10)
        assert bank._pobierz_konto(ANNA).saldo == Decimal("500")

    def test_konto_docelowe_nie_istnieje(self, bank):
        with pytest.raises(KontoNieIstnieje, match="nie istnieje"):
            bank.przelew(JAN, BRAK, 10)
        assert bank._pobierz_konto(JAN).saldo == Decimal("1000")

    def test_konto_zrodlowe_zablokowane(self, bank):
        bank.zablokuj_konto(JAN)
        with pytest.raises(KontoZablokowane, match=r"Konto \{numer_z\} jest zablokowane"):
            bank.przelew(JAN, ANNA, 10)
        assert bank._pobierz_konto(ANNA).saldo == Decimal("500")

    def test_kwota_zero(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.przelew(JAN, ANNA, 0)

    def test_kwota_ujemna(self, bank):
        with pytest.raises(ValueError, match="dodatnia"):
            bank.przelew(JAN, ANNA, -1)

    def test_niewystarczajace_srodki(self, bank):
        with pytest.raises(ValueError, match="zrodlowym"):
            bank.przelew(JAN, ANNA, 1001)

    def test_kwota_rowna_limitowi_systemowemu(self, bank):
        bank.wplac(JAN, 1_000_000)
        assert bank.przelew(JAN, ANNA, 1_000_000) == Decimal("1000")
        assert bank._pobierz_konto(ANNA).saldo == Decimal("1000500")

    def test_przekroczony_limit_systemowy(self, bank):
        bank.wplac(JAN, 2_000_000)
        with pytest.raises(ValueError, match="limit systemowy"):
            bank.przelew(JAN, ANNA, 1_000_001)
        assert bank._pobierz_konto(JAN).saldo == Decimal("2001000")
        assert bank._pobierz_konto(ANNA).saldo == Decimal("500")

    def test_przelew_wychodzacy_wchodzi_do_limitu_wyplat(self, bank):
        bank.wplac(JAN, 10_000)
        bank.przelew(JAN, ANNA, 4500)
        with pytest.raises(ValueError, match="dzienny limit"):
            bank.wyplac(JAN, 501)

    def test_kwota_jeden(self, bank):
        assert bank.przelew(JAN, ANNA, 1) == Decimal("999")
        assert bank._pobierz_konto(ANNA).saldo == Decimal("501")

    def test_przelew_rowny_saldu(self, bank):
        assert bank.przelew(JAN, ANNA, 1000) == Decimal("0")
        assert bank._pobierz_konto(ANNA).saldo == Decimal("1500")


class TestUtworzKonto:
    def test_zwraca_konto(self, bank):
        numer = "1111111119"
        konto = bank.utworz_konto(numer, "Ewa", 50)
        assert konto is not None
        assert konto.numer == numer
        assert konto.saldo == Decimal("50")

    def test_zly_numer_za_krotki(self):
        system = BankSystem()
        with pytest.raises(ValueError, match="Nieprawidlowy"):
            system.utworz_konto("123", "X", 0)

    def test_zly_numer_nie_cyfry(self):
        system = BankSystem()
        with pytest.raises(ValueError, match="Nieprawidlowy"):
            system.utworz_konto("123456789a", "X", 0)


class TestNaliczOdsetki:
    def test_nalicza_i_zwraca_saldo(self, bank):
        # 12% rocznie, 1 miesiąc → +1% od 1000 = 1010.00
        saldo = bank.nalicz_odsetki(JAN, 12, 1)
        assert saldo == Decimal("1010.00")
        assert bank._pobierz_konto(JAN).saldo == Decimal("1010.00")


class TestHistoria:
    def test_poza_zakresem_pusta(self, bank):
        bank.wplac(JAN, 10)
        wczoraj = date.today() - timedelta(days=1)
        assert bank.historia_w_okresie(JAN, wczoraj, wczoraj) == []
