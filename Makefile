.PHONY = all upload clean test

init:
	virtualenv -p python3 .env
	.env/bin/pip install -e .[dev]
	./runtests.py

all:
	python setup.py sdist

upload:
	python setup.py sdist upload

clean:
	find . -name __pycache__ -type d -print0 | xargs -0 rm -r
	find . -name "*.py[co]" -print0 | xargs -0 rm
	rm -rf .coverage *.egg-info build dist

test:
	./runtests.py
