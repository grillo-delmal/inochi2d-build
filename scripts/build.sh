#!/usr/bin/bash

set -e

source /opt/build/semver.sh

# Clean out folder
find /opt/out/ -mindepth 1 -maxdepth 1 -exec rm -r -- {} +

echo "======== Loading sources ========"

cd /opt
mkdir -p src

rsync --info=progress2 -azh /opt/orig/inochi-creator/ /opt/src/inochi-creator/
rsync --info=progress2 -azh /opt/orig/inochi-session/ /opt/src/inochi-session/

rsync --info=progress2 -azh /opt/orig/bindbc-spout2/ /opt/src/bindbc-spout2/
rsync --info=progress2 -azh /opt/orig/dportals/ /opt/src/dportals/
rsync --info=progress2 -azh /opt/orig/facetrack-d/ /opt/src/facetrack-d/
rsync --info=progress2 -azh /opt/orig/fghj/ /opt/src/fghj/
rsync --info=progress2 -azh /opt/orig/i18n/ /opt/src/i18n/
rsync --info=progress2 -azh /opt/orig/i2d-imgui/ /opt/src/i2d-imgui/
rsync --info=progress2 -azh /opt/orig/i2d-opengl/ /opt/src/i2d-opengl/
rsync --info=progress2 -azh /opt/orig/inmath/ /opt/src/inmath/
rsync --info=progress2 -azh /opt/orig/inochi2d/ /opt/src/inochi2d/
rsync --info=progress2 -azh /opt/orig/inui/ /opt/src/inui/
rsync --info=progress2 -azh /opt/orig/kra-d/ /opt/src/kra-d/
rsync --info=progress2 -azh /opt/orig/psd-d/ /opt/src/psd-d/
rsync --info=progress2 -azh /opt/orig/vmc-d/ /opt/src/vmc-d/

echo "======== Applying patches ========"

if [ -d ./patches ]; then
    pushd patches
    if [ ! -z "$(ls -A */ 2> /dev/null)" ]; then
        for d in */ ; do
            for p in ${d}*.patch; do
                echo "patch /opt/patches/$p"
                git -C /opt/src/${d} apply /opt/patches/$p
            done
        done
    fi
    popd
fi

cat > /opt/src/inochi-creator/source/creator/ver.d <<EOF
module creator.ver;

enum INC_VERSION = "$(semver /opt/src/inochi-creator/)";
EOF

cat > /opt/src/inochi-session/source/session/ver.d <<EOF
module session.ver;

enum INS_VERSION = "$(semver /opt/src/inochi-session/)";
EOF

# FIX: Inochi2D version dependent on git
cat > /opt/src/inochi2d/source/inochi2d/ver.d <<EOF
module inochi2d.ver;

enum IN_VERSION = "$(semver /opt/src/inochi2d/)";
EOF

if [[ ! -z ${LOAD_CACHE} ]]; then

    echo "======== Loading cache ========"

    if [ -d /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiStatic ]; then
        mkdir -p /opt/src/i2d-imgui/deps/build_linux_x64_cimguiStatic/
        rsync -azh /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiStatic/ /opt/src/i2d-imgui/deps/build_linux_x64_cimguiStatic/
    fi
    if [ -d /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic ]; then
        mkdir -p /opt/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic/
        rsync -azh /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic/ /opt/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic/
    fi
    if [ -d /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic ]; then
        mkdir -p /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic/
        rsync -azh /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic/ /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic/
    fi
    if [ -d /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic ]; then
        mkdir -p /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic/
        rsync -azh /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic/ /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic/
    fi

    mkdir -p /opt/cache/.dub/
    rsync --info=progress2 -azh /opt/cache/.dub/ ~/.dub/

    rm -f /opt/cache/.dub/packages/local-packages.json
fi

echo "======== Loading dub dependencies ========"

# Add dlang deps
dub add-local /opt/src/bindbc-spout2/   "$(semver /opt/src/bindbc-spout2/)"
dub add-local /opt/src/dportals/        "$(semver /opt/src/dportals/)"
dub add-local /opt/src/facetrack-d/     "$(semver /opt/src/facetrack-d/)"
dub add-local /opt/src/fghj/            "$(semver /opt/src/fghj/)"
dub add-local /opt/src/i18n/            "$(semver /opt/src/i18n/)"
dub add-local /opt/src/i2d-imgui/       "$(semver /opt/src/i2d-imgui/)"
dub add-local /opt/src/i2d-opengl/      "$(semver /opt/src/i2d-opengl/)"
dub add-local /opt/src/inmath/          "$(semver /opt/src/inmath/)"
dub add-local /opt/src/inochi2d/        "$(semver /opt/src/inochi2d/)"
dub add-local /opt/src/inui/            "$(semver /opt/src/inui/)"
dub add-local /opt/src/kra-d/           "$(semver /opt/src/kra-d/)"
dub add-local /opt/src/psd-d/           "$(semver /opt/src/psd-d/)"
dub add-local /opt/src/vmc-d/           "$(semver /opt/src/vmc-d/)"

