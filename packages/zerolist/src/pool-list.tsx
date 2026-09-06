import {
  Fragment,
  forwardRef,
  memo,
  useCallback,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';
import {
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';
import type { ZeroListProps, ZeroListHandle } from './windowed-list';
import PoolHost from './pool-host';
import { defaultKeyExtractor } from './virtualizer';
import { decodeBinding, reconcileSlots, type PoolSlot } from './pool-layout';

const separators = { highlight() {}, unhighlight() {}, updateProps() {} };
const fill = { flex: 1 };
const slotStyle = { position: 'absolute' as const, left: 0, right: 0 };
function Content<T>({
  item,
  index,
  renderItem,
}: {
  item: T;
  index: number;
  renderItem: ZeroListProps<T>['renderItem'];
  extraData: unknown;
}) {
  return renderItem({ item, index, separators });
}
const MemoContent = memo(Content) as typeof Content;

type State<T> = {
  data: readonly T[];
  keyExtractor: ZeroListProps<T>['keyExtractor'];
  rowHeight: number;
  capacity: number;
  epoch: number;
  version: number;
  slots: PoolSlot[];
};

function PoolList<T>(
  props: ZeroListProps<T> & { rowHeight: number },
  ref: React.ForwardedRef<ZeroListHandle<T>>
) {
  const {
    data: source,
    rowHeight,
    renderItem,
    keyExtractor,
    extraData,
    windowSize = 21,
    initialNumToRender = 10,
  } = props;
  const data = source!;
  const nativeRef = useRef<React.ComponentRef<typeof View>>(null);
  const [viewport, setViewport] = useState(0);
  const [width, setWidth] = useState(0);
  const latestOffset = useRef(0);
  const commandId = useRef(0);
  const [command, setCommand] = useState('');
  const endArmed = useRef(true);
  const overscan =
    viewport > 0
      ? Math.max(
          0,
          Math.ceil(
            ((Math.max(1, windowSize) - 1) * viewport) / (2 * rowHeight)
          )
        )
      : 0;
  const capacity = Math.min(
    data.length,
    Math.max(initialNumToRender, Math.ceil(viewport / rowHeight) + 2 * overscan)
  );
  const keyOf = (index: number) =>
    keyExtractor
      ? keyExtractor(data[index]!, index)
      : defaultKeyExtractor(data[index], index);
  const [state, setState] = useState<State<T>>(() => ({
    data,
    keyExtractor,
    rowHeight,
    capacity,
    epoch: 0,
    version: -1,
    slots: reconcileSlots(
      [],
      Array.from({ length: capacity }, (_, i) => i),
      keyOf
    ),
  }));
  // 새 데이터·풀 크기의 이벤트 세대를 바꾼다. 이전 세대의 지연 요청은 수용하지 않는다.
  if (
    state.data !== data ||
    state.keyExtractor !== keyExtractor ||
    state.rowHeight !== rowHeight ||
    state.capacity !== capacity
  ) {
    const first = Math.max(
      0,
      Math.min(
        props.onScroll || props.onEndReached
          ? Math.floor(latestOffset.current / rowHeight) - overscan
          : Math.min(...state.slots.map((slot) => slot.index)),
        data.length - capacity
      )
    );
    setState({
      data,
      keyExtractor,
      rowHeight,
      capacity,
      epoch: state.epoch + 1,
      version: -1,
      slots: reconcileSlots(
        state.slots,
        Array.from({ length: capacity }, (_, i) => first + i),
        keyOf
      ),
    });
  }
  const scrollTo = useCallback(
    (offset: number, animated = true) => {
      if (!Number.isFinite(offset)) return;
      setCommand(
        `${++commandId.current},${Math.max(0, Math.min(offset, data.length * rowHeight - viewport))},${animated ? 1 : 0}`
      );
    },
    [data.length, rowHeight, viewport]
  );
  useImperativeHandle(
    ref,
    () => ({
      scrollToOffset: ({ offset, animated }) => scrollTo(offset, animated),
      scrollToIndex: ({
        index,
        animated,
        viewOffset = 0,
        viewPosition = 0,
      }) => {
        if (!Number.isInteger(index) || index < 0 || index >= data.length) {
          props.onScrollToIndexFailed?.({
            index,
            highestMeasuredFrameIndex: data.length - 1,
            averageItemLength: rowHeight,
          });
          return;
        }
        scrollTo(
          index * rowHeight -
            viewOffset -
            viewPosition * (viewport - rowHeight),
          animated
        );
      },
      scrollToItem: ({ item, animated }) => {
        const i = data.indexOf(item);
        if (i >= 0) scrollTo(i * rowHeight, animated);
      },
      scrollToEnd: ({ animated = true } = {}) =>
        scrollTo(data.length * rowHeight - viewport, animated),
      flashScrollIndicators: () => setCommand(`${++commandId.current},flash,0`),
      recordInteraction: () => {},
      getScrollableNode: () => nativeRef.current,
    }),
    [data, props.onScrollToIndexFailed, rowHeight, scrollTo, viewport]
  );
  const initialPositioned = useRef(false);
  return (
    <PoolHost
      ref={nativeRef}
      testID={props.testID}
      style={[fill, props.style]}
      count={data.length}
      rowHeight={rowHeight}
      dataVersion={state.epoch}
      preparationMode={0}
      committedVersion={state.version}
      committedBinds={state.slots.map((s) => s.index).join(',')}
      overscan={overscan}
      scrollCommand={command}
      scrollIndicator={props.showsVerticalScrollIndicator === false ? 0 : 1}
      reportScroll={!!(props.onScroll || props.onEndReached)}
      onLayout={(e: any) => {
        setViewport(e.nativeEvent.layout.height);
        setWidth(e.nativeEvent.layout.width);
        props.onLayout?.(e);
        if (!initialPositioned.current && e.nativeEvent.layout.height > 0) {
          initialPositioned.current = true;
          if (props.initialScrollIndex != null)
            scrollTo(props.initialScrollIndex * rowHeight, false);
        }
      }}
      onRecycle={(e: {
        nativeEvent: { binds: string; version: number; dataVersion: number };
      }) => {
        const { binds, version, dataVersion } = e.nativeEvent;
        if (dataVersion !== state.epoch) return;
        const indices = decodeBinding(binds, data.length, capacity);
        if (!indices) return;
        setState((previous) =>
          dataVersion !== previous.epoch || version <= previous.version
            ? previous
            : {
                ...previous,
                version,
                slots: reconcileSlots(previous.slots, indices, keyOf),
              }
        );
      }}
      onPoolScroll={(e: {
        nativeEvent: { offset: number; viewport: number };
      }) => {
        const { offset, viewport: vp } = e.nativeEvent;
        latestOffset.current = offset;
        const distance = data.length * rowHeight - offset - vp;
        const atEnd = distance <= (props.onEndReachedThreshold ?? 0.5) * vp;
        if (atEnd && endArmed.current) {
          endArmed.current = false;
          props.onEndReached?.({ distanceFromEnd: distance });
        } else if (!atEnd) endArmed.current = true;
        props.onScroll?.({
          ...e,
          nativeEvent: {
            contentOffset: { x: 0, y: offset },
            contentSize: { width, height: data.length * rowHeight },
            layoutMeasurement: { width, height: vp },
            contentInset: { top: 0, left: 0, bottom: 0, right: 0 },
            zoomScale: 1,
          },
        } as NativeSyntheticEvent<NativeScrollEvent>);
      }}
    >
      {state.slots.map((slot, s) => (
        <View
          key={s}
          collapsable={false}
          style={[slotStyle, { height: rowHeight }]}
        >
          <Fragment key={slot.key}>
            <MemoContent
              item={data[slot.index]!}
              index={slot.index}
              renderItem={renderItem}
              extraData={extraData}
            />
          </Fragment>
        </View>
      ))}
    </PoolHost>
  );
}
export const NativePoolList = forwardRef(PoolList) as <T>(
  props: ZeroListProps<T> & {
    rowHeight: number;
    ref?: React.ForwardedRef<ZeroListHandle<T>>;
  }
) => React.ReactElement;
