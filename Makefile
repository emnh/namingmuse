
FILES = namingmuse/*.py setup.py

all: $(FILES) doc
	./setup.py build

install: all
	./setup.py install

clean:
	./setup.py clean
	rm -rf build dist README *.pyc */*.pyc

dist: all
	./setup.py sdist

doc:
	./nmuse --doc > README

rpm:
	./setup.py bdist_rpm
