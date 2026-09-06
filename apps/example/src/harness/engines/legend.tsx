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
// getEstimatedItemSize 로 전달. 자원 예산 비교의 고정 높이 조건은
// getFixedItemSize도 제공해 실제 확정 높이를 활용한다.
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
        drawDistance={
          p.bufferRows == null || p.bufferRows < 0
            ? undefined
            : p.bufferRows * (p.fixedHeight ?? 100)
        }
        ref={listRef}
        data={items}
        recycleItems
        keyExtractor={(it) => String(it.id)}
        getFixedItemSize={
          p.bufferRows != null && p.bufferRows >= 0 && fixedHeight != null
            ? () => fixedHeight
            : undefined
        }
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
