# Komendy

```bash
# venv (raz / nowy terminal)
python3 -m venv .venv
source .venv/bin/activate
pip install pytest pytest-cov pytest-gremlins

# testy
pytest tests/test_operacje.py -v

# pokrycie
pytest tests/test_operacje.py --cov=bank.system --cov-branch

# mutacje
pytest --gremlins --gremlin-targets=bank/system.py --gremlin-report=console,html tests/test_operacje.py
# raport: coverage/gremlins/index.html
```
