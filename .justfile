default: install

alias f := format
alias fmt := format

format:
    venv/bin/ruff format .
    just --fmt --unstable

init:
    [ -d venv ] || python -m venv venv
    venv/bin/python -m pip install --requirement requirements.txt

init-dev: && sync
    [ -d venv ] || python -m venv venv
    venv/bin/python -m pip install --requirement requirements-dev.txt
    venv/bin/pre-commit install

install-circuitpython version="7.2.5":
    curl --location --output-dir /run/media/$(id --name --user)/RPI-RP2 --remote-name https://downloads.circuitpython.org/bin/adafruit_qtpy_rp2040/en_US/adafruit-circuitpython-adafruit_qtpy_rp2040-en_US-{{ version }}.uf2

install:
    venv/bin/pipkin --mount /run/media/$(id --name --user)/CIRCUITPY install --compile --requirement requirements-circuitpython.txt
    cp code.py font/font5x8.bin /run/media/$(id --name --user)/CIRCUITPY
    udisksctl unmount --block-device $(findmnt --noheadings --output SOURCE --target /run/media/$(id --name --user)/CIRCUITPY)

alias l := lint

lint:
    venv/bin/yamllint .
    venv/bin/ruff check --fix .

sync:
    venv/bin/pip-sync requirements-dev.txt requirements.txt

alias u := update
alias up := update

update:
    venv/bin/pip-compile \
        --allow-unsafe \
        --generate-hashes \
        --reuse-hashes \
        --upgrade \
        requirements-dev.in
    venv/bin/pip-compile \
        --allow-unsafe \
        --generate-hashes \
        --reuse-hashes \
        --upgrade \
        requirements.in
    venv/bin/pip-compile \
        --allow-unsafe \
        --generate-hashes \
        --no-annotate \
        --no-header \
        --output-file requirements-circuitpython.txt \
        --reuse-hashes \
        --upgrade \
        requirements.in
    awk \
        -i inplace \
        '/adafruit-circuitpython/{c=2} c&&c--' \
        requirements-circuitpython.txt
    venv/bin/pre-commit autoupdate
