.PHONY: all check checkstyle analyse test

all: check test

check: checkstyle analyse

checkstyle:
	python3 -m flake8 --ignore=F401,W503 .

analyse:
	python3 -m mypy app.py

test:
	python3 -m pytest -v