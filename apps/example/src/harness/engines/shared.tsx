import {
  forwardRef,
  useImperativeHandle,
  type ComponentType,
  type Ref,
  type RefObject,
} from 'react';
import {
  StyleSheet,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';
import { Cell } from '../cells';
import type { Item, ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';

// 3 어댑터(flatlist/legend/flashlist)가 동일하게 쓰던 보일러플레이트.
// 세 라이브러리 모두 scrollToOffset({offset,animated}) 동일 API.

type AnyListRef = {
  scrollToOffset(p: { offset: number; animated?: boolean }): void;
} | null;

export function useScrollableHandle(
  ref: Ref<Scrollable>,
  listRef: RefObject<AnyListRef>
) {
  useImperativeHandle(ref, () => ({
    scrollToOffset: (offset: number, animated = false) =>
      listRef.current?.scrollToOffset({ offset, animated }),
  }));
}

export function renderCell(
  p: Pick<ListEngineProps, 'cell' | 'height' | 'onMeasure' | 'onRender'>
) {
  return ({ item }: { item: Item }) => (
    <Cell
      item={item}
      cell={p.cell}
      height={p.height}
      onMeasure={p.onMeasure}
      onRender={p.onRender}
    />
  );
}

export function scrollYHandler(onScrollY?: (y: number) => void) {
  return (e: NativeSyntheticEvent<NativeScrollEvent>) =>
    onScrollY?.(e.nativeEvent.contentOffset.y);
}

// 진행 추적 JS 부하를 엔진 간 동일하게(패리티).
export const SCROLL_THROTTLE = 16;

const fill = StyleSheet.create({ s: { flex: 1 } }).s;

// 네이티브 호스트 엔진(native/nativezig) 공용: 네이티브가 셀을 직접
// 렌더하므로 JS scrollToOffset 은 no-op. props 매핑만 다름.
export function makeNativeHostEngine<P>(
  Comp: ComponentType<P & { style?: unknown }>,
  mapProps: (p: ListEngineProps) => P
) {
  return forwardRef<Scrollable, ListEngineProps>((p, ref) => {
    useImperativeHandle(ref, () => ({ scrollToOffset: () => {} }));
    return <Comp {...mapProps(p)} style={fill} />;
  });
}
