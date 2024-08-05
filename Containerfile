FROM quay.io/fedora/fedora:40

# Base stuff
RUN dnf -y install \
        git \
        rsync \
        patch

# Install deps
RUN dnf -y install \
        ldc \
        cmake \
        gcc \
        gcc-c++ \
        SDL2-devel \
        freetype-devel \
        dub \
        gettext \
        dbus-devel \
        libva-devel \
        openssl-devel

ADD scripts/build.sh /opt/build/build.sh
ADD scripts/semver.sh /opt/build/semver.sh

WORKDIR /opt/build/

CMD ./build.sh
