#!/usr/bin/env bash
# Zig 엔진을 빌드해 iOS 기기/시뮬레이터를 한 번에 담는
# XCFramework 로 묶는다. → ios/Zerolist.xcframework
set -euo pipefail
cd "$(dirname "$0")"

echo "▶ zig build (ios + android)"
zig build

OUT="../ios/Zerolist.xcframework"
rm -rf "$OUT"

echo "▶ create-xcframework"
xcodebuild -create-xcframework \
  -library zig-out/ios-arm64/libzerolist_engine.a \
  -library zig-out/ios-arm64-simulator/libzerolist_engine.a \
  -output "$OUT"

echo "✔ $OUT"
