#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="$(cd -- "$project_dir/../.." && pwd)"
source /opt/ros/noetic/setup.bash
mkdir -p "$workspace_dir/.toolchain/include"
if [ ! -e "$workspace_dir/.toolchain/include/google" ]; then
  ln -s /usr/include/google "$workspace_dir/.toolchain/include/google"
fi
cd "$workspace_dir"
catkin_make -j2 -l2 \
  -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3 \
  -DCMAKE_IGNORE_PREFIX_PATH=/usr/local \
  -DCMAKE_CXX_FLAGS="-I$workspace_dir/.toolchain/include -fmax-errors=5" \
  -DProtobuf_INCLUDE_DIR=/usr/include \
  -DProtobuf_LIBRARY_RELEASE=/usr/lib/x86_64-linux-gnu/libprotobuf.so \
  -DProtobuf_LIBRARY_DEBUG=/usr/lib/x86_64-linux-gnu/libprotobuf.so \
  -DProtobuf_LITE_LIBRARY_RELEASE=/usr/lib/x86_64-linux-gnu/libprotobuf-lite.so \
  -DProtobuf_LITE_LIBRARY_DEBUG=/usr/lib/x86_64-linux-gnu/libprotobuf-lite.so \
  -DProtobuf_PROTOC_LIBRARY_RELEASE=/usr/lib/x86_64-linux-gnu/libprotoc.so \
  -DProtobuf_PROTOC_LIBRARY_DEBUG=/usr/lib/x86_64-linux-gnu/libprotoc.so \
  -DProtobuf_PROTOC_EXECUTABLE=/home/zxr2/cerlab_ws/.toolchain/protobuf-3.6.1/usr/bin/protoc \
  "$@"
