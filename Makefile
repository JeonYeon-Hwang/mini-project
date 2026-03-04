PYTHON = python3
VENV = venv
VENV_BIN = $(VENV)/bin

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install -r requirements.txt

run:
	$(VENV_BIN)/python app.py