# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

FROM ros:foxy-ros-base

ARG PYTHON=python3.8

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
        python3-pybind11 \
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

RUN cd /opt && \
    curl -sL https://github.com/ternaris/rosbag2/archive/marv-2020-07-30.zip > rosbag2.zip && \
    unzip rosbag2.zip && rm rosbag2.zip && \
    mkdir -p ws/src && mv rosbag2-marv-2020-07-30 ws/src/rosbag2 && \
    bash -c 'source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ws && colcon build --install /opt/rosbag2 --merge-install \
      --cmake-args " -DBUILD_TESTING=OFF" --packages-up-to rosbag2_py \
    ' && cd .. && rm -rf ws && \
    bash -c 'source /opt/ros/${ROS_DISTRO}/setup.bash && source /opt/rosbag2/setup.bash \
      ${PYTHON} -c "import rosbag2_py" \
    '


ARG MARV_UID=1000
ARG MARV_GID=1000

RUN groupadd -g $MARV_GID marv && \
    useradd -m -u $MARV_UID -g $MARV_GID --shell /bin/bash marv

ARG venv=/opt/marv

ENV MARV_VENV=$venv
RUN bash -c '\
if [[ -n "$MARV_VENV" ]]; then \
    mkdir $MARV_VENV && \
    chown marv:marv $MARV_VENV; \
fi'

USER marv

COPY requirements/* /home/marv/requirements/
RUN bash -c '\
if [[ -n "$MARV_VENV" ]]; then \
    ${PYTHON} -m venv $MARV_VENV && \
    $MARV_VENV/bin/pip install -U -r /home/marv/requirements/venv.txt; \
    $MARV_VENV/bin/pip install -U -c /home/marv/requirements/marv-robotics.txt cython && \
    $MARV_VENV/bin/pip install -U -r /home/marv/requirements/marv-robotics.txt && \
    $MARV_VENV/bin/pip install opencv-python-headless==4.3.0.36 && \
    $MARV_VENV/bin/pip install -U -r /home/marv/requirements/develop.txt; \
    rm -rf /home/marv/.cache/pip && rmdir /home/marv/.cache || (ls -la /home/marv/.cache; exit 1); \
fi'

ARG code=code

COPY --chown=marv:marv ${code:-CHANGES.rst} /home/marv/code
RUN bash -c '\
if [[ -z "$code" ]]; then \
    rm /home/marv/code; \
fi'

ARG docs=docs

COPY --chown=marv:marv CHANGES.rst /home/marv/CHANGES.rst
COPY --chown=marv:marv CONTRIBUTING.rst /home/marv/CONTRIBUTING.rst
COPY --chown=marv:marv tutorial /home/marv/tutorial
COPY --chown=marv:marv ${docs:-CHANGES.rst} /home/marv/docs
RUN bash -c '\
if [[ -z "$docs" ]]; then \
    rm -r /home/marv/{docs,CHANGES.rst,CONTRIBUTING.rst,tutorial}; \
fi'

ARG scripts=scripts

COPY --chown=marv:marv ${scripts:-CHANGES.rst} /home/marv/scripts
RUN bash -c '\
if [[ -z "$scripts" ]]; then \
    rm /home/marv/scripts; \
fi'

ARG dist=

COPY --chown=marv:marv ${dist:-CHANGES.rst} /home/marv/dist
RUN bash -c '\
if [[ -z "$dist" ]]; then \
    rm /home/marv/dist; \
fi'

ARG version=
ARG pypi_install_args=

RUN bash -c '\
if [[ -n "$MARV_VENV" ]]; then \
    if [[ -z "$code" ]]; then \
        ${MARV_VENV}/bin/pip install ${pypi_install_args} marv-robotics${version:+==${version}}; \
    else \
        find /home/marv/code -maxdepth 2 -name setup.py -execdir ${MARV_VENV}/bin/pip install --no-deps . \; && \
        ${MARV_VENV}/bin/pip install ${pypi_install_args} /home/marv/code/marv-robotics && \
        (source $MARV_VENV/bin/activate && /home/marv/scripts/build-docs) && \
        ${MARV_VENV}/bin/pip install -U --no-deps /home/marv/code/marv-robotics; \
    fi; \
    if [[ -d /home/marv/.cache ]]; then \
        rm -rf /home/marv/.cache/pip && rmdir /home/marv/.cache || (ls -la /home/marv/.cache; exit 1); \
    fi; \
fi'

USER root

COPY .docker/entrypoint.sh /marv_entrypoint.sh
COPY .docker/env.sh /etc/profile.d/marv_env.sh
RUN echo 'source /etc/profile.d/marv_env.sh' >> /etc/bash.bashrc

ENV ACTIVATE_VENV=1
ENTRYPOINT ["/marv_entrypoint.sh"]
CMD ["/bin/sh", "-c", "trap 'exit 147' TERM; tail -f /dev/null & while wait ${!}; [ $? -ge 128 ]; do true; done"]
