import { forwardRef, useRef } from 'react';
import { LegendList, type LegendListRef } from '@legendapp/list';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import {
  renderCell,
  scrollYHandler,
  SCROLL_THROTTLE,
  useScrollableHandle,
} from './shared';

// dynamic(offsets·fixedHeight 둘 다 null)에서만 쓰는 추정 기본값.
const DYNAMIC_ESTIMATE = 100;

// 패리티: fixed/variable 는 offsets 에서 도출한 크기를
// getEstimatedItemSize 로 전달(Legend 의 최강 등가 힌트).
export const LegendEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    const listRef = useRef<LegendListRef>(null);
    useScrollableHandle(ref, listRef);
    const { offsets, fixedHeight, items } = p;

    const estimate =
      fixedHeight ??
      (offsets
        ? offsets[offsets.length - 1]! / (items.length || 1)
        : DYNAMIC_ESTIMATE);

    return (
      <LegendList
        ref={listRef}
        data={items}
        recycleItems
        keyExtractor={(it) => String(it.id)}
        estimatedItemSize={estimate}
        getEstimatedItemSize={
          offsets ? (i) => offsets[i + 1]! - offsets[i]! : undefined
        }
        onScroll={scrollYHandler(p.onScrollY)}
        scrollEventThrottle={SCROLL_THROTTLE}
        renderItem={renderCell(p)}
      />
    );
  }
);
