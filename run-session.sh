#!/bin/bash

LD_LIBRARY_PATH=$(pwd)/build_out/inochi-session:${LD_LIBRARY_PATH} \
    ./build_out/inochi-session/inochi-session $1
