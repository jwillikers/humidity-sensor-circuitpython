default: install

alias f := format
alias fmt := format

format:
    venv/bin/ruff format .
    just --fmt --unstable

init:
    [ -d venv ] || python -m venv venv
    venv/bin/python -m pip install -r requirements-dev.txt
    venv/bin/pre-commit install

install:
    venv/bin/pipkin -m /run/media/$USER/CIRCUITPY install --compile -r requirements-circuitpython.txt
    cp code.py font/font5x8.bin /run/media/$USER/CIRCUITPY
    udisksctl unmount --block-device (findmnt --noheadings --output SOURCE --target /run/media/$USER/CIRCUITPY)

alias l := lint

lint:
    venv/bin/ruff check .

sync:
    venv/bin/pip-sync requirements-dev.txt requirements.txt

alias u := update

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
