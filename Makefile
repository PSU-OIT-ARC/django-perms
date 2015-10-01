.PHONY = all upload clean test

all:
	./setup.py sdist

upload:
	./setup.py sdist upload

clean:
	rm -rf django_perms.egg-info dist
