// 웹 폴백 — 네이티브 Zig 엔진이 없으므로 동일 연산을 JS 로 제공.
import {
  buildOffsets as buildOffsetsRef,
  visibleChecksum as visibleChecksumRef,
} from './reference';

export function sumInt32(arr: Int32Array): number {
  let s = 0;
  for (let i = 0; i < arr.length; i++) s += arr[i]!;
  return s;
}

export function engineInfo(): string {
  return 'ZeroList JS fallback (web)';
}

export function nativeLog(message: string): void {
  console.log('[ZeroList-PoC]', message);
}

export function buildOffsetsZig(
  heights: Float32Array,
  out: Float64Array
): void {
  buildOffsetsRef(heights, out);
}

export function visibleChecksumZig(
  offsets: Float64Array,
  n: number,
  viewport: number,
  scrolls: Float64Array
): number {
  return visibleChecksumRef(offsets, n, viewport, scrolls);
}