if [[ ! -z ${PREBUILD_IMGUI} ]]; then

    echo "======== Prebuild imgui ========"

    # Build i2d-imgui deps
    pushd src
    pushd i2d-imgui

    mkdir -p deps/build_linux_x64_cimguiStatic
    mkdir -p deps/build_linux_x64_cimguiDynamic

    ARCH=$(uname -m)
    if [ "${ARCH}" == 'x86_64' ]; then
        if [[ -z ${DEBUG} ]]; then
            cmake -DSTATIC_CIMGUI= -S deps -B deps/build_linux_x64_cimguiStatic
            cmake --build deps/build_linux_x64_cimguiStatic --config Release

            cmake -S deps -B deps/build_linux_x64_cimguiDynamic
            cmake --build deps/build_linux_x64_cimguiDynamic --config Release
        else
            cmake -DCMAKE_BUILD_TYPE=Debug -DSTATIC_CIMGUI= -S deps -B deps/build_linux_x64_cimguiStatic
            cmake --build deps/build_linux_x64_cimguiStatic --config Debug

            cmake -DCMAKE_BUILD_TYPE=Debug -S deps -B deps/build_linux_x64_cimguiDynamic
            cmake --build deps/build_linux_x64_cimguiDynamic --config Debug

        fi
    elif [ "${ARCH}" == 'aarch64' ]; then
        if [[ -z ${DEBUG} ]]; then
            cmake -DSTATIC_CIMGUI= -S deps -B deps/build_linux_aarch64_cimguiStatic
            cmake --build deps/build_linux_aarch64_cimguiStatic --config Release

            cmake -S deps -B deps/build_linux_aarch64_cimguiDynamic
            cmake --build deps/build_linux_aarch64_cimguiDynamic --config Release
        else
            cmake -DCMAKE_BUILD_TYPE=Debug -DSTATIC_CIMGUI= -S deps -B deps/build_linux_aarch64_cimguiStatic
            cmake --build deps/build_linux_aarch64_cimguiStatic --config Debug

            cmake -DCMAKE_BUILD_TYPE=Debug -S deps -B deps/build_linux_aarch64_cimguiDynamic
            cmake --build deps/build_linux_aarch64_cimguiDynamic --config Debug
        fi

    fi
    popd
    popd
fi

if [[ ! -z ${CREATOR} ]]; then
    echo "======== Starting creator ========"

    # Build inochi-creator
    pushd src
    pushd inochi-creator

    # Remove branding assets
    rm -rf res/Inochi-Creator.iconset/
    find res/ui/ -type f -not -name "grid.png" -delete
    rm res/icon.png
    rm res/logo.png
    rm res/logo_256.png
    rm res/shaders/ada.frag
    rm res/shaders/ada.vert

    # Replace files
    rm source/creator/config.d
    rsync -azh /opt/files/inochi-creator/ $(pwd)

    # Gen tl files
    chmod +x ./gentl.sh
    ./gentl.sh

    if [[ ! -z ${DEBUG} ]]; then
        export DFLAGS='-g --d-debug'
    fi
    export DC='/usr/bin/ldc2'
    if [[ ! -z ${PREDOWNLOAD_LIBS} ]]; then
        echo "======== Downloading creator libs ========"
        echo "Download time" > /opt/out/creator-stats 
        if [[ -z ${LOAD_CACHE} ]]; then

            { time \
                dub describe \
                    --config=barebones \
                    --cache=user \
                        2>&1 > /opt/out/creator-describe ; \
                }  2>> /opt/out/creator-stats 
        else
            { time \
                dub describe \
                    --config=barebones \
                    --cache=user \
                    --skip-registry=all \
                        2>&1 > /opt/out/creator-describe ; \
                }  2>> /opt/out/creator-stats 
        fi
        echo "" >> /opt/out/creator-stats 
    fi
    echo "======== Building creator ========"
    echo "Build time" >> /opt/out/creator-stats 
    if [[ -z ${LOAD_CACHE} ]]; then
    { time \
        dub build \
            --config=barebones \
            --cache=user \
                2>&1 ; \
        } 2>> /opt/out/creator-stats 
    else
        { time \
            dub build \
                --config=barebones \
                --cache=user \
                --skip-registry=all \
                    2>&1 ; \
            } 2>> /opt/out/creator-stats 
    fi
    popd
    popd
