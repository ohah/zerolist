import { forwardRef, useRef } from 'react';
import { FlashList, type FlashListRef } from '@shopify/flash-list';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import {
  renderCell,
  scrollYHandler,
  SCROLL_THROTTLE,
  useScrollableHandle,
} from './shared';

// FlashList v2 는 레이아웃을 자동 측정·재활용하므로 offsets/estimated
// 힌트를 받지 않는다(설계상 그게 v2 의 최강 경로). 다른 엔진과 API 가
// 달라 동일 힌트 주입 불가 — 이 비대칭은 결과 로그(hint=none)에 표기.
export const FlashListEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    const listRef = useRef<FlashListRef<(typeof p.items)[number]>>(null);
    useScrollableHandle(ref, listRef);

    return (
      <FlashList
        ref={listRef}
        data={p.items}
        keyExtractor={(it) => String(it.id)}
        renderItem={renderCell(p)}
        onScroll={scrollYHandler(p.onScrollY)}
        scrollEventThrottle={SCROLL_THROTTLE}
      />
    );
  }
);
