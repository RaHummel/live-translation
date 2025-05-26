SHELL:=/bin/bash

ZIP_FILE ?= translation-service.zip

# Jenkins required commands
.PHONY: lock
lock: 	## install the dependencies
	pipenv run pipenv lock

.PHONY: install
install: 	## install the dependencies
	pipenv sync --dev
	pipenv graph

.PHONY: shell
shell: 	## start the shell
	pipenv shell

.PHONY: bundle
bundle: ## bundles the project
	mkdir -p build/libs build/distribution
	pipenv run pipenv requirements > requirements.txt
	pipenv run pip install -r requirements.txt -t build/libs/
	cp -rf lib/mumble/pymumble_py3 build/libs
	cp -rf lib/py-opuslib/opuslib build/libs
	cd build/libs/; zip -qr ../distribution/${ZIP_FILE} .; cd ../../
	cd src/; zip -qr ../build/distribution/${ZIP_FILE} .; cd ..
	zip -qr build/distribution/${ZIP_FILE} res;
