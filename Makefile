
FILES = namingmuse/*.py setup.py

all: $(FILES) doc
	./setup.py build

install: all
	./setup.py install

clean:
	./setup.py clean
	rm -rf MANIFEST build dist README *.pyc */*.pyc

dist: clean
	./setup.py sdist

doc:
	cat README.in > README
	./nmuse --doc >> README

rpm:
	./setup.py bdist_rpm
