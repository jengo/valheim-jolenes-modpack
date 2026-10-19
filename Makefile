all: build

build:
	python scripts/validate.py
	python scripts/build.py

publish:
	python scripts/publish.py

