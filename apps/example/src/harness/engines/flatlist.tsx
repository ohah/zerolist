import { useWindowDimensions } from 'react-native';
import { forwardRef, useRef } from 'react';
import { FlatList } from 'react-native';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import {
  renderCell,
  scrollYHandler,
  SCROLL_THROTTLE,
  useScrollableHandle,
} from './shared';

// 패리티: offsets 가 있으면 getItemLayout 로 연결(엔진의 최강 힌트).
export const FlatListEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    const { height: viewportHeight } = useWindowDimensions();
    const windowSize =
      p.bufferRows == null || p.bufferRows < 0
        ? 11
        : 1 + (2 * p.bufferRows * (p.fixedHeight ?? 100)) / viewportHeight;
    const listRef = useRef<FlatList<(typeof p.items)[number]>>(null);
    useScrollableHandle(ref, listRef);
    const offsets = p.offsets;

    return (
      <FlatList
        ref={listRef}
        data={p.items}
        keyExtractor={(it) => String(it.id)}
        renderItem={renderCell(p)}
        getItemLayout={
          offsets
            ? (_, index) => ({
                length: p.items[index]!.height,
                offset: offsets[index]!,
                index,
              })
            : undefined
        }
        onScroll={scrollYHandler(p.onScrollY)}
        scrollEventThrottle={SCROLL_THROTTLE}
        initialNumToRender={
          p.bufferRows == null || p.bufferRows < 0
            ? 12
            : Math.max(1, Math.ceil(viewportHeight / (p.fixedHeight ?? 100)))
        }
        windowSize={windowSize}
        removeClippedSubviews
      />
    );
  }
);

export const FlatPaletteEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => <FlatListEngine {...p} ref={ref} nativePalette />
);
