# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

FROM ubuntu:focal

ARG PYTHON=python3.8

# This warning can simply be ignored:
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

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV MARV_VENV=/opt/marv
COPY requirements/* ${MARV_VENV}/requirements/
RUN cd ${MARV_VENV} && \
    ${PYTHON} -m venv . && \
    ./bin/pip install -U -r requirements/venv.txt && \
    ./bin/pip install -U -c requirements/marv.txt cython && \
    ./bin/pip install -U -r requirements/marv.txt && \
    ./bin/pip install -U -r requirements/marv-robotics.txt && \
    ./bin/pip install opencv-python-headless==4.3.0.36 && \
    ./bin/pip install -U -r requirements/develop.txt && \
    rm -rf /root/.cache/pip /root/.cache/matplotlib && \
    rmdir /root/.cache || (ls -la /root/.cache; exit 1)

COPY CHANGES.rst ${MARV_VENV}/CHANGES.rst
COPY CONTRIBUTING.rst ${MARV_VENV}/CONTRIBUTING.rst
COPY tutorial ${MARV_VENV}/tutorial
COPY code ${MARV_VENV}/code
COPY docs ${MARV_VENV}/docs
RUN rm ${MARV_VENV}/docs/config/marv.conf
COPY sites/example/marv.conf ${MARV_VENV}/docs/config/marv.conf
COPY scripts ${MARV_VENV}/scripts

ARG version=

# For internal use only
ARG dist=
COPY ${dist:-CHANGES.rst} ${MARV_VENV}/dist

RUN bash -c '\
    set -e; \
    cd ${MARV_VENV}; \
    if [[ -n "${dist}" ]]; then \
        ./bin/pip install --no-index -f ${MARV_VENV}/dist marv=="${version}"; \
        ./bin/pip install --no-index -f ${MARV_VENV}/dist marv-robotics=="${version}"; \
    else \
        rm ${MARV_VENV}/dist; \
        find code -maxdepth 2 -name setup.py -execdir ${MARV_VENV}/bin/pip install --no-deps . \; ; \
        (source ./bin/activate && ./scripts/build-docs); \
        ./bin/pip install -U --no-deps ./code/marv; \
    fi; \
    if [[ -d /root/.cache ]]; then \
        rm -rf /root/.cache/pip /root/.cache/matplotlib; \
        rmdir /root/.cache || (ls -la /root/.cache; exit 1) \
    fi; \
    '
RUN chown -R 1000:1000 /opt/marv

COPY .docker/entrypoint.sh /marv_entrypoint.sh
COPY .docker/env.sh /etc/profile.d/marv_env.sh
RUN echo 'source /etc/profile.d/marv_env.sh' >> /etc/bash.bashrc

ENV ACTIVATE_VENV=1
ENTRYPOINT ["/marv_entrypoint.sh"]
CMD ["/bin/sh", "-c", "trap 'exit 147' TERM; tail -f /dev/null & while wait ${!}; [ $? -ge 128 ]; do true; done"]
