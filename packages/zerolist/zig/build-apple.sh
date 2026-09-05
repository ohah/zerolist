#!/usr/bin/env bash
# Build both Apple slices, then package aligned archives for Apple's linker.
set -euo pipefail
cd "$(dirname "$0")"

zig build
OUT="../ios/Zerolist.xcframework"
rm -rf "$OUT"

# Let Xcode read platform metadata from the original Zig archives first.
xcodebuild -create-xcframework \
  -library zig-out/ios-arm64/libzerolist_engine.a \
  -library zig-out/ios-arm64-simulator/libzerolist_engine.a \
  -output "$OUT"

# Apple's linker requires Mach-O archive members to be 8-byte aligned.
# Repack the packaged copies; keep Xcode's platform metadata unchanged.
APPLE_ARCHIVES="$(mktemp -d)"
trap 'rm -rf "$APPLE_ARCHIVES"' EXIT
for SLICE in ios-arm64 ios-arm64-simulator; do
  LIB="$OUT/$SLICE/libzerolist_engine.a"
  xcrun libtool -static -o "$APPLE_ARCHIVES/$SLICE.a" "$LIB"
  mv "$APPLE_ARCHIVES/$SLICE.a" "$LIB"
done

echo "✔ $OUT"
