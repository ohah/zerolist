import { forwardRef, useMemo } from 'react';
import {
  ZeroList as WindowedList,
  type ZeroListProps,
  type ZeroListHandle,
} from './windowed-list';
import { NativePoolList } from './pool-list';
import { poolAvailable } from './pool-host';
import { uniformLength } from './pool-layout';

export type { ZeroListProps, ZeroListHandle } from './windowed-list';

// 지원하지 않는 ScrollView 기능을 조용히 무시하지 않고 기존 구현에 위임한다.
// 사용자는 엔진을 선택하지 않는다. 데이터 길이 전체를 검사해 비균일 높이를 배제한다.
const poolProps = new Set([
  'data',
  'renderItem',
  'keyExtractor',
  'getItemLayout',
  'extraData',
  'estimatedItemSize',
  'windowSize',
  'initialNumToRender',
  'initialScrollIndex',
  'style',
  'testID',
  'onScroll',
  'scrollEventThrottle',
  'onEndReached',
  'onEndReachedThreshold',
  'onScrollToIndexFailed',
  'onLayout',
  'showsVerticalScrollIndicator',
]);
function UnifiedList<T>(
  props: ZeroListProps<T>,
  ref: React.ForwardedRef<ZeroListHandle<T>>
) {
  const supported =
    (props.scrollEventThrottle == null || props.scrollEventThrottle <= 16) &&
    Object.keys(props).every(
      (key) =>
        poolProps.has(key) || props[key as keyof typeof props] === undefined
    );
  const height = useMemo(
    () =>
      poolAvailable && supported && props.data && props.getItemLayout
        ? uniformLength(props.data, props.getItemLayout)
        : null,
    [supported, props.data, props.getItemLayout]
  );
  return poolAvailable &&
    height != null &&
    supported &&
    (props.scrollEventThrottle == null || props.scrollEventThrottle <= 16) ? (
    <NativePoolList {...props} rowHeight={height} ref={ref} />
  ) : (
    <WindowedList {...props} ref={ref} />
  );
}
export const ZeroList = forwardRef(UnifiedList) as <T>(
  props: ZeroListProps<T> & { ref?: React.ForwardedRef<ZeroListHandle<T>> }
) => React.ReactElement;
