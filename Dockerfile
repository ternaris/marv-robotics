# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

FROM ubuntu:bionic

ARG PYTHON=python3.7

# This warning can simply be ignore:
# debconf: delaying package configuration, since apt-utils is not installed
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
        bash-completion \
        bc \
        capnproto \
        curl \
        ffmpeg \
        iputils-ping \
        jq \
        less \
        libcapnp-dev \
        libffi-dev \
        libfreetype6-dev \
        libjpeg-dev \
        liblz4-dev \
        libpng-dev \
        libssl-dev \
        libz-dev \
        locales \
        lsof \
        man \
        python3-pip \
        ${PYTHON} \
        ${PYTHON}-dev \
        ${PYTHON}-venv \
        rsync \
        sqlite3 \
        ssh \
        strace \
        tzdata \
        unzip \
        vim \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8; dpkg-reconfigure -f noninteractive locales
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8

ARG MARV_UID=1000
ARG MARV_GID=1000

RUN groupadd -g $MARV_GID marv && \
    useradd -m -u $MARV_UID -g $MARV_GID --shell /bin/bash marv

ARG venv=/opt/marv

ENV MARV_VENV=$venv
RUN bash -c '\
if [[ -n "$MARV_VENV" ]]; then \
    mkdir $MARV_VENV; \
    chown marv:marv $MARV_VENV; \
fi'

USER marv

COPY requirements/* /requirements/
RUN bash -c '\
if [[ -n "$MARV_VENV" ]]; then \
    ${PYTHON} -m venv $MARV_VENV; \
    $MARV_VENV/bin/pip install -U pip==19.2.3 setuptools==41.2.0 wheel==0.33.6; \
    $MARV_VENV/bin/pip install -U -r /requirements/marv-robotics.txt; \
    $MARV_VENV/bin/pip install -U -r /requirements/develop.txt; \
fi'

ARG code=code

COPY --chown=marv:marv ${code:-CHANGES.rst} /home/marv/code
RUN bash -c '\
if [[ -z "$code" ]]; then \
    rm /home/marv/code; \
fi'

ARG docs=docs

COPY --chown=marv:marv CHANGES.rst /home/marv/CHANGES.rst
COPY --chown=marv:marv tutorial /home/marv/tutorial
COPY --chown=marv:marv ${docs:-CHANGES.rst} /home/marv/docs
RUN bash -c '\
if [[ -z "$docs" ]]; then \
    rm -r /home/marv/docs /home/marv/CHANGES.rst /home/marv/tutorial; \
fi'

ARG scripts=scripts

COPY --chown=marv:marv ${scripts:-CHANGES.rst} /home/marv/scripts
RUN bash -c '\
if [[ -z "$scripts" ]]; then \
    rm /home/marv/scripts; \
fi'

ARG version=
ARG pypi_install_args=

RUN bash -c '\
if [[ -n "$MARV_VENV" ]]; then \
    if [[ -z "$code" ]]; then \
        ${MARV_VENV}/bin/pip install ${pypi_install_args} marv-robotics${version:+==${version}}; \
    else \
        find /home/marv/code -maxdepth 2 -name setup.py -execdir ${MARV_VENV}/bin/pip install --no-deps . \; ;\
        ${MARV_VENV}/bin/pip install /home/marv/code/marv-robotics; \
        (source "/opt/ros/$ROS_DISTRO/setup.bash"; source $MARV_VENV/bin/activate; /home/marv/scripts/build-docs); \
        ${MARV_VENV}/bin/pip install -U --no-deps /home/marv/code/marv-robotics; \
    fi \
fi'

USER root

COPY .docker/entrypoint.sh /marv_entrypoint.sh
COPY .docker/env.sh /etc/profile.d/marv_env.sh
RUN echo 'source /etc/profile.d/marv_env.sh' >> /etc/bash.bashrc

ENV ACTIVATE_VENV=1
ENTRYPOINT ["/marv_entrypoint.sh"]
CMD ["/bin/sh", "-c", "trap 'exit 147' TERM; tail -f /dev/null & while wait ${!}; [ $? -ge 128 ]; do true; done"]
