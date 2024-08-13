#!/usr/bin/bash

set -e

source /opt/scripts/semver.sh
source /opt/scripts/cimgui.sh

# Clean out folder
find /opt/out/ -mindepth 1 -maxdepth 1 -exec rm -r -- {} +

echo "======== Loading sources ========"

cd /opt
mkdir -p src
mkdir -p deps

rsync --info=progress2 -azh /opt/orig/inochi-creator/ /opt/src/inochi-creator/
rsync --info=progress2 -azh /opt/orig/inochi-session/ /opt/src/inochi-session/

if [ -d ./orig-deps ]; then
    pushd orig-deps
    if [ ! -z "$(ls -A */ 2> /dev/null)" ]; then
        for d in */ ; do
            if [ -d /opt/orig-deps/${d} ]; then
                rsync --info=progress2 -azh /opt/orig-deps/${d} /opt/deps/${d}
                ln -s /opt/deps/${d} /opt/src/${d::-1}

                pushd /opt/deps/${d}
                if [ -f dub.sdl ]; then
                    dub convert -f json
                fi

                DEP_SEMVER=$(semver /opt/deps/${d})

                mv dub.json dub.json.base
                jq ". += {\"version\": \"${DEP_SEMVER}\"}" dub.json.base > dub.json.ver
                jq 'walk(if type == "object" then with_entries(select(.key | test("preBuildCommands*") | not)) else . end)' dub.json.ver > dub.json
                if [ $d == 'i2d-imgui/' ]; then
                    check_local_imgui
                fi
                popd

                dub add-local /opt/deps/${d}
                rm /opt/src/${d::-1}
            fi
        done
    fi
    popd
fi

echo "======== Applying patches ========"

if [ -d ./patches ]; then
    pushd patches
    if [ ! -z "$(ls -A */ 2> /dev/null)" ]; then
        for d in */ ; do
            if [ -d /opt/src/${d} ]; then
                for p in ${d}*.patch; do
                    echo "patch /opt/patches/$p"
                    git -C /opt/src/${d} apply /opt/patches/$p
                done
            fi
            if [ -d /opt/deps/${d} ]; then
                for p in ${d}*.patch; do
                    echo "patch /opt/patches/$p"
                    git -C /opt/deps/${d} apply /opt/patches/$p
                done
            fi
        done
    fi
    popd
fi

echo "======== Replacing files ========"
if [ -d ./files ]; then
    pushd files
    if [ ! -z "$(ls -A */ 2> /dev/null)" ]; then
        for d in */ ; do
            pushd $d
            if [ -d /opt/src/${d} ]; then
                for p in $(find . -type f); do
                    if [ -f "/opt/files/$d$p" ]; then
                        echo "Adding $p in /opt/files/$d to /opt/src/${d::-1}/$(dirname $p)"
                        pushd /opt/src/${d::-1}/
                        mkdir -p "$(dirname $p)"
                        cp --force "/opt/files/$d$p" "$(dirname $p)"
                        popd

                    fi
                done
            fi
            if [ -d /opt/deps/${d} ]; then
                for p in $(find . -type f); do
                    if [ -f "/opt/files/$d$p" ]; then
                        echo "Adding $p in /opt/files/$d to /opt/deps/${d::-1}/$(dirname $p)"
                        pushd /opt/deps/${d::-1}/
                        mkdir -p "$(dirname $p)"
                        cp --force "/opt/files/$d$p" "$(dirname $p)"
                        popd

                    fi
                done
            fi
            popd
        done
    fi
    popd
fi

if [[ ! -z ${LOAD_CACHE} ]]; then
    echo "======== Loading cache ========"

    mkdir -p /opt/cache/.dub/
    rsync --info=progress2 -azh /opt/cache/.dub/ ~/.dub/
fi

echo "======== Loading dub dependencies ========"

if [[ ! -z ${DEBUG} ]]; then
    export DFLAGS='-g --d-debug'
fi
export DC='/usr/bin/ldc2'

if [[ ! -z ${CREATOR} ]]; then
    # Build inochi-creator
    pushd src
    pushd inochi-creator

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
    popd
    popd
fi

if [[ ! -z ${SESSION} ]]; then
    # Build inochi-session
    pushd src
    pushd inochi-session

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
    popd
    popd
fi

echo "======== Removing preBuildCommands ========"

