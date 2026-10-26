.PHONY: all build publish upgrade

all: build

build:
	python scripts/validate.py
	python scripts/build.py

publish:
	python scripts/publish.py

upgrade:
	python3 scripts/update_dependencies.py
