.PHONY = all upload clean test

all:
	python setup.py sdist

upload:
	python setup.py sdist upload

clean:
	rm -rf django_perms.egg-info dist
