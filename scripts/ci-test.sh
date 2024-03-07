#!/usr/bin/env bash

system_flag=$1

uv_pip_install_test() {
    system_flag=$1
    uv pip install $system_flag -r requirements/test.py$(just python-version 2).txt 'phrasify @ .'
}

if [[ $system_flag != "--system" ]]; then
    uv venv
    source .venv/bin/activate
fi

uv_pip_install_test $system_flag
just _test-cov
