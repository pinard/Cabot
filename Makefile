SETUP = python setup.py --quiet

all:
	$(SETUP) build

install:
	$(SETUP) install

tags:
	find -name '*.py' | egrep -v '^./build|~$$' | etags -
