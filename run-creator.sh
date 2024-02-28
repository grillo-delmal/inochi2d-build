#!/bin/bash

LD_LIBRARY_PATH=$(pwd)/build_out/inochi-creator:${LD_LIBRARY_PATH} \
    ./build_out/inochi-creator/inochi-creator "$@"
