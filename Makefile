
FILES = namingmuse/*.py setup.py

all: $(FILES) doc
	./setup.py build

install: all
	./setup.py install

clean:
	./setup.py clean
	find -iname \*.pyc -exec rm {} \;
	rm -rf MANIFEST build dist README

dist: clean
	./setup.py sdist

doc:
	cat README.in > README
	./nmuse --doc >> README

rpm:
	./setup.py bdist_rpm
