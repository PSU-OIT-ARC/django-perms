.PHONY = all upload clean test

all:
	python setup.py sdist

upload:
	python setup.py sdist upload

clean:
	find . -name __pycache__ -type d -print0 | xargs -0 rm -r
	find . -name "*.py[co]" -print0 | xargs -0 rm
	rm -rf .coverage *.egg-info build dist
