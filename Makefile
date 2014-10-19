build:
	python setup.py build
install:
	python setup.py install
genenerate_pot:
	python scripts/generate_pot.py
compile_translations:
	python scripts/compile_translations.py
update_translations:
	python scripts/update_translations.py
clean:
	rm -rf build etc
	find . -name "*.pyc" -delete
.PHONY: install build clean
