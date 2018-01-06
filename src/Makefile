.PHONY: all check checkstyle analyse test

all: check test

check: checkstyle analyse

checkstyle:
	flake8 --ignore=F401,W503 .

analyse:
	mypy app.py

test:
	py.test -v