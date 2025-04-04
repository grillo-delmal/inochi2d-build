FROM quay.io/fedora/fedora:42

# Base stuff
RUN dnf -y install \
        git \
        rsync \
        patch \
        jq \
        awk

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
