import { forwardRef, useImperativeHandle, useMemo, useRef } from 'react';
import { FlatList } from 'react-native';
import { jsRef } from '@ohah/zerolist';
import { Cell } from '../cells';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';

// fixed/variable 는 높이를 알므로 getItemLayout 제공(엔진이 쓸 수
// 있는 최선을 쓰게 함 = 공정). dynamic 은 미제공(미지 높이 = jank 경로).
export const FlatListEngine = forwardRef<Scrollable, ListEngineProps>(
  ({ items, cell, height, onMeasure }, ref) => {
    const listRef = useRef<FlatList<(typeof items)[number]>>(null);
    useImperativeHandle(ref, () => ({
      scrollToOffset: (offset, animated = false) =>
        listRef.current?.scrollToOffset({ offset, animated }),
    }));

    const offsets = useMemo(() => {
      if (height === 'dynamic') return null;
      const heights = new Float32Array(items.length);
      for (let i = 0; i < items.length; i++) heights[i] = items[i]!.height;
      const o = new Float64Array(items.length + 1);
      jsRef.buildOffsets(heights, o); // 누적오프셋 = 라이브러리와 단일 소스
      return o;
    }, [items, height]);

    return (
      <FlatList
        ref={listRef}
        data={items}
        keyExtractor={(it) => String(it.id)}
        renderItem={({ item }) => (
          <Cell item={item} cell={cell} height={height} onMeasure={onMeasure} />
        )}
        getItemLayout={
          offsets
            ? (_, index) => ({
                length: items[index]!.height,
                offset: offsets[index]!,
                index,
              })
            : undefined
        }
        initialNumToRender={12}
        windowSize={11}
        removeClippedSubviews
      />
    );
  }
);
