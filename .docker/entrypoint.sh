#!/usr/bin/env bash
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

source /etc/profile.d/marv_env.sh

set -e

if [[ -n "$DEBUG" ]]; then
    set -x
fi

if [[ -n "$DEVELOP" ]]; then
    find "$DEVELOP" -maxdepth 2 -name setup.py -execdir $MARV_VENV/bin/pip install -e . \;
fi

if [[ -e "$MARV_CONFIG" ]]; then
    if [[ -n "$MARV_INIT" ]] || [[ ! -e "$MARV_SITE/sessionkey" ]]; then
	$MARV_VENV/bin/marv init
    fi
fi

( cd "$MARV_SITE" && "$@" ) &
PID="$!"
trap "kill -INT $PID" INT
trap "kill -TERM $PID" TERM
trap "kill -KILL $PID" KILL
echo "Container startup complete."
wait
