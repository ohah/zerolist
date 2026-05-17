// ZeroList 가상화 엔진 — 순수 함수(React/RN 비의존)라 단위 테스트가
// 100% 가능한 지점. FlatList 의 윈도잉/레이아웃/가시성 동작을 동일
// 시맨틱으로 재현한다. 오프셋 누적·가시범위는 라이브러리의 단일 JS
// 레퍼런스(reference.ts)를 재사용 — 네이티브 Zig 경로와 같은 알고리즘.
import {
  buildOffsets as buildOffsetsRef,
  upperIndex,
  visibleRange,
} from './reference';

export type ItemLayout = { length: number; offset: number; index: number };

/** FlatList 의 keyExtractor 기본값과 동일: item.key → item.id → String(index). */
export function defaultKeyExtractor(item: unknown, index: number): string {
  if (item != null && typeof item === 'object') {
    const o = item as { key?: unknown; id?: unknown };
    if (o.key != null) return String(o.key);
    if (o.id != null) return String(o.id);
  }
  return String(index);
}

/**
 * ③ 링버퍼 리사이클러의 슬롯→데이터인덱스 매핑(미래 구현용 계약 spec).
 * 윈도우 [windowStart, windowStart+pool) 를 pool 개 고정 슬롯에
 * 분배하되 windowStart 가 1 변할 때 **정확히 1 슬롯만** 바뀌게 한다.
 *
 * 검증된 사실(#24, strategy 메모리): 이 ring 으로 JS renderItem 을
 * 112→9 로 줄일 수 있음(thesis 지지). 그러나 **네이티브와 JS 가 각자
 * windowStart 로 ring 을 파생하는 "순수함수 단축"은 desync 시 wrapped
 * offset 으로 화면이 영구 깨짐**(에뮬 스크린샷 확인, 폐기). 올바른
 * 구현은 네이티브가 slot↔dataIndex 의 단일 권위가 되어 per-slot
 * binding 을 이벤트로 내려주고 JS 는 그것을 적용만 해야 한다
 * (start-only/순수ring 둘 다 불충분). 이 함수는 그 알고리즘의
 * 단일 소스이자 테스트된 계약 — 통합은 아직 안 됨(미화 금지).
 */
export function ringIndex(
  slot: number,
  windowStart: number,
  pool: number
): number {
  return windowStart + ((((slot - windowStart) % pool) + pool) % pool);
}

/** numColumns 적용: data 를 길이 cols 의 행으로 그룹화한 인덱스 행렬. */
export function groupIntoRows(count: number, numColumns: number): number[][] {
  const cols = Math.max(1, Math.floor(numColumns));
  const rows: number[][] = [];
  for (let i = 0; i < count; i += cols) {
    const row: number[] = [];
    for (let c = 0; c < cols && i + c < count; c++) row.push(i + c);
    rows.push(row);
  }
  return rows;
}

/**
 * 행별 길이(주축 픽셀) → 누적 오프셋 Float64Array(길이 n+1, [0]=0).
 * 우선순위는 FlatList 와 동일: getItemLayout > 측정값 > 추정치.
 */
export function buildOffsets(
  count: number,
  opts: {
    getItemLength?: (index: number) => number | undefined;
    measured?: Map<number, number>;
    estimatedItemSize: number;
  }
): Float64Array {
  const heights = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    const exact = opts.getItemLength?.(i);
    if (exact != null && exact >= 0) {
      heights[i] = exact;
      continue;
    }
    const m = opts.measured?.get(i);
    heights[i] = m != null && m >= 0 ? m : opts.estimatedItemSize;
  }
  const out = new Float64Array(count + 1);
  buildOffsetsRef(heights, out);
  return out;
}

/** index 의 레이아웃(offset/length). 범위 밖이면 null. */
export function itemLayout(
  offsets: Float64Array,
  count: number,
  index: number
): ItemLayout | null {
  if (index < 0 || index >= count) return null;
  const offset = offsets[index]!;
  return { index, offset, length: offsets[index + 1]! - offset };
}

export type Window = { first: number; last: number };

export type WindowOptions = {
  scrollOffset: number;
  viewportLength: number;
  /** FlatList 와 동일하게 "뷰포트 배수"(기본 21). */
  windowSize: number;
  /** 첫 스크롤 전 최소 렌더 행 수. */
  initialNumToRender: number;
};

/**
 * 렌더할 행 윈도우 [first, last) 계산.
 * - 순수 가시구간은 reference.visibleRange(= Zig 와 동일 계약).
 * - windowSize: 가시 구간 위아래로 ((windowSize-1)/2) 뷰포트씩 픽셀로
 *   확장(오버스캔). 이 정책 레이어가 reference 와의 차이.
 * - 첫 스크롤 전(scrollOffset<=0)에는 최소 initialNumToRender 행 보장.
 */
