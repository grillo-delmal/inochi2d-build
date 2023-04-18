#!/bin/bash

if [[ -z ${DEBUG} ]]; then
    LD_LIBRARY_PATH=$(pwd)/build_out/inochi-session:${LD_LIBRARY_PATH} \
        ./build_out/inochi-session/inochi-session $1
else
    LD_LIBRARY_PATH=$(pwd)/build_out/inochi-session:${LD_LIBRARY_PATH} \
        gdb \
        --ex 'handle SIGUSR1 noprint nostop' \
        --ex 'handle SIGUSR2 noprint nostop' \
        --ex 'r' \
        --args \
        ./build_out/inochi-session/inochi-session $1
fi