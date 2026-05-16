// ZeroList — FlatList drop-in. props/ref 표면을 FlatList 와 동일하게
// 맞추고, 윈도잉·가시성·끝도달 판정은 순수 가상화 엔진(virtualizer.ts,
// = Zig 와 동일 알고리즘)에 위임한다. RN ScrollView 위에서 동작하므로
// native/web 공용. (파일명 list.tsx — 대소문자 비구분 FS 에서
// zerolist.tsx 와 충돌 회피)
//
// 주의(PoC): 동작/호환은 테스트로 검증하지만 "네이티브급 성능"은
// 실기기 측정 전까지 미검증 — 여기서 주장하지 않는다.
import type * as React from 'react';
import {
  Fragment,
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import type {
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
  StyleProp,
  ViewStyle,
} from 'react-native';
import { RefreshControl, ScrollView, View } from 'react-native';
import {
  buildOffsets,
  computeViewableItems,
  computeWindow,
  defaultKeyExtractor,
  diffViewable,
  groupIntoRows,
  isEndReached,
  type ViewabilityConfig,
  type ViewToken,
  type Window,
} from './virtualizer';

type RenderItemInfo<ItemT> = {
  item: ItemT;
  index: number;
  separators: {
    highlight: () => void;
    unhighlight: () => void;
    updateProps: (select: 'leading' | 'trailing', newProps: object) => void;
  };
};

type Renderable =
  | React.ComponentType<unknown>
  | React.ReactElement
  | null
  | undefined;

export type ZeroListProps<ItemT> = {
  data: ReadonlyArray<ItemT> | null | undefined;
  renderItem: (info: RenderItemInfo<ItemT>) => React.ReactElement | null;
  keyExtractor?: (item: ItemT, index: number) => string;
  getItemLayout?: (
    data: ReadonlyArray<ItemT> | null | undefined,
    index: number
  ) => { length: number; offset: number; index: number };
  ItemSeparatorComponent?: React.ComponentType<unknown> | null;
  ListHeaderComponent?: Renderable;
  ListFooterComponent?: Renderable;
  ListEmptyComponent?: Renderable;
  ListHeaderComponentStyle?: StyleProp<ViewStyle>;
  ListFooterComponentStyle?: StyleProp<ViewStyle>;
  horizontal?: boolean | null;
  numColumns?: number;
  inverted?: boolean | null;
  onEndReached?: ((info: { distanceFromEnd: number }) => void) | null;
  onEndReachedThreshold?: number | null;
  onViewableItemsChanged?:
    | ((info: { viewableItems: ViewToken[]; changed: ViewToken[] }) => void)
    | null;
  viewabilityConfig?: ViewabilityConfig;
  refreshing?: boolean | null;
  onRefresh?: (() => void) | null;
  initialNumToRender?: number;
  windowSize?: number;
  initialScrollIndex?: number | null;
  onScroll?: (e: NativeSyntheticEvent<NativeScrollEvent>) => void;
  scrollEventThrottle?: number;
  extraData?: unknown;
  /** ZeroList 확장: 측정 전 추정 행 크기(FlatList 는 내부 추정). */
  estimatedItemSize?: number;
  style?: StyleProp<ViewStyle>;
  contentContainerStyle?: StyleProp<ViewStyle>;
  columnWrapperStyle?: StyleProp<ViewStyle>;
  testID?: string;
};

export type ZeroListHandle<ItemT = unknown> = {
  scrollToOffset: (p: { offset: number; animated?: boolean }) => void;
  scrollToIndex: (p: {
    index: number;
    animated?: boolean;
    viewOffset?: number;
  }) => void;
  scrollToItem: (p: { item: ItemT; animated?: boolean }) => void;
  scrollToEnd: (p?: { animated?: boolean }) => void;
  flashScrollIndicators: () => void;
  recordInteraction: () => void;
  getScrollableNode: () => unknown;
};

const EMPTY: readonly never[] = [];
const INVERT: ViewStyle = { transform: [{ scaleY: -1 }] };
const DEFAULTS = {
  onEndReachedThreshold: 0.5,
  initialNumToRender: 10,
  windowSize: 21,
  estimatedItemSize: 50,
  scrollEventThrottle: 16,
};

function render(node: Renderable): React.ReactElement | null {
  if (node == null) return null;
  if (typeof node === 'function') {
    const C = node as React.ComponentType<unknown>;
    return <C />;
  }
  return node as React.ReactElement;
}

function ZeroListInner<ItemT>(
  props: ZeroListProps<ItemT>,
  ref: React.ForwardedRef<ZeroListHandle<ItemT>>
) {
  const {
    data,
    renderItem,
    keyExtractor,
    getItemLayout,
    ItemSeparatorComponent,
    ListHeaderComponent,
    ListFooterComponent,
    ListEmptyComponent,
    ListHeaderComponentStyle,
    ListFooterComponentStyle,
    horizontal,
    numColumns = 1,
    inverted,
    onEndReached,
    onEndReachedThreshold = DEFAULTS.onEndReachedThreshold,
    onViewableItemsChanged,
    viewabilityConfig,
    refreshing,
    onRefresh,
    initialNumToRender = DEFAULTS.initialNumToRender,
    windowSize = DEFAULTS.windowSize,
    initialScrollIndex,
    onScroll,
    scrollEventThrottle = DEFAULTS.scrollEventThrottle,
    estimatedItemSize = DEFAULTS.estimatedItemSize,
    style,
    contentContainerStyle,
    columnWrapperStyle,
    testID,
  } = props;

  const items = (data ?? EMPTY) as ReadonlyArray<ItemT>;
  const count = items.length;
  const cols = Math.max(1, Math.floor(numColumns));
  const isH = !!horizontal;

  const scrollRef = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const measured = useRef<Map<number, number>>(new Map());
  const prevViewable = useRef<Map<string, ViewToken>>(new Map());
  const endReachedArmed = useRef(true);
  const measureRaf = useRef<number | null>(null);
  // 리렌더는 윈도우 경계가 실제로 바뀔 때만(handleScroll) — 매 스크롤
  // setState 리렌더 회피. scrollOffset state 는 그 게이트된 값만 보관.
  const [scrollOffset, setScrollOffset] = useState(0);
  const [viewport, setViewport] = useState(0);
  // measured(ref Map) 변경을 useMemo 에 반영시키는 무효화 카운터.
  const [measureNonce, setMeasureNonce] = useState(0);

  const keyOf = useCallback(
    (i: number) =>
      keyExtractor
        ? keyExtractor(items[i] as ItemT, i)
        : defaultKeyExtractor(items[i], i),
    [keyExtractor, items]
  );

  const rows = useMemo(
    () => (cols > 1 ? groupIntoRows(count, cols) : null),
    [cols, count]
  );
  const rowCount = rows ? rows.length : count;

  const offsets = useMemo(
    () => {
      const getRowLength = (rowIdx: number): number | undefined => {
        if (!getItemLayout) return undefined;
        return getItemLayout(data, rows ? rows[rowIdx]![0]! : rowIdx).length;
      };
      return buildOffsets(rowCount, {
        getItemLength: getItemLayout ? getRowLength : undefined,
        measured: rows ? undefined : measured.current,
        estimatedItemSize,
      });
    },
    // measured.current(ref) 변경은 measureNonce 로만 반영된다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [rowCount, getItemLayout, data, rows, estimatedItemSize, measureNonce]
  );

  const contentLength = offsets[rowCount] ?? 0;

  const win = useMemo(
    () =>
      computeWindow(offsets, rowCount, {
        scrollOffset,
        viewportLength: viewport || 1,
        windowSize,
        initialNumToRender,
      }),
    [offsets, rowCount, scrollOffset, viewport, windowSize, initialNumToRender]
  );
  const winRef = useRef<Window>(win);
  winRef.current = win;

  const rowToItem = useCallback(
    (r: number) => (rows ? rows[r]![0]! : r),
    [rows]
  );

  const fireViewability = useCallback(
    (offset: number) => {
      if (!onViewableItemsChanged || viewport <= 0) return;
      const current = computeViewableItems(offsets, rowCount, {
        scrollOffset: offset,
        viewportLength: viewport,
        config: viewabilityConfig ?? {},
        keyOf: (r) => keyOf(rowToItem(r)),
        itemOf: (r) => items[rowToItem(r)],
      });
      const delta = diffViewable(prevViewable.current, current);
      if (delta) {
        prevViewable.current = new Map(current.map((t) => [t.key, t]));
        onViewableItemsChanged(delta);
      }
    },
    [
      onViewableItemsChanged,
      viewport,
      offsets,
      rowCount,
      viewabilityConfig,
      keyOf,
      rowToItem,
      items,
    ]
  );

  const handleScroll = useCallback(
    (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      const o = e.nativeEvent.contentOffset;
      const offset = isH ? o.x : o.y;
      // 윈도우 경계가 실제로 바뀔 때만 리렌더.
      const next = computeWindow(offsets, rowCount, {
        scrollOffset: offset,
        viewportLength: viewport || 1,
        windowSize,
        initialNumToRender,
      });
      if (
        next.first !== winRef.current.first ||
        next.last !== winRef.current.last
      )
        setScrollOffset(offset);

      const threshold = onEndReachedThreshold ?? DEFAULTS.onEndReachedThreshold;
      const atEnd = isEndReached(offset, viewport, contentLength, threshold);
      if (atEnd && endReachedArmed.current && onEndReached) {
        endReachedArmed.current = false;
        onEndReached({ distanceFromEnd: contentLength - (offset + viewport) });
      } else if (!atEnd) {
        endReachedArmed.current = true;
      }
      fireViewability(offset);
      onScroll?.(e);
    },
    [
      isH,
      offsets,
      rowCount,
      viewport,
      windowSize,
      initialNumToRender,
      onEndReachedThreshold,
      contentLength,
      onEndReached,
      fireViewability,
      onScroll,
    ]
  );

  const onContainerLayout = useCallback(
    (e: LayoutChangeEvent) => {
      const { width, height } = e.nativeEvent.layout;
      setViewport(isH ? width : height);
    },
    [isH]
  );

  const offsetForIndex = useCallback(
    (index: number) => {
      const row = rows ? Math.floor(index / cols) : index;
      return offsets[Math.max(0, Math.min(row, rowCount))] ?? 0;
    },
    [rows, cols, offsets, rowCount]
  );

  const axisPoint = useCallback(
    (n: number, animated?: boolean) =>
      isH ? { x: n, y: 0, animated } : { x: 0, y: n, animated },
    [isH]
  );

  useImperativeHandle(ref, (): ZeroListHandle<ItemT> => {
    const scrollTo = (offset: number, animated = true) =>
      scrollRef.current?.scrollTo(axisPoint(offset, animated));
    return {
      scrollToOffset: ({ offset, animated }) => scrollTo(offset, animated),
      scrollToIndex: ({ index, animated, viewOffset = 0 }) =>
        scrollTo(offsetForIndex(index) - viewOffset, animated),
      scrollToItem: ({ item, animated }) => {
        const i = items.indexOf(item);
        if (i >= 0) scrollTo(offsetForIndex(i), animated);
      },
      scrollToEnd: ({ animated = true } = {}) =>
        scrollRef.current?.scrollToEnd({ animated }),
      flashScrollIndicators: () => scrollRef.current?.flashScrollIndicators(),
      recordInteraction: () => {},
      getScrollableNode: () => scrollRef.current,
    };
  }, [axisPoint, offsetForIndex, items]);

  // 측정 변경을 rAF 1회로 코얼레싱(초기 수렴 중 buildOffsets 다회 방지).
  const scheduleMeasureFlush = useCallback(() => {
    if (measureRaf.current != null) return;
    measureRaf.current = requestAnimationFrame(() => {
      measureRaf.current = null;
      setMeasureNonce((n) => n + 1);
    });
  }, []);
  useEffect(
    () => () => {
      if (measureRaf.current != null) cancelAnimationFrame(measureRaf.current);
    },
    []
  );

  const measureRow = useCallback(
    (rowIdx: number, e: LayoutChangeEvent) => {
      if (rows || getItemLayout) return; // 측정 불필요
      const len = isH
        ? e.nativeEvent.layout.width
        : e.nativeEvent.layout.height;
      if (measured.current.get(rowIdx) !== len) {
        measured.current.set(rowIdx, len);
        scheduleMeasureFlush();
      }
    },
    [rows, getItemLayout, isH, scheduleMeasureFlush]
  );

  const noopSeparators = useMemo(
    () => ({
      highlight: () => {},
      unhighlight: () => {},
      updateProps: () => {},
    }),
    []
  );

  const refreshControl = useMemo(
    () =>
      onRefresh ? (
        <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} />
      ) : undefined,
    [onRefresh, refreshing]
  );

  const bodyRows: React.ReactElement[] = [];
  if (count > 0)
    for (let r = win.first; r < win.last; r++) {
      const idxs = rows ? rows[r]! : [r];
      bodyRows.push(
        <View
          key={`row-${r}`}
          onLayout={(e) => measureRow(r, e)}
          style={
            rows
              ? [{ flexDirection: 'row' as const }, columnWrapperStyle]
              : undefined
          }
        >
          {idxs.map((i) => (
            <Fragment key={keyOf(i)}>
              {renderItem({
                item: items[i] as ItemT,
                index: i,
                separators: noopSeparators,
              })}
              {ItemSeparatorComponent && i < count - 1 ? (
                <ItemSeparatorComponent />
              ) : null}
            </Fragment>
          ))}
        </View>
      );
    }

  const leadPx = offsets[win.first] ?? 0;
  const tailPx = Math.max(
    0,
    contentLength - (offsets[win.last] ?? contentLength)
  );
  const mainSpacer = (px: number) => (isH ? { width: px } : { height: px });

  // inverted: 컨테이너를 뒤집고 콘텐츠를 다시 뒤집어 항목을 정상 표시
  // (FlatList 표준 구현). 주의(PoC 한계): inverted 시 contentOffset 좌표
  // 반전을 onEndReached/viewability 가 보정하지 않음 — 미구현.
  return (
    <ScrollView
      ref={scrollRef}
      testID={testID}
      style={inverted ? [style, INVERT] : style}
      horizontal={isH}
      onLayout={onContainerLayout}
      onScroll={handleScroll}
      scrollEventThrottle={scrollEventThrottle}
      contentContainerStyle={contentContainerStyle}
      contentOffset={
        initialScrollIndex != null
          ? axisPoint(offsetForIndex(initialScrollIndex))
          : undefined
      }
      refreshControl={refreshControl}
    >
      <View style={inverted ? INVERT : undefined}>
        {ListHeaderComponent ? (
          <View style={ListHeaderComponentStyle}>
            {render(ListHeaderComponent)}
          </View>
        ) : null}
        {count === 0 ? (
          render(ListEmptyComponent)
        ) : (
          <>
            <View style={mainSpacer(leadPx)} />
            {bodyRows}
            <View style={mainSpacer(tailPx)} />
          </>
        )}
        {ListFooterComponent ? (
          <View style={ListFooterComponentStyle}>
            {render(ListFooterComponent)}
          </View>
        ) : null}
      </View>
    </ScrollView>
  );
}

ZeroListInner.displayName = 'ZeroList';

export const ZeroList = forwardRef(ZeroListInner) as <ItemT>(
  props: ZeroListProps<ItemT> & {
    ref?: React.ForwardedRef<ZeroListHandle<ItemT>>;
  }
) => React.ReactElement;
