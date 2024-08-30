SHELL:=/bin/bash

ZIP_FILE ?= translation-service.zip

# Jenkins required commands
.PHONY: lock
lock: 	## install the dependencies
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pipenv lock

.PHONY: install
install: 	## install the dependencies
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv sync --dev
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv graph

.PHONY: shell
shell: 	## start the shell
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv shell

.PHONY: bundle
bundle: ## bundles the project
	mkdir -p build/libs build/distribution
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pipenv requirements > requirements.txt
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pip install -r requirements.txt -t build/libs/
	cp -rf lib/mumble/pymumble_py3 build/libs
	cp -rf lib/py-opuslib build/libs
	cd build/libs/; zip -qr ../distribution/${ZIP_FILE} .; cd ../../
	cd src/; zip -qr ../build/distribution/${ZIP_FILE} .; cd ..
	zip -qr build/distribution/${ZIP_FILE} res;
