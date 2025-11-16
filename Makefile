.PHONY: init-dev init-prod init preco install-prod docs docs-serve unittest\
bump2version _coverage coverage-html ruff mypy check-project-structure build help

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory
# Allow to pass parameters to targets
RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

# Allow Mac/Linux sed and echo commands
# sed: when mac 'sed -i' only works with -i ''
MAC_SED :=
ifeq ($(shell uname),Darwin)
	MAC_SED := ''
endif
# echo: when linux must use /bin/echo -e to allow colors
ECHO := /bin/echo -e
ECHO_N := ${ECHO} -n
ifeq ($(shell uname),Darwin)
	ECHO := echo
	ECHO_N := printf
endif

CURRENT_PATH := "$(CURDIR)"
CURRENT_DIR := "$(shell basename $(CURRENT_PATH))"

# Colors
_GREY=\x1b[30m
_RED=\x1b[31m
_GREEN=\x1b[32m
_YELLOW=\x1b[33m
_BLUE=\x1b[34m
_PURPLE=\x1b[35m
_CYAN=\x1b[36m
_WHITE=\x1b[37m
_END=\x1b[0m
_BOLD=\x1b[1m
_UNDER=\x1b[4m
_REV=\x1b[7m

PROJECT_DIR = config data docs docker notebooks tests config/packaging config/tests

PROJECT_FILES = Makefile pyproject.toml README.md \
config/pre-commit-hook-template \
config/tests/setup.cfg \
config/packaging/mkdocs.yml config/packaging/setup.cfg \
config/pre-commit/.pre-commit-config.yaml \
config/pre-commit/config.toml

# Pre commit config
PRE_COMMIT_HOOK_TEMPLATE_PATH=config/pre-commit-hook-template
CONFIG_DIR=$(shell bash -c 'source ${PRE_COMMIT_HOOK_TEMPLATE_PATH}; echo "$${CONFIG_DIR}"')

HAS_HOOKS_PATH := no
HOOKS_PATH="$(shell git config --get core.hooksPath)"

ifeq (${HOOKS_PATH},"/etc/global_hooks")
	HAS_HOOKS_PATH := yes
endif

PIPX_PATH_BIN="${HOME}/.local/bin"
PIPX_PATH_HOME="${HOME}/.local/pipx"
PRE_COMMIT="${PIPX_PATH_BIN}/pre-commit"
UV="${PIPX_PATH_BIN}/uv"


# Dev & Prod targets

## init
init: ## Initialise pre-commit automatically
	@${ECHO} "${_BLUE}Init: install pipx & pre-commit...${_END}" &&\
	${MAKE} _init_pip_step1 &&\
	${ECHO_N} "${_CYAN}Init: install pipx... ${_END}" &&\
	$(MAKE) _init_pipx_step2 &&\
	${ECHO} "${_CYAN}Init: install pre-commit... ${_END}" &&\
	$(MAKE) _init_preco_step3 &&\
	${ECHO} "${_BLUE}Init: install pipx & pre-commit... OK${_END}"

_init_pip_step1:
	@_="$(shell python3 -m pip install --upgrade pip)"

_init_pipx_step2:
	@_="$(shell PIPX_HOME='${PIPX_PATH_HOME}' PIPX_BIN_DIR='${PIPX_PATH_BIN}' python3 -m pip install pipx)" &&\
	${ECHO} "${_CYAN}OK${_END}"

_init_preco_step3:
	@_="$(shell PIPX_HOME="${PIPX_PATH_HOME}" PIPX_BIN_DIR="${PIPX_PATH_BIN}" python3 -m pipx install pre-commit)"

	@# pre-commit bug when core.hooksPath is set. So we disable temporary core.hooksPath.
	@if [ "$(HAS_HOOKS_PATH)" = 'yes' ]; then\
		sudo git config --system --unset core.hooksPath;\
	fi

	@${PRE_COMMIT} install

	@# pre-commit bug when core.hooksPath is set. So we disable temporary core.hooksPath.
	@if [ "$(HAS_HOOKS_PATH)" = "yes" ]; then\
		sudo git config --system core.hooksPath "${HOOKS_PATH}";\
	fi

	@sed -i ${MAC_SED} '/# start templated/ r '${PRE_COMMIT_HOOK_TEMPLATE_PATH} .git/hooks/pre-commit
	@sed -i ${MAC_SED} -r 's/\.pre\-commit\-config\.yaml/"$$CONFIG_DIR\/.pre-commit-config.yaml"/' .git/hooks/pre-commit

	@${ECHO} "${_CYAN}Init: install pre-commit... OK ${_END}"

## pre-commit
preco:
	${PRE_COMMIT} run --config "config/pre-commit/.pre-commit-config.yaml" --all-files ${RUN_ARGS}

ruff-check:
	make preco '\ruff-check' ${RUN_ARGS}

ruff-format:
	make preco '\ruff-format' ${RUN_ARGS}

### custom pre-commit checks
check-py3:
	@python3 -c "import compileall; compileall.compile_dir('python',force=True,quiet=1)"

## Install environment in prod
install-prod:
	@${ECHO} "${_BLUE}Install-prod: init & install uv & uv install packages + extra ...${_END}" &&\
	make _install_prod_uv_step1 &&\
	${ECHO} "${_CYAN}Install-prod: install uv ...${_END}" &&\
	make _install_prod_uv_step2 &&\
	${ECHO} "${_BLUE}Install-prod: init & install uv & uv install packages + extra ... OK${_END}"

_install_prod_uv_step1:
	@${ECHO} "${_CYAN}Install-prod: init ...${_END}"
	@make init

_install_prod_uv_step2:
	@_="$(shell PIPX_HOME="${PIPX_PATH_HOME}" PIPX_BIN_DIR="${PIPX_PATH_BIN}" python3 -m pipx install uv)" &&\
	${ECHO} "${_CYAN}Install-prod: uv install packages + extra ...${_END}" &&\
	${UV} sync --all-extras && \
	${ECHO} "${_CYAN}Install-prod: install uv ... OK${_END}"

## typing
mypy:
	make preco '\mypy' ${RUN_ARGS}

## docs
docs:
	${UV} run mkdocs build --config-file config/packaging/mkdocs.yml --site-dir "${PWD}/site"

### Serve documentation (prod)
docs-serve:
	${UV} run python -m http.server 3000 --directory site

### Deploy the documentation to gh-pages
docs-deploy:
	${UV} run mkdocs gh-deploy --config-file config/packaging/mkdocs.yml
	@${ECHO} "${_BLUE}https://alexym1.github.io/taglyatelle${_END}"

## Testing
unittest:
	${UV} run pytest ${RUN_ARGS} -c "config/tests/setup.cfg" tests/unitary

tox:
	tox -c "config/tests/setup.cfg" --workdir . --root . || true
	rm -rf python3.12/

_coverage:
	${UV} run pytest -c "config/tests/setup.cfg" --cov-config="config/tests/setup.cfg" --cov=taglyatelle --cov-branch --cov-report ${RUN_ARGS} tests/unitary

coverage:
	make _coverage term-missing

coverage-html:
	make _coverage html
	@${ECHO} "${_BLUE}open htmlcov/index.html or run 'make coverage-html-serve' ${_END}"

coverage-html-serve:
	python -m http.server 3000 --directory htmlcov


## packaging
build:
	${UV} build ${RUN_ARGS}

### Change package version (prod)
bump2version:
	${UV} run bump2version "${RUN_ARGS}" --commit-args="--no-verify" --config-file="config/packaging/setup.cfg"

### Run mypy
poetry-mypy:
	@${UV} run mypy --show-error-codes --config "./config/pre-commit/config.toml" ${RUN_ARGS}


docker-build:
	(docker build -t taglyatelle:0.1.0 .)

docker-run:
	(docker run -p 8000:8000 --env-file ".env" -v "private_key.pem:/app/private_key.pem:ro" taglyatelle:0.1.0)

show-api:
	@${UV} run uvicorn taglyatelle.exposition.taglyatelle_api:app --host 0.0.0.0 --port 8000
