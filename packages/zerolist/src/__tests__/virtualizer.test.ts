import { describe, it, expect } from '@jest/globals';
import {
  defaultKeyExtractor,
  groupIntoRows,
  buildOffsets,
  itemLayout,
  computeWindow,
  isViewable,
  computeViewableItems,
  diffViewable,
  isEndReached,
  visibleRange,
  ringIndex,
  type ViewToken,
} from '../virtualizer';

const toMap = (tokens: ViewToken[]) =>
  new Map(tokens.map((t) => [t.key, t] as const));
const mk = (i: number): ViewToken => ({
  index: i,
  key: `k${i}`,
  isViewable: true,
  item: { v: i },
});

describe('defaultKeyExtractor (FlatList 기본 동작 동일)', () => {
  it('item.key 우선', () => {
    expect(defaultKeyExtractor({ key: 'k1', id: 9 }, 3)).toBe('k1');
  });
  it('key 없으면 id', () => {
    expect(defaultKeyExtractor({ id: 42 }, 3)).toBe('42');
  });
  it('key/id 없으면 index 문자열', () => {
    expect(defaultKeyExtractor({ name: 'x' }, 7)).toBe('7');
  });
  it('원시값/Null 은 index', () => {
    expect(defaultKeyExtractor('hello', 2)).toBe('2');
    expect(defaultKeyExtractor(null, 5)).toBe('5');
    expect(defaultKeyExtractor(undefined, 0)).toBe('0');
  });
  it('숫자 0 / falsy id 도 유효 키', () => {
    expect(defaultKeyExtractor({ id: 0 }, 4)).toBe('0');
  });
});

describe('groupIntoRows (numColumns)', () => {
  it('정확히 나눠떨어짐', () => {
    expect(groupIntoRows(6, 3)).toEqual([
      [0, 1, 2],
      [3, 4, 5],
    ]);
  });
  it('마지막 행 부분 채움', () => {
    expect(groupIntoRows(5, 2)).toEqual([[0, 1], [2, 3], [4]]);
  });
  it('numColumns=1 은 행마다 1개', () => {
    expect(groupIntoRows(3, 1)).toEqual([[0], [1], [2]]);
  });
  it('count=0 → 빈 배열', () => {
    expect(groupIntoRows(0, 3)).toEqual([]);
  });
  it('numColumns<1 은 1로 클램프', () => {
    expect(groupIntoRows(2, 0)).toEqual([[0], [1]]);
  });
});

describe('buildOffsets (레이아웃 소스 우선순위 = FlatList)', () => {
  it('estimatedItemSize 균일', () => {
    const off = buildOffsets(4, { estimatedItemSize: 50 });
    expect(Array.from(off)).toEqual([0, 50, 100, 150, 200]);
  });
  it('getItemLength(정확) 가 추정치보다 우선', () => {
    const off = buildOffsets(3, {
      estimatedItemSize: 50,
      getItemLength: (i) => (i === 1 ? 100 : undefined),
    });
    expect(Array.from(off)).toEqual([0, 50, 150, 200]);
  });
  it('측정값이 추정치보다 우선(정확값 없을 때)', () => {
    const off = buildOffsets(3, {
      estimatedItemSize: 50,
      measured: new Map([[0, 30]]),
    });
    expect(Array.from(off)).toEqual([0, 30, 80, 130]);
  });
  it('정확값 > 측정값 > 추정치 순', () => {
    const off = buildOffsets(3, {
      estimatedItemSize: 50,
      getItemLength: (i) => (i === 0 ? 10 : undefined),
      measured: new Map([
        [0, 999],
        [1, 20],
      ]),
    });
    expect(Array.from(off)).toEqual([0, 10, 30, 80]);
  });
  it('count=0 → 길이1, [0]', () => {
    const off = buildOffsets(0, { estimatedItemSize: 50 });
    expect(Array.from(off)).toEqual([0]);
  });
  it('대용량(N=100k) 누적 정밀도 — f64 라 마지막=N*size 정확', () => {
    const N = 100_000;
    const off = buildOffsets(N, { estimatedItemSize: 37 });
    expect(off[N]).toBe(N * 37);
  });
});

describe('itemLayout', () => {
  const off = buildOffsets(3, { estimatedItemSize: 40 });
  it('정상 인덱스', () => {
    expect(itemLayout(off, 3, 1)).toEqual({ index: 1, offset: 40, length: 40 });
  });
  it('범위 밖 → null', () => {
    expect(itemLayout(off, 3, -1)).toBeNull();
    expect(itemLayout(off, 3, 3)).toBeNull();
  });
});

