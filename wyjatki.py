class KontoNieIstnieje(Exception):
    """Wyjatek zglaszany, gdy operacja dotyczy nieistniejacego numeru konta."""
    pass


class ProcesorNiedostepny(Exception):
    """Wyjatek symulujacy niedostepnosc zewnetrznego procesora platnosci."""
    pass


class KontoZablokowane(Exception):
    """Wyjatek zglaszany przy probie operacji na zablokowanym koncie."""
    pass
