import Zerolist from './NativeZerolist';

/** Int32Array 를 zero-copy 로 Zig 엔진(SIMD)에 넘겨 합산. */
export function sumInt32(arr: Int32Array): number {
  return Zerolist.sumInt32(arr);
}

export function engineInfo(): string {
  return Zerolist.engineInfo();
}

export function nativeLog(message: string): void {
  Zerolist.nativeLog(message);
}

/** 가변 높이(f32) → 누적 오프셋(f64, 길이 n+1). zero-copy.
 * 누적값이 대용량에서 f32 정수 정확 한계를 넘으므로 out 은 Float64Array. */
export function buildOffsetsZig(
  heights: Float32Array,
  out: Float64Array
): void {
  Zerolist.buildOffsets(heights, heights.length, out);
}

/** Phase A: k 개 scrollOffset(f64) 의 가시범위 인덱스 합(체크섬). zero-copy. */
export function visibleChecksumZig(
  offsets: Float64Array,
  n: number,
  viewport: number,
  scrolls: Float64Array
): number {
  return Zerolist.visibleChecksum(
    offsets,
    n,
    viewport,
    scrolls,
    scrolls.length
  );
}
