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
  # Newer libtool can skip misaligned archive members. Extract with Zig's
  # archiver first, then give libtool the Mach-O objects rather than the archive.
  mkdir -p "$APPLE_ARCHIVES/$SLICE"
  SOURCE="$PWD/$LIB"
  (cd "$APPLE_ARCHIVES/$SLICE" && zig ar x "$SOURCE")
  chmod u+r "$APPLE_ARCHIVES/$SLICE"/*.o
  xcrun libtool -static -o "$APPLE_ARCHIVES/$SLICE.a" "$APPLE_ARCHIVES/$SLICE"/*.o
  mv "$APPLE_ARCHIVES/$SLICE.a" "$LIB"
  xcrun nm -gU "$LIB" | awk '$NF == "_zl_build_offsets" { found = 1 } END { exit !found }'
done

echo "✔ $OUT"
