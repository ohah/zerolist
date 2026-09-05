#!/usr/bin/env bash
# Zig 엔진을 빌드해 iOS 기기/시뮬레이터를 한 번에 담는
# XCFramework 로 묶는다. → ios/Zerolist.xcframework
set -euo pipefail
cd "$(dirname "$0")"

echo "▶ zig build (ios + android)"
zig build

# Zig's archive layout can leave Mach-O members only 2-byte aligned.
# Apple's linker requires 8-byte alignment; repack with the platform archiver.
APPLE_ARCHIVES="$(mktemp -d)"
trap 'rm -rf "$APPLE_ARCHIVES"' EXIT
for TARGET in ios-arm64 ios-arm64-simulator; do
  mkdir -p "$APPLE_ARCHIVES/$TARGET"
  xcrun libtool -static -o "$APPLE_ARCHIVES/$TARGET/libzerolist_engine.a" \
    "zig-out/$TARGET/libzerolist_engine.a"
done

OUT="../ios/Zerolist.xcframework"
rm -rf "$OUT"

echo "▶ create-xcframework"
xcodebuild -create-xcframework \
  -library "$APPLE_ARCHIVES/ios-arm64/libzerolist_engine.a" \
  -library "$APPLE_ARCHIVES/ios-arm64-simulator/libzerolist_engine.a" \
  -output "$OUT"

echo "✔ $OUT"