describe('visibleRange (JS·Zig 공유 계약 — 오버스캔 없음)', () => {
  const off = buildOffsets(1000, { estimatedItemSize: 100 });
  it('순수 가시구간 [first, lastExclusive)', () => {
    // scroll 5000, vp 500 → offsets[50]=5000..[55]=5500
    expect(visibleRange(off, 1000, 5000, 500)).toEqual([50, 56]);
  });
  it('상단(0) 경계', () => {
    expect(visibleRange(off, 1000, 0, 500)).toEqual([0, 6]);
  });
  it('끝에서 last 는 n 으로 클램프(+1 안 함)', () => {
    const [, last] = visibleRange(off, 1000, 100_000, 500);
    expect(last).toBe(1000);
  });
  it('computeWindow(windowSize=1, init=0) 의 base 와 일치', () => {
    const w = computeWindow(off, 1000, {
      scrollOffset: 5000,
      viewportLength: 500,
      windowSize: 1,
      initialNumToRender: 0,
    });
    expect([w.first, w.last]).toEqual(visibleRange(off, 1000, 5000, 500));
  });
});

describe('computeWindow (FlatList windowSize 시맨틱)', () => {
  const off = buildOffsets(1000, { estimatedItemSize: 100 }); // 뷰포트=500
  const W = (
    scrollOffset: number,
    windowSize: number,
    initialNumToRender: number
  ) =>
    computeWindow(off, 1000, {
      scrollOffset,
      viewportLength: 500,
      windowSize,
      initialNumToRender,
    });

  it('상단: 첫 스크롤 전 initialNumToRender 보장', () => {
    const w = W(0, 1, 10);
    expect(w.first).toBe(0);
    expect(w.last).toBeGreaterThanOrEqual(10);
  });

  it('windowSize=1 → 가시구간만(오버스캔 0)', () => {
    const w = W(5000, 1, 0);
    expect(w.first).toBe(50);
    expect(w.last).toBe(56);
  });

  it('windowSize=3 → 위아래 1뷰포트(=5행)씩 확장', () => {
    const w = W(5000, 3, 0);
    expect(w.first).toBe(45);
    expect(w.last).toBe(61);
  });

  it('상단/하단 경계 클램프', () => {
    expect(W(0, 21, 0).first).toBe(0);
    expect(W(100_000, 21, 0).last).toBe(1000);
  });

  it('count=0 → 빈 윈도우', () => {
    expect(
      computeWindow(new Float64Array([0]), 0, {
        scrollOffset: 0,
        viewportLength: 500,
        windowSize: 21,
        initialNumToRender: 10,
      })
    ).toEqual({ first: 0, last: 0 });
  });

  it('음수 scroll 은 0 으로 처리', () => {
    expect(W(-300, 1, 0).first).toBe(0);
  });

  it('가변 높이에서도 이진탐색이 올바른 first', () => {
    const v = buildOffsets(5, {
      estimatedItemSize: 0,
      getItemLength: (i) => [100, 200, 50, 400, 100][i]!,
    });
    // offsets [0,100,300,350,750,850], scroll 320 vp 100 ws1
    // offsets[2]=300<=320 < offsets[3]=350 → first=2
    const w = computeWindow(v, 5, {
      scrollOffset: 320,
      viewportLength: 100,
      windowSize: 1,
      initialNumToRender: 0,
    });
    expect(w.first).toBe(2);
    expect(v[w.first]).toBeLessThanOrEqual(320);
    expect(v[w.first + 1]).toBeGreaterThan(320);
  });
});

describe('isViewable (FlatList 임계 모드 동일)', () => {
  it('itemVisiblePercentThreshold: 항목 50% 보임', () => {
    expect(
      isViewable(100, 100, 150, 1000, { itemVisiblePercentThreshold: 50 })
    ).toBe(true);
    expect(
      isViewable(100, 100, 151, 1000, { itemVisiblePercentThreshold: 50 })
    ).toBe(false);
  });
  it('viewAreaCoveragePercentThreshold: 뷰포트 점유율', () => {
    expect(
      isViewable(0, 300, 0, 100, { viewAreaCoveragePercentThreshold: 80 })
    ).toBe(true);
    expect(
      isViewable(0, 40, 0, 100, { viewAreaCoveragePercentThreshold: 80 })
    ).toBe(false);
  });
  it('둘 다 주면 viewAreaCoverage 가 우선(상호배타)', () => {
    // item 100% 보이지만 뷰포트 점유 10% < 80 → area 기준으로 false
    expect(
      isViewable(0, 100, 0, 1000, {
        itemVisiblePercentThreshold: 100,
        viewAreaCoveragePercentThreshold: 80,
      })
    ).toBe(false);
  });
  it('기본(임계 미지정): 1px 라도 보이면 true', () => {
    expect(isViewable(99, 50, 0, 100, {})).toBe(true);
    expect(isViewable(100, 50, 0, 100, {})).toBe(false);
  });
  it('length<=0 항목은 보이지 않음', () => {
    expect(isViewable(0, 0, 0, 100, {})).toBe(false);
  });
  it('뷰포트 밖(위) 항목 false', () => {
    expect(
      isViewable(0, 100, 500, 100, { itemVisiblePercentThreshold: 1 })
    ).toBe(false);
  });
});

