#!/usr/bin/env bash
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

if [ -z "$CENV" ]; then
    export CENV=1
    source /opt/ros/${ROS_DISTRO}/setup.bash
    source /opt/rosbag2/setup.bash
    if [[ -n "$ACTIVATE_VENV" ]] && [[ -n "$MARV_VENV" ]]; then
        source $MARV_VENV/bin/activate
    fi
    if [[ -d "/home/marv/site" ]]; then
        export MARV_SITE="/home/marv/site"
        export MARV_CONFIG="$MARV_SITE/marv.conf"
    fi
    cd
fi
