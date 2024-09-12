#!/usr/bin/bash

set -e

DEBUG=
PREBUILD_IMGUI=1
PREDOWNLOAD_LIBS=1
CREATOR=1
SESSION=1
LOAD_CACHE=
SAVE_CACHE=1

podman build -t inochi-build .

mkdir -p $(pwd)/build_out
mkdir -p $(pwd)/cache

podman unshare chown $UID:$UID -R $(pwd)/build_out
podman unshare chown $UID:$UID -R $(pwd)/cache

podman run -ti --rm \
    -v $(pwd)/build_out:/opt/out/:Z \
    -v $(pwd)/cache:/opt/cache/:Z \
    -v $(pwd)/.git:/opt/.git/:ro,Z \
    -v $(pwd)/src/inochi-creator:/opt/orig/inochi-creator/:ro,Z \
    -v $(pwd)/src/inochi-session:/opt/orig/inochi-session/:ro,Z \
    -v $(pwd)/src/inochi2d:/opt/orig-deps/inochi2d/:ro,Z \
    -v $(pwd)/src/inui:/opt/orig-deps/inui/:ro,Z \
    -v $(pwd)/src/bindbc-spout2:/opt/orig-deps/bindbc-spout2/:ro,Z \
    -v $(pwd)/src/dportals:/opt/orig-deps/dportals/:ro,Z \
    -v $(pwd)/src/facetrack-d:/opt/orig-deps/facetrack-d/:ro,Z \
    -v $(pwd)/src/fghj:/opt/orig-deps/fghj/:ro,Z \
    -v $(pwd)/src/i18n:/opt/orig-deps/i18n/:ro,Z \
    -v $(pwd)/src/i2d-imgui:/opt/orig-deps/i2d-imgui/:ro,Z \
    -v $(pwd)/src/i2d-opengl:/opt/orig-deps/i2d-opengl/:ro,Z \
    -v $(pwd)/src/inmath:/opt/orig-deps/inmath/:ro,Z \
    -v $(pwd)/src/kra-d:/opt/orig-deps/kra-d/:ro,Z \
    -v $(pwd)/src/numem:/opt/orig-deps/numem/:ro,Z \
    -v $(pwd)/src/psd-d:/opt/orig-deps/psd-d/:ro,Z \
    -v $(pwd)/src/vmc-d:/opt/orig-deps/vmc-d/:ro,Z \
    -v $(pwd)/patches:/opt/patches/:ro,Z \
    -v $(pwd)/files:/opt/files/:ro,Z \
    -v $(pwd)/scripts:/opt/scripts/:ro,Z \
    -w /opt/scripts/ \
    -e PREBUILD_IMGUI=${PREBUILD_IMGUI} \
    -e PREDOWNLOAD_LIBS=${PREDOWNLOAD_LIBS} \
    -e CREATOR=${CREATOR} \
    -e SESSION=${SESSION} \
    -e DEBUG=${DEBUG} \
    -e LOAD_CACHE=${LOAD_CACHE} \
    -e SAVE_CACHE=${SAVE_CACHE} \
    localhost/inochi-build:latest \
    bash build.sh

podman unshare chown 0:0 -R $(pwd)/build_out
podman unshare chown 0:0 -R $(pwd)/cache
