# Default recipe to display help
_default:
    @just --list

# Allow Mac/Linux sed and echo commands
# sed: when mac 'sed -i' only works with -i ''
MAC_SED := if os() == "macos" { "''" } else { "" }

# echo: when linux must use /bin/echo -e to allow colors
ECHO := if os() == "macos" { "echo" } else { "/bin/echo -e" }
ECHO_N := if os() == "macos" { "printf" } else { "/bin/echo -e -n" }

CURRENT_PATH := justfile_directory()
CURRENT_DIR := file_name(justfile_directory())

# Colors
_GREY := "\\x1b[30m"
_RED := "\\x1b[31m"
_GREEN := "\\x1b[32m"
_YELLOW := "\\x1b[33m"
_BLUE := "\\x1b[34m"
_PURPLE := "\\x1b[35m"
_CYAN := "\\x1b[36m"
_WHITE := "\\x1b[37m"
_END := "\\x1b[0m"
_BOLD := "\\x1b[1m"
_UNDER := "\\x1b[4m"
_REV := "\\x1b[7m"

PROJECT_DIR := "config data docs docker notebooks tests config/packaging config/tests"

PROJECT_FILES := "Justfile pyproject.toml README.md config/tests/setup.cfg config/packaging/mkdocs.yml config/packaging/setup.cfg config/pre-commit/.pre-commit-config.yaml"

# Prek config
PREK := env_var('HOME') + "/.local/bin/prek"
PIPX_PATH_BIN := env_var('HOME') + "/.local/bin"
PIPX_PATH_HOME := env_var('HOME') + "/.local/pipx"
UV := PIPX_PATH_BIN + "/uv"

# Dev & Prod targets

# Initialise prek automatically
init:
    @{{ECHO}} "{{_BLUE}}Init: install pipx & prek...{{_END}}"
    @just _init_pip_step1
    @{{ECHO_N}} "{{_CYAN}}Init: install pipx... {{_END}}"
    @just _init_pipx_step2
    @{{ECHO}} "{{_CYAN}}Init: install prek... {{_END}}"
    @just _init_prek_step3
    @{{ECHO}} "{{_BLUE}}Init: install pipx & prek... OK{{_END}}"

_init_pip_step1:
    -@python3 -m pip install --upgrade pip > /dev/null 2>&1

_init_pipx_step2:
    -@PIPX_HOME='{{PIPX_PATH_HOME}}' PIPX_BIN_DIR='{{PIPX_PATH_BIN}}' python3 -m pip install pipx > /dev/null 2>&1
    @{{ECHO}} "{{_CYAN}}OK{{_END}}"

_init_prek_step3:
    #!/usr/bin/env bash
    set -euo pipefail
    {{PREK}} install --config config/pre-commit/.pre-commit-config.yaml
    {{ECHO}} "{{_CYAN}}Init: install prek... OK {{_END}}"

# Run prek checks
preco *args:
    {{PREK}} run --config config/pre-commit/.pre-commit-config.yaml --all-files {{args}}

# Run ruff check
ruff-check *args:
    @just preco '\ruff-check' {{args}}

# Run ruff format
ruff-format *args:
    @just preco '\ruff-format' {{args}}

# Custom pre-commit checks - check Python 3 compatibility
check-py3:
    @python3 -c "import compileall; compileall.compile_dir('python',force=True,quiet=1)"

# Install environment in prod
install-prod:
    @{{ECHO}} "{{_BLUE}}Install-prod: init & install uv & uv install packages + extra ...{{_END}}"
    @just _install_prod_uv_step1
    @{{ECHO}} "{{_CYAN}}Install-prod: install uv ...{{_END}}"
    @just _install_prod_uv_step2
    @{{ECHO}} "{{_BLUE}}Install-prod: init & install uv & uv install packages + extra ... OK{{_END}}"

_install_prod_uv_step1:
    @{{ECHO}} "{{_CYAN}}Install-prod: init ...{{_END}}"
    @just init

_install_prod_uv_step2:
    #!/usr/bin/env bash
    set -euo pipefail
    PIPX_HOME="" PIPX_BIN_DIR="" python3 -m pipx install uv > /dev/null 2>&1 || true
    {{ECHO}} "{{_CYAN}}Install-prod: uv install packages + extra ...{{_END}}"
    {{UV}} sync --all-extras
    {{ECHO}} "{{_CYAN}}Install-prod: install uv ... OK{{_END}}"

# Run mypy type checking
mypy *args:
    @just preco '\mypy' {{args}}

# Build documentation
docs:
    {{UV}} run mkdocs build --config-file docs/mkdocs.yml --site-dir "{{CURRENT_PATH}}/site"

# Serve documentation (prod)
docs-serve:
    {{UV}} run python -m http.server 3000 --directory site

# Deploy the documentation to gh-pages
docs-deploy:
    {{UV}} run mkdocs gh-deploy --config-file docs/mkdocs.yml
    @{{ECHO}} "{{_BLUE}}https://taglyatelle.github.io/taglyatelle{{_END}}"

# Run unit tests
unittest *args:
    {{UV}} run pytest {{args}} -c "config/tests/setup.cfg" tests/unitary

# Run tox tests
tox:
    {{UV}} run tox -c "config/tests/setup.cfg" --workdir . --root .
    -rm -rf python3.12/

_coverage *args:
    {{UV}} run pytest -c "config/tests/setup.cfg" --cov-config="config/tests/setup.cfg" --cov=taglyatelle --cov-branch --cov-report {{args}} tests/unitary

# Run coverage with terminal output
coverage:
    @just _coverage term-missing

# Generate HTML coverage report
coverage-html:
    @just _coverage html
    @{{ECHO}} "{{_BLUE}}open htmlcov/index.html or run 'just coverage-html-serve' {{_END}}"

# Serve HTML coverage report
coverage-html-serve:
    python -m http.server 3000 --directory htmlcov

# Build package
build *args:
    {{UV}} build {{args}}

# Change package version (prod)
bump2version *args:
    {{UV}} run bump-my-version bump {{args}} --commit-args="--no-verify" --config-file="config/packaging/setup.toml"

# Run mypy for uv
uv-mypy *args:
    @{{UV}} run mypy --show-error-codes {{args}}

# Build docker image
docker-build:
    docker build -t taglyatelle:0.2.0 .

# Run docker container
docker-run:
    docker run -p 8000:8000 --env-file ".env" -v "{{CURRENT_PATH}}/private_key.pem:/app/private_key.pem:ro" taglyatelle:0.2.0

# Start the API server
show-api:
    @{{UV}} run uvicorn taglyatelle.exposition.taglyatelle_api:app --host 0.0.0.0 --port 8000
