// 가상화 연산의 정식 JS 레퍼런스 구현.
// 벤치마크(네이티브 Zig vs JS)의 공정성은 "JS 기준 구현"이
// Zig 와 동일 알고리즘이라는 데 달려 있으므로, 웹 폴백과 예제
// 벤치가 같은 단일 소스를 쓰도록 여기로 모은다.

/** 가변 높이(f32) → 누적 오프셋. out 은 길이 n+1, out[0]=0.
 * 누적값은 대용량에서 f32 정수 정확 한계를 넘으므로 Float64Array. */
export function buildOffsets(heights: Float32Array, out: Float64Array): void {
  out[0] = 0;
  let acc = 0;
  for (let i = 0; i < heights.length; i++) {
    acc += heights[i]!;
    out[i + 1] = acc;
  }
}

/** offsets(오름차순) 에서 offsets[idx] <= value 인 최대 idx (∈ [0,n]). */
export function upperIndex(
  offsets: Float64Array,
  n: number,
  value: number
): number {
  let lo = 0;
  let hi = n;
  while (lo < hi) {
    const mid = lo + ((hi - lo + 1) >> 1);
    if (offsets[mid]! <= value) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

/**
 * 한 scrollY 의 가시 index 범위 [first, lastExclusive).
 * Zig `zl_visible_range`(engine.zig) 와 비트수준 동일해야 하는 계약을
 * 코드 한 곳에 고정한다. 오버스캔/초기렌더 같은 정책은 포함하지 않는
 * "순수 가시 범위" — 그 위 정책은 virtualizer.computeWindow 가 담당.
 */
export function visibleRange(
  offsets: Float64Array,
  n: number,
  scrollY: number,
  viewport: number
): [number, number] {
  const first = upperIndex(offsets, n, scrollY);
  const last = upperIndex(offsets, n, scrollY + viewport);
  return [first, last < n ? last + 1 : n];
}

/** k 개 scrollOffset 의 [first,last] 가시범위 인덱스 합(체크섬). */
export function visibleChecksum(
  offsets: Float64Array,
  n: number,
  viewport: number,
  scrolls: Float64Array
): number {
  let sum = 0;
  for (let q = 0; q < scrolls.length; q++) {
    const s = scrolls[q]!;
    sum += upperIndex(offsets, n, s);
    sum += upperIndex(offsets, n, s + viewport);
  }
  return sum;
}
