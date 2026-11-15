"""
Testy wspolbieznosci dla BankSystem (Lab 5).

Kazdy scenariusz uruchamiany jest dwa razy:
- "domyslny" - domyslne przelaczanie watkow CPython (5 ms),
- "agresywny" - interwal 1 us, wymuszajacy przeplatanie operacji.

Scenariusze S1-S4 sprawdzaja niezmienniki, ktore powinny byc zachowane
rowniez przy wspolbieznym dostepie. S5 jest kontrola (metoda z lockiem).
"""

import pytest

from lab5_scenariusze import (
    INTERWALY,
    s1_wplac_wspolbieznie,
    s2_wyplac_ponizej_zera,
    s3_limit_dzienny,
    s4_przelew_zewnetrzny,
    s5_przelew_wewnetrzny_kontrola,
)

ID_INTERWALU = {None: "domyslny", 1e-6: "agresywny"}


def _sprawdz(wynik):
    assert wynik["ok"], (
        f"Niezmiennik naruszony: oczekiwane={wynik['oczekiwane']}, "
        f"otrzymane={wynik['otrzymane']}, szczegoly={wynik}"
    )


@pytest.mark.parametrize("interwal", INTERWALY, ids=ID_INTERWALU.get)
def test_s1_wplac_wspolbieznie(interwal):
    _sprawdz(s1_wplac_wspolbieznie(interwal_s=interwal))


@pytest.mark.parametrize("interwal", INTERWALY, ids=ID_INTERWALU.get)
def test_s2_wyplac_saldo_nie_spada_ponizej_zera(interwal):
    _sprawdz(s2_wyplac_ponizej_zera(interwal_s=interwal))


@pytest.mark.parametrize("interwal", INTERWALY, ids=ID_INTERWALU.get)
def test_s3_limit_dzienny_wyplat(interwal):
    _sprawdz(s3_limit_dzienny(interwal_s=interwal))


@pytest.mark.parametrize("interwal", INTERWALY, ids=ID_INTERWALU.get)
def test_s4_przelew_zewnetrzny_saldo_nie_spada_ponizej_zera(interwal):
    _sprawdz(s4_przelew_zewnetrzny(interwal_s=interwal))


@pytest.mark.parametrize("interwal", INTERWALY, ids=ID_INTERWALU.get)
def test_s5_kontrola_przelew_z_lockiem(interwal):
    _sprawdz(s5_przelew_wewnetrzny_kontrola(interwal_s=interwal))