export function computeWindow(
  offsets: Float64Array,
  count: number,
  opts: WindowOptions
): Window {
  if (count === 0) return { first: 0, last: 0 };
  const s = Math.max(0, opts.scrollOffset);
  const vp = Math.max(1, opts.viewportLength);
  const overscanPx = ((Math.max(1, opts.windowSize) - 1) / 2) * vp;
  let first = upperIndex(offsets, count, s - overscanPx);
  let last = upperIndex(offsets, count, s + vp + overscanPx) + 1;
  if (first < 0) first = 0;
  if (last > count) last = count;
  if (s <= 0) last = Math.max(last, Math.min(count, opts.initialNumToRender));
  if (last < first) last = first;
  return { first, last };
}

export type ViewToken = {
  index: number;
  key: string;
  isViewable: boolean;
  item: unknown;
};

export type ViewabilityConfig = {
  /** 항목 자신의 몇 % 가 보이면 viewable (0~100). */
  itemVisiblePercentThreshold?: number;
  /** 뷰포트의 몇 % 를 덮으면 viewable (0~100). */
  viewAreaCoveragePercentThreshold?: number;
};

/**
 * 한 항목이 viewable 인지 — FlatList 의 두 임계 모드와 동일 판정.
 * 둘 다 주어지면 viewAreaCoverage 가 우선(FlatList 와 동일, 상호배타).
 * 임계 미지정 시 FlatList 기본: 1px 라도 보이면 viewable.
 */
export function isViewable(
  itemOffset: number,
  itemLength: number,
  scrollOffset: number,
  viewportLength: number,
  config: ViewabilityConfig
): boolean {
  if (itemLength <= 0) return false;
  const top = Math.max(itemOffset, scrollOffset);
  const bottom = Math.min(
    itemOffset + itemLength,
    scrollOffset + viewportLength
  );
  const visiblePx = Math.max(0, bottom - top);
  const { viewAreaCoveragePercentThreshold, itemVisiblePercentThreshold } =
    config;
  if (viewAreaCoveragePercentThreshold != null)
    return (
      (visiblePx / Math.max(1, viewportLength)) * 100 >=
      viewAreaCoveragePercentThreshold
    );
  if (itemVisiblePercentThreshold != null)
    return (visiblePx / itemLength) * 100 >= itemVisiblePercentThreshold;
  return visiblePx > 0;
}

export type ViewableOptions = {
  scrollOffset: number;
  viewportLength: number;
  config: ViewabilityConfig;
  keyOf: (index: number) => string;
  itemOf: (index: number) => unknown;
};

/** 현재 뷰포트의 viewable 토큰 목록(index 오름차순). */
export function computeViewableItems(
  offsets: Float64Array,
  count: number,
  opts: ViewableOptions
): ViewToken[] {
  const tokens: ViewToken[] = [];
  if (count === 0) return tokens;
  const { scrollOffset, viewportLength, config, keyOf, itemOf } = opts;
  const viewportBottom = scrollOffset + viewportLength;
  let i = Math.max(0, upperIndex(offsets, count, scrollOffset));
  for (; i < count; i++) {
    const l = itemLayout(offsets, count, i)!;
    if (l.offset >= viewportBottom) break;
    if (isViewable(l.offset, l.length, scrollOffset, viewportLength, config))
      tokens.push({
        index: i,
        key: keyOf(i),
        isViewable: true,
        item: itemOf(i),
      });
  }
  return tokens;
}

/**
 * onViewableItemsChanged 페이로드 계산. 이전(키→토큰) 과 현재 viewable
 * 을 비교해 바뀐 게 없으면 null(콜백 미발화) — FlatList 와 동일.
 * 흔한 no-op 프레임은 Set/배열 할당 전에 early-out.
 * 이탈 항목은 FlatList 처럼 직전 토큰(실제 index/item)을 isViewable:false
 * 로 돌려준다(센티넬 없음).
 */
export function diffViewable(
  prev: ReadonlyMap<string, ViewToken>,
  current: ViewToken[]
): { viewableItems: ViewToken[]; changed: ViewToken[] } | null {
  let allKnown = current.length === prev.size;
  if (allKnown)
    for (const t of current)
      if (!prev.has(t.key)) {
        allKnown = false;
        break;
      }
  if (allKnown) return null; // 같은 키 집합 → 변화 없음

  const curKeys = new Set<string>();
  const changed: ViewToken[] = [];
  for (const t of current) {
    curKeys.add(t.key);
    if (!prev.has(t.key)) changed.push(t);
  }
  for (const [k, token] of prev)
    if (!curKeys.has(k)) changed.push({ ...token, isViewable: false });
  if (changed.length === 0) return null;
  return { viewableItems: current, changed };
}

/**
 * onEndReached 발화 여부 — FlatList 동일: 콘텐츠 끝까지 남은 거리가
 * onEndReachedThreshold * viewportLength 이하이면 true.
 * (재무장은 호출부에서 거리 회복 시 처리)
 */
export function isEndReached(
  scrollOffset: number,
  viewportLength: number,
  contentLength: number,
  threshold: number
): boolean {
  if (contentLength <= 0) return false;
  const distanceToEnd = contentLength - (scrollOffset + viewportLength);
  return distanceToEnd <= threshold * viewportLength;
}

// re-export: JS·Zig 가 공유하는 순수 가시범위 계약의 단일 소스.
export { visibleRange };
