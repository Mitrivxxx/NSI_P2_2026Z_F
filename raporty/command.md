# Komendy

python3 -m venv .venv
source .venv/bin/activate
# testy
pytest tests/test_operacje.py -v

# pokrycie
pytest tests/test_operacje.py --cov=bank.system --cov-branch

# mutacje
pytest --gremlins --gremlin-targets=bank/system.py --gremlin-report=console,html tests/test_operacje.py
# raport: coverage/gremlins/index.html


# testy brzegowe dla utworz konto
pytest tests/test_lab4.py -k UtworzKonto -v 