describe('computeViewableItems', () => {
  const off = buildOffsets(100, { estimatedItemSize: 100 });
  const base = {
    keyOf: (i: number) => `k${i}`,
    itemOf: (i: number) => ({ v: i }),
  };

  it('가시 토큰만 index 오름차순', () => {
    const t = computeViewableItems(off, 100, {
      scrollOffset: 250,
      viewportLength: 200,
      config: {},
      ...base,
    });
    expect(t.map((x) => x.index)).toEqual([2, 3, 4]);
    expect(t[0]).toEqual({
      index: 2,
      key: 'k2',
      isViewable: true,
      item: { v: 2 },
    });
  });
  it('임계 적용 시 부분 항목 제외', () => {
    const t = computeViewableItems(off, 100, {
      scrollOffset: 250,
      viewportLength: 200,
      config: { itemVisiblePercentThreshold: 100 },
      ...base,
    });
    expect(t.map((x) => x.index)).toEqual([3]);
  });
  it('count=0 → 빈 배열', () => {
    expect(
      computeViewableItems(new Float64Array([0]), 0, {
        scrollOffset: 0,
        viewportLength: 200,
        config: {},
        ...base,
      })
    ).toEqual([]);
  });
});

describe('diffViewable (onViewableItemsChanged 페이로드)', () => {
  it('변화 없으면 null (콜백 미발화, early-out)', () => {
    expect(diffViewable(toMap([mk(1), mk(2)]), [mk(1), mk(2)])).toBeNull();
  });
  it('새로 들어온 항목은 changed(isViewable true)', () => {
    const r = diffViewable(toMap([mk(1)]), [mk(1), mk(2)]);
    expect(r?.changed.map((c) => c.key)).toEqual(['k2']);
    expect(r?.changed[0]!.isViewable).toBe(true);
    expect(r?.viewableItems).toHaveLength(2);
  });
  it('나간 항목은 직전 토큰(실제 index/item) + isViewable:false', () => {
    const r = diffViewable(toMap([mk(1), mk(2)]), [mk(2)]);
    const gone = r?.changed.find((c) => c.key === 'k1');
    expect(gone).toEqual({
      index: 1,
      key: 'k1',
      isViewable: false,
      item: { v: 1 },
    });
  });
  it('동시 진입/이탈', () => {
    const r = diffViewable(toMap([mk(1)]), [mk(2)]);
    expect(r?.changed.map((c) => [c.key, c.isViewable]).sort()).toEqual([
      ['k1', false],
      ['k2', true],
    ]);
  });
  it('빈→빈 은 null', () => {
    expect(diffViewable(new Map(), [])).toBeNull();
  });
  it('같은 키 집합이면 길이 같아도 null(early-out)', () => {
    expect(diffViewable(toMap([mk(3), mk(4)]), [mk(4), mk(3)])).toBeNull();
  });
});

describe('ringIndex (③ 링버퍼 슬롯↔데이터 — 교차 계약)', () => {
  const P = 14;
  const set = (W: number) =>
    Array.from({ length: P }, (_, s) => ringIndex(s, W, P)).sort(
      (a, b) => a - b
    );

  it('윈도우 [W,W+P) 를 정확히 한 번씩 덮음', () => {
    for (const W of [0, 1, 7, 100, 1986]) {
      expect(set(W)).toEqual(Array.from({ length: P }, (_, i) => W + i));
    }
  });
  it('W→W+1 시 정확히 1 슬롯만 변경', () => {
    for (const W of [0, 5, 137]) {
      let changed = 0;
      for (let s = 0; s < P; s++)
        if (ringIndex(s, W, P) !== ringIndex(s, W + 1, P)) changed++;
      expect(changed).toBe(1);
    }
  });
  it('W=0 이면 슬롯=데이터 인덱스', () => {
    for (let s = 0; s < P; s++) expect(ringIndex(s, 0, P)).toBe(s);
  });
  it('W→W+1: 빠져나간 행을 보던 슬롯이 새 바닥행을 받음', () => {
    // W=0→1: 슬롯0(행0 보던)→행14(=W+P-1+1 의 새 바닥)
    expect(ringIndex(0, 0, P)).toBe(0);
    expect(ringIndex(0, 1, P)).toBe(P); // 14
    expect(ringIndex(1, 1, P)).toBe(1); // 나머지 불변
  });
});

describe('isEndReached (FlatList onEndReachedThreshold)', () => {
  it('끝 근처에서 true', () => {
    expect(isEndReached(800, 200, 1000, 0.5)).toBe(true);
  });
  it('멀면 false', () => {
    expect(isEndReached(0, 200, 1000, 0.5)).toBe(false);
  });
  it('임계 경계', () => {
    expect(isEndReached(700, 200, 1000, 0.5)).toBe(true);
    expect(isEndReached(699, 200, 1000, 0.5)).toBe(false);
  });
  it('threshold=0 은 바닥에서만', () => {
    expect(isEndReached(800, 200, 1000, 0)).toBe(true);
    expect(isEndReached(799, 200, 1000, 0)).toBe(false);
  });
  it('contentLength<=0 → false', () => {
    expect(isEndReached(0, 200, 0, 0.5)).toBe(false);
  });
});
