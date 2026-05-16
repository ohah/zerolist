#!/usr/bin/env bash
# zlbridge(JNI→Zig) 를 RN 네이티브 빌드와 분리해 NDK 로 단독 빌드.
# 인자: 1=cmake bin 디렉토리 2=ndk 디렉토리 3=android-platform(min sdk)
#       4=cpp 소스 디렉토리 5=출력 jniLibs/arm64-v8a 디렉토리
set -euo pipefail
CMAKE_BIN="$1"; NDK="$2"; PLATFORM="$3"; SRC="$4"; OUT="$5"
CONF="$(dirname "$OUT")/cmake-arm64-v8a"
"$CMAKE_BIN/cmake" -S "$SRC" -B "$CONF" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$NDK/build/cmake/android.toolchain.cmake" \
  -DCMAKE_MAKE_PROGRAM="$CMAKE_BIN/ninja" \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM="android-$PLATFORM" \
  -DCMAKE_LIBRARY_OUTPUT_DIRECTORY="$OUT"
"$CMAKE_BIN/cmake" --build "$CONF"
