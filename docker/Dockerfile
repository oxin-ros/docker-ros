ARG BASE_IMAGE

############ dependencies ######################################################
FROM ${BASE_IMAGE} as dependencies

USER root
SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive

# create workspace folder structure
ENV WORKSPACE=/docker-ros/ws
WORKDIR $WORKSPACE
RUN mkdir -p src/target src/upstream src/downstream

# setup keys and sources.list for ROS packages
ARG ROS_DISTRO
ENV ROS_DISTRO=${ROS_DISTRO}
RUN test -n "$ROS_DISTRO" || (echo "missing build-arg: ROS_DISTRO" && false)
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654 && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null && \
    rm -rf /var/lib/apt/lists/*

# install ROS bootstrapping tools
RUN apt-get update && \
    apt-get install -y \
        git \
        python3-rosdep \
        python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# copy contents of repository
COPY . src/target

# clone .repos upstream dependencies
ARG GIT_HTTPS_SERVER=
ARG GIT_HTTPS_USER=
ARG GIT_HTTPS_PASSWORD=
RUN if [[ -n ${GIT_HTTPS_SERVER} ]]; then \
        git config --global url.https://${GIT_HTTPS_USER}:${GIT_HTTPS_PASSWORD}@${GIT_HTTPS_SERVER}.insteadOf https://${GIT_HTTPS_SERVER} ; \
    fi
ARG GIT_SSH_PRIVATE_KEY=
ARG GIT_SSH_KNOWN_HOST_KEYS=
RUN if [[ -n ${GIT_SSH_PRIVATE_KEY} ]]; then \
        echo -e ${GIT_SSH_PRIVATE_KEY} > /tmp/ssh_id && \
        chmod 400 /tmp/ssh_id && \
        git config --global core.sshCommand "ssh -i /.ssh_key" && \
        mkdir -p ~/.ssh && \
        touch ~/.ssh/known_hosts && \
        echo -e ${GIT_SSH_KNOWN_HOST_KEYS} >> ~/.ssh/known_hosts ; \
    fi
COPY docker/docker-ros/docker/recursive_vcs_import.py /usr/local/bin
RUN apt-get update && \
    apt-get install -y python-is-python3 && \
    rm -rf /var/lib/apt/lists/*
RUN /usr/local/bin/recursive_vcs_import.py src src/upstream

# create install script with list of rosdep dependencies
RUN echo "set -e" >> $WORKSPACE/.install-dependencies.sh && \
    apt-get update && \
    rosdep init || true && \
    rosdep update --rosdistro ${ROS_DISTRO} && \
    export OS="ubuntu:$(lsb_release -c | awk '{print $2}')" && \
    if [[ "$ROS_DISTRO" = "rolling" && "$OS" = "ubuntu:focal" ]]; then export OS="ubuntu:jammy"; fi && \
    set -o pipefail && \
    ROS_PACKAGE_PATH=$(pwd):$ROS_PACKAGE_PATH rosdep install --os $OS -y --simulate --from-paths src --ignore-src | tee -a $WORKSPACE/.install-dependencies.sh && \
    chmod +x $WORKSPACE/.install-dependencies.sh && \
    rm -rf /var/lib/apt/lists/*

# add additionally specified apt dependencies to install script
ARG ADDITIONAL_DEBS_FILE="docker/additional-debs.txt"
ARG ENABLE_RECURSIVE_ADDITIONAL_DEBS="false"
RUN echo "apt-get install -y \\" >> $WORKSPACE/.install-dependencies.sh && \
    set -o pipefail && \
    if [[ $ENABLE_RECURSIVE_ADDITIONAL_DEBS == 'true' ]]; then \
        find . -type f -name $(basename {ADDITIONAL_DEBS_FILE}) -exec sed '$a\' {} \; | awk '{print "  " $0 " \\"}' >> $WORKSPACE/.install-dependencies.sh ; \
    elif [[ -f src/target/${ADDITIONAL_DEBS_FILE} ]]; then \
        cat src/target/${ADDITIONAL_DEBS_FILE} | awk '{print "  " $0 " \\"}' >> $WORKSPACE/.install-dependencies.sh ; \
    fi && \
    echo ";" >> $WORKSPACE/.install-dependencies.sh

# add additionally specified pip dependencies to install script
ARG ADDITIONAL_PIP_FILE="docker/additional-pip-requirements.txt"
ARG ENABLE_RECURSIVE_ADDITIONAL_PIP="false"
RUN echo "pip install pip \\" >> $WORKSPACE/.install-dependencies.sh && \
    set -o pipefail && \
    if [[ $ENABLE_RECURSIVE_ADDITIONAL_PIP == 'true' ]]; then \
        find . -type f -name $(basename ${ADDITIONAL_PIP_FILE}) -exec sed '$a\' {} \; | awk '{print "  " $0 " \\"}' >> $WORKSPACE/.install-dependencies.sh ; \
    elif [[ -f src/target/${ADDITIONAL_PIP_FILE} ]]; then \
        cat src/target/${ADDITIONAL_PIP_FILE} | awk '{print "  " $0 " \\"}' >> $WORKSPACE/.install-dependencies.sh ; \
    fi && \
    echo ";" >> $WORKSPACE/.install-dependencies.sh

# add custom installation commands to install script
ARG CUSTOM_SCRIPT_FILE="docker/custom.sh"
ARG ENABLE_RECURSIVE_CUSTOM_SCRIPT="false"
RUN if [[ $ENABLE_RECURSIVE_CUSTOM_SCRIPT == 'true' ]]; then \
        find . -type f -name $(basename ${CUSTOM_SCRIPT_FILE}) -exec sed '$a\' {} >> $WORKSPACE/.install-dependencies.sh \; ; \
    elif [[ -f src/target/${CUSTOM_SCRIPT_FILE} ]]; then \
        cat src/target/${CUSTOM_SCRIPT_FILE} >> $WORKSPACE/.install-dependencies.sh ; \
    fi

# remove additional-files folder from copied repository content to avoid redundancies
ARG ADDITIONAL_FILES_DIR="docker/additional-files"
RUN rm -rf src/target/${ADDITIONAL_FILES_DIR}

############ dependencies-install ##############################################
FROM ${BASE_IMAGE} AS dependencies-install
ARG TARGETARCH
ARG GIT_HTTPS_URL
ARG GIT_HTTPS_USER
ARG GIT_HTTPS_PASSWORD
ENV TARGETARCH=${TARGETARCH}
ENV DOCKER_ROS=1

USER root
SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive

# user setup
ENV DOCKER_USER=dockeruser
ENV DOCKER_UID=
ENV DOCKER_GID=

# ROS setup
ENV RCUTILS_COLORIZED_OUTPUT=1
ENV WORKSPACE=/docker-ros/ws
ENV COLCON_HOME=$WORKSPACE/.colcon
WORKDIR $WORKSPACE

# setup keys and sources.list for ROS packages
ARG ROS_DISTRO
ENV ROS_DISTRO=${ROS_DISTRO}
RUN test -n "$ROS_DISTRO" || (echo "missing build-arg: ROS_DISTRO" && false)
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654 && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null && \
    rm -rf /var/lib/apt/lists/*

# copy contents of files-folder into image
ARG ADDITIONAL_FILES_DIR="docker/additional-files"
ADD ${ADDITIONAL_FILES_DIR}* /docker-ros/additional-files/

# install essential build tools and dependencies for install script
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gosu \
        python-is-python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# copy install script from dependencies stage
COPY --from=dependencies $WORKSPACE/.install-dependencies.sh $WORKSPACE/.install-dependencies.sh

# install dependencies
RUN apt-get update && \
    $WORKSPACE/.install-dependencies.sh && \
    rm -rf /var/lib/apt/lists/*

# install ROS CLI tools
RUN source /opt/ros/$ROS_DISTRO/setup.bash && \
    apt-get update && \
    if [[ "$ROS_VERSION" == "1" ]]; then \
        apt-get install -y \
            python3-catkin-tools ; \
    elif [[ "$ROS_VERSION" == "2" ]]; then \
        apt-get install -y \
            python3-colcon-common-extensions ; \
    fi \
    && rm -rf /var/lib/apt/lists/*

# source ROS
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> ~/.bashrc

# set entrypoint
COPY docker/docker-ros/docker/entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

############ dev ###############################################################
FROM dependencies-install as dev

# copy contents of repository from dependencies stage
COPY --from=dependencies $WORKSPACE/src $WORKSPACE/src

CMD ["bash"]

############ build #############################################################
FROM dev as build

# build ROS workspace
RUN if [[ -x "$(command -v colcon)" ]]; then \
        source /opt/ros/${ROS_DISTRO}/setup.bash && \
        colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release ; \
    elif [[ -x "$(command -v catkin)" ]]; then \
        catkin config --install --extend /opt/ros/${ROS_DISTRO} && \
        catkin build -DCMAKE_BUILD_TYPE=Release --force-color --no-status --summarize ; \
    fi

############ run ###############################################################
FROM dependencies-install as run

# copy ROS install space from build stage
COPY --from=build $WORKSPACE/install install
RUN ldconfig
RUN echo "[[ -f $WORKSPACE/devel/setup.bash ]] && source $WORKSPACE/devel/setup.bash" >> ~/.bashrc && \
    echo "[[ -f $WORKSPACE/install/setup.bash ]] && source $WORKSPACE/install/setup.bash" >> ~/.bashrc

# setup command
ARG COMMAND
ENV DEFAULT_CMD=${COMMAND}
CMD bash -c "${DEFAULT_CMD}"