pushd ~/.dub/packages/
for d in */ ; do
    di=${d::-1}
    if [ -d ~/.dub/packages/${di} ]; then
        pushd ~/.dub/packages/${di}
        if [ -d */ ]; then
            pushd */

            if [ -d ${di}*/ ]; then
                pushd ${di}*/
                echo "Processing ${di}"
                if [ -f dub.sdl ]; then
                    echo "  Transforming ${di} sdl -> json"
                    dub convert -f json
                fi

                rm -f dub.json.bak*
                mv dub.json dub.json.bak
                jq 'walk(if type == "object" then with_entries(select(.key | test("preBuildCommands*") | not)) else . end)' dub.json.bak > dub.json
                popd
            fi
            popd
        fi
        popd
    fi
done
popd

echo "======== Applying dub lib patches ========"

if [ -d ./patches ]; then
    pushd patches
    if [ ! -z "$(ls -A */ 2> /dev/null)" ]; then
        for d in */ ; do
            if [ -d ~/.dub/packages/${d::-1} ]; then
                for p in ${d}*.patch; do
                    echo "patch /opt/patches/$p"
                    pushd ~/.dub/packages/${d::-1}/*/${d::-1}
                    patch -p1 < /opt/patches/$p
                    popd
                done
            fi
        done
    fi
    popd
fi

echo "======== Replacing dub lib files ========"
if [ -d ./files ]; then
    pushd files
    if [ ! -z "$(ls -A */ 2> /dev/null)" ]; then
        for d in */ ; do
            pushd $d
            if [ -d ~/.dub/packages/${d::-1} ]; then
                for p in $(find . -type f); do
                    if [ -f "/opt/files/$d$p" ]; then
                        echo "Adding $p in /opt/files/$d to ~/.dub/packages/${d::-1}/*/${d::-1}/$(dirname $p)"
                        pushd ~/.dub/packages/${d::-1}/*/${d::-1}/
                        mkdir -p "$(dirname $p)"
                        cp --force "/opt/files/$d$p" "$(dirname $p)"
                        popd
                    fi
                done
            fi
            popd
        done
    fi
    popd
fi

check_dub_i2d_imgui

prepare_i2d_imgui

if [[ ! -z ${CREATOR} ]]; then
    echo "======== Starting creator ========"

    # Build inochi-creator
    pushd src
    pushd inochi-creator

cat > ./source/creator/ver.d <<EOF
module creator.ver;

enum INC_VERSION = "$(semver /opt/src/inochi-creator/)";
EOF

    # Remove branding assets
    rm -rf res/Inochi-Creator.iconset/
    find res/ui/ -type f -not -name "grid.png" -delete
    rm res/icon.png
    rm res/logo.png
    rm res/logo_256.png
    rm res/shaders/ada.frag
    rm res/shaders/ada.vert
    cp res/ui/grid.png res/ui/banner.png

    # Replace files
    rm source/creator/config.d
    rsync -azh /opt/files/inochi-creator/ $(pwd)

    # Gen tl files
    chmod +x ./gentl.sh
    ./gentl.sh

    mkdir -p out

    echo "======== Building creator ========"
    echo "Build time" >> /opt/out/creator-stats 
    if [[ -z ${LOAD_CACHE} ]]; then
    { time \
        dub build \
            --config=barebones \
            --cache=user \
            --non-interactive \
                2>&1 ; \
        } 2>> /opt/out/creator-stats 
    else
        { time \
            dub build \
                --config=barebones \
                --cache=user \
                --non-interactive \
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

cat > ./source/session/ver.d <<EOF
module session.ver;

enum INS_VERSION = "$(semver /opt/src/inochi-session/)";
EOF
    mkdir -p out

    echo "======== Building session ========"
    echo "Build time" >> /opt/out/session-stats 
    if [[ -z ${LOAD_CACHE} ]]; then
        { time \
            dub build \
                --config=barebones \
                --cache=user \
                --non-interactive \
                --override-config=facetrack-d/web-adaptors \
                    2>&1 ; \
            } 2>> /opt/out/session-stats
    else
        { time \
            dub build \
                --config=barebones \
                --cache=user \
                --non-interactive \
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

    find /opt/cache/ -mindepth 1 -maxdepth 1 -exec rm -r -- {} +
    mkdir -p /opt/cache/.dub/
    rsync --info=progress2 -azh ~/.dub/ /opt/cache/.dub/

fi

