import { useWindowDimensions } from 'react-native';
import { forwardRef, useRef } from 'react';
import { ZeroList, type ZeroListHandle } from '@ohah/zerolist';
import type { Item, ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import {
  renderCell,
  scrollYHandler,
  SCROLL_THROTTLE,
  useScrollableHandle,
} from './shared';

// 패리티: 다른 엔진과 동일한 offsets/fixedHeight 입력을 ZeroList 의
// 최강 힌트(getItemLayout)로 연결. dynamic 은 측정으로 수렴.
export const ZeroListEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    const { height: viewportHeight } = useWindowDimensions();
    const windowSize =
      p.bufferRows == null || p.bufferRows < 0
        ? 11
        : 1 + (2 * p.bufferRows * (p.fixedHeight ?? 100)) / viewportHeight;
    const listRef = useRef<ZeroListHandle<Item>>(null);
    useScrollableHandle(ref, listRef);
    const { offsets, fixedHeight, items } = p;

    return (
      <ZeroList
        ref={listRef}
        data={items}
        keyExtractor={(it) => String(it.id)}
        renderItem={renderCell(p)}
        getItemLayout={
          offsets
            ? (_, index) => ({
                length: items[index]!.height,
                offset: offsets[index]!,
                index,
              })
            : undefined
        }
        estimatedItemSize={fixedHeight ?? 100}
        onScroll={scrollYHandler(p.onScrollY)}
        scrollEventThrottle={SCROLL_THROTTLE}
        initialNumToRender={
          p.bufferRows == null || p.bufferRows < 0
            ? 12
            : Math.max(1, Math.ceil(viewportHeight / (p.fixedHeight ?? 100)))
        }
        windowSize={windowSize}
      />
    );
  }
);