fi

if [[ ! -z ${SESSION} ]]; then
    echo "======== Starting session ========"

    # Build inochi-session
    pushd src
    pushd inochi-session
    mkdir -p out
    if [[ ! -z ${DEBUG} ]]; then
        export DFLAGS='-g --d-debug'
    fi
    export DC='/usr/bin/ldc2'
    if [[ ! -z ${PREDOWNLOAD_LIBS} ]]; then
        echo "======== Downloading session libs ========"
        echo "Download time" > /opt/out/session-stats 
        if [[ -z ${LOAD_CACHE} ]]; then
            { time \
                dub describe \
                    --config=barebones \
                    --cache=user \
                    --override-config=facetrack-d/web-adaptors \
                        2>&1 > /opt/out/session-describe ; \
                }  2>> /opt/out/session-stats
        else
            { time \
                dub describe \
                    --config=barebones \
                    --cache=user \
                    --override-config=facetrack-d/web-adaptors \
                    --skip-registry=all \
                        2>&1 > /opt/out/session-describe ; \
                }  2>> /opt/out/session-stats
        fi
        echo "" >> /opt/out/session-stats 
    fi
    echo "======== Building session ========"
    echo "Build time" >> /opt/out/session-stats 
    if [[ -z ${LOAD_CACHE} ]]; then
        { time \
            dub build \
                --config=barebones \
                --cache=user \
                --override-config=facetrack-d/web-adaptors \
                    2>&1 ; \
            } 2>> /opt/out/session-stats
    else
        { time \
            dub build \
                --config=barebones \
                --cache=user \
                --override-config=facetrack-d/web-adaptors \
                --skip-registry=all \
                    2>&1 ; \
            } 2>> /opt/out/session-stats
    fi
    popd
    popd
fi

echo "======== Getting results ========"

if [[ ! -z ${CREATOR} ]]; then
    # Install inochi-creator
    rsync -azh /opt/src/inochi-creator/out/ /opt/out/inochi-creator/
    echo "" >> /opt/out/creator-stats 
    echo "Result files" >> /opt/out/creator-stats 
    echo "" >> /opt/out/creator-stats 
    du -sh /opt/out/inochi-creator/* >> /opt/out/creator-stats 
fi

if [[ ! -z ${SESSION} ]]; then
    # Install inochi-session
    rsync -azh /opt/src/inochi-session/out/ /opt/out/inochi-session/
    echo "" >> /opt/out/session-stats 
    echo "Result files" >> /opt/out/session-stats 
    echo "" >> /opt/out/session-stats 
    du -sh /opt/out/inochi-session/* >> /opt/out/session-stats
fi

# ---
dub list > /opt/out/version_dump

if [[ ! -z ${SAVE_CACHE} ]]; then
    echo "======== Saving cache ========"

    if [[ -z ${LOAD_CACHE} ]]; then
        find /opt/cache/ -mindepth 1 -maxdepth 1 -exec rm -r -- {} +
    fi

    mkdir -p /opt/cache/.dub/
    rsync --info=progress2 -azh ~/.dub/ /opt/cache/.dub/

    if [ -d /opt/src/i2d-imgui/deps/build_linux_x64_cimguiStatic ]; then
        mkdir -p /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiStatic/
        rsync --info=progress2 -azh /opt/src/i2d-imgui/deps/build_linux_x64_cimguiStatic/ /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiStatic/
    fi
    if [ -d /opt/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic ]; then
        mkdir -p /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic/
        rsync --info=progress2 -azh /opt/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic/  /opt/cache/src/i2d-imgui/deps/build_linux_x64_cimguiDynamic/
    fi
    if [ -d /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic ]; then
        mkdir -p /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic/
        rsync --info=progress2 -azh /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic/  /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiStatic/
    fi
    if [ -d /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic ]; then
        mkdir -p /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic/
        rsync --info=progress2 -azh /opt/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic/ /opt/cache/src/i2d-imgui/deps/build_linux_aarch64_cimguiDynamic/
    fi

fi

