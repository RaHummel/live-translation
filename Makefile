SHELL:=/bin/bash

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