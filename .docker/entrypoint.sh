#!/usr/bin/env bash
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

source /etc/profile.d/marv_env.sh

set -e

if [[ -n "$DEBUG" ]]; then
    set -x
fi

echo "$TIMEZONE" > /etc/timezone
ln -sf /usr/share/zoneinfo/"$TIMEZONE" /etc/localtime
dpkg-reconfigure -f noninteractive tzdata

if [[ -n "$DEVELOP" ]]; then
    find "$DEVELOP" -maxdepth 2 -name setup.py -execdir su -c "$MARV_VENV/bin/pip install -e ." marv \;
fi

export HOME=/home/marv
cd $MARV_SITE

if [[ -d code ]]; then
    find code -maxdepth 2 -name setup.py -execdir su -c "$MARV_VENV/bin/pip install -e ." marv \;
fi

if [[ -n "$MARV_INIT" ]] || [[ ! -e db ]]; then
    su marv -p -c '/opt/marv/bin/marv --config "$MARV_CONFIG" init'
fi
su marv -p -c '/opt/marv/bin/marv --config "${MARV_CONFIG}" serve --host 0.0.0.0 --approot "${MARV_APPLICATION_ROOT:-/}" ${MARV_ARGS}' &

echo 'Container startup complete.'
exec "$@"
