#!/usr/bin/bash

set -e

source /opt/build/semver.sh

# Clean out folder
find /opt/out/ -mindepth 1 -maxdepth 1 -exec rm -r -- {} +

cd /opt
mkdir src

rsync -r /opt/orig/inochi-creator/ /opt/src/inochi-creator/
rsync -r /opt/orig/inochi-session/ /opt/src/inochi-session/

rsync -r /opt/orig/bindbc-imgui/ /opt/src/bindbc-imgui/
rsync -r /opt/orig/bindbc-spout2/ /opt/src/bindbc-spout2/
rsync -r /opt/orig/dportals/ /opt/src/dportals/
rsync -r /opt/orig/facetrack-d/ /opt/src/facetrack-d/
rsync -r /opt/orig/fghj/ /opt/src/fghj/
rsync -r /opt/orig/i18n/ /opt/src/i18n/
rsync -r /opt/orig/inmath/ /opt/src/inmath/
rsync -r /opt/orig/inochi2d/ /opt/src/inochi2d/
rsync -r /opt/orig/inui/ /opt/src/inui/
rsync -r /opt/orig/psd-d/ /opt/src/psd-d/
rsync -r /opt/orig/vmc-d/ /opt/src/vmc-d/

pushd patches
for d in */ ; do
    for p in ${d}*.patch; do
        echo "patch /opt/patches/$p"
        git -C /opt/src/${d} apply /opt/patches/$p
    done
done
popd

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

# Add dlang deps
dub add-local /opt/src/bindbc-imgui/    "$(semver /opt/src/bindbc-imgui/)"
dub add-local /opt/src/bindbc-spout2/   "$(semver /opt/src/bindbc-spout2/)"
dub add-local /opt/src/dportals/        "$(semver /opt/src/dportals/)"
dub add-local /opt/src/facetrack-d/     "$(semver /opt/src/facetrack-d/)"
dub add-local /opt/src/fghj/            "$(semver /opt/src/fghj/)"
dub add-local /opt/src/i18n/            "$(semver /opt/src/i18n/)"
dub add-local /opt/src/inmath/          "$(semver /opt/src/inmath/)"
dub add-local /opt/src/inochi2d/        "$(semver /opt/src/inochi2d/ 0.8.0)"
dub add-local /opt/src/inui/            "$(semver /opt/src/inui/ 1.0.0)"
dub add-local /opt/src/psd-d/           "$(semver /opt/src/psd-d/)"
dub add-local /opt/src/vmc-d/           "$(semver /opt/src/vmc-d/)"

# Build bindbc-imgui deps
pushd src
pushd bindbc-imgui
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

# Build inochi-creator
pushd src
pushd inochi-creator

# Remove branding assets
rm -rf res/Inochi-Creator.iconset/
find res/ui/ -type f -not -name "grid.png" -delete
rm res/icon.png
rm res/Info.plist
rm res/logo.png
rm res/logo_256.png
rm res/inochi-creator.ico
rm res/inochi-creator.rc
rm res/shaders/ada.frag
rm res/shaders/ada.vert

# Replace files
rm source/creator/config.d
cp /opt/files/config.d source/creator/
cp /opt/files/empty.png res/ui/banner.png

# Gen tl files
chmod +x ./gentl.sh
./gentl.sh

if [[ ! -z ${DEBUG} ]]; then
    export DFLAGS='-g --d-debug'
fi
export DC='/usr/bin/ldc2'
echo "Download time" > /opt/out/creator-stats 
{ time \
    dub describe \
        --config=barebones \
        --cache=local \
            2>&1 > /opt/out/creator-describe ; \
    }  2>> /opt/out/creator-stats 
echo "" >> /opt/out/creator-stats 
echo "Build time" >> /opt/out/creator-stats 
{ time \
    dub build \
        --config=barebones \
        --cache=local \
            2>&1 ; \
    } 2>> /opt/out/creator-stats 
popd
popd

# Build inochi-session
pushd src
pushd inochi-session
if [[ ! -z ${DEBUG} ]]; then
    export DFLAGS='-g --d-debug'
fi
export DC='/usr/bin/ldc2'
echo "Download time" > /opt/out/session-stats 
{ time \
    dub describe \
        --config=barebones \
        --cache=local \
        --override-config=facetrack-d/web-adaptors \
            2>&1 > /opt/out/session-describe ; \
    }  2>> /opt/out/session-stats
echo "" >> /opt/out/session-stats 
echo "Build time" >> /opt/out/session-stats 
{ time \
    dub build \
        --config=barebones \
        --cache=local \
        --override-config=facetrack-d/web-adaptors \
            2>&1 ; \
    } 2>> /opt/out/session-stats
popd
popd

# Install inochi-creator
rsync -r /opt/src/inochi-creator/out/ /opt/out/inochi-creator/
echo "" >> /opt/out/creator-stats 
echo "Result files" >> /opt/out/creator-stats 
echo "" >> /opt/out/creator-stats 
du -sh /opt/out/inochi-creator/* >> /opt/out/creator-stats 

# Install inochi-session
rsync -r /opt/src/inochi-session/out/ /opt/out/inochi-session/
echo "" >> /opt/out/session-stats 
echo "Result files" >> /opt/out/session-stats 
echo "" >> /opt/out/session-stats 
du -sh /opt/out/inochi-session/* >> /opt/out/session-stats

# ---
dub list > /opt/out/version_dump