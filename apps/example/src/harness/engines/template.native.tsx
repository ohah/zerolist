import { forwardRef, useEffect, useRef } from 'react';
import { Image, StyleSheet, View, useWindowDimensions } from 'react-native';
import {
  getRuntimeKind,
  RuntimeKind,
  scheduleOnUI,
} from 'react-native-worklets';
import Animated, {
  useAnimatedProps,
  useAnimatedStyle,
  useDerivedValue,
  useEvent,
  useSharedValue,
  type SharedValue,
} from 'react-native-reanimated';
import ZlPoolList from '../../../specs/ZlPoolListNativeComponent';
import ZlTemplateText from '../../../specs/ZlTemplateTextNativeComponent';
import type { Item, ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import { inst } from '../instrument';
import { useNoopScrollable } from './shared';
import { packItems, columnItem, type Columns } from './templateData';

// WishList의 템플릿 발상을 현재 RN/Worklets API로 검증하는 별도 PoC.
// React는 구조를 한 번 만들고, UI 런타임이 이미 존재하는 네이티브 속성을 갱신한다.
// 일반 Text children, 임의 renderItem, 동적 높이를 지원하는 drop-in API가 아니다.
const Pool = Animated.createAnimatedComponent(ZlPoolList);
const NativeText = Animated.createAnimatedComponent(ZlTemplateText);
const IMG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAFklEQVR4nGNgYGD4z4AHMA4qAQAB/wQEZxJ3HQAAAABJRU5ErkJggg==';
const DOTS = Array.from({ length: 64 }, (_, i) => i);
type DataSource = Item[] | Columns;
type DataValue = { readonly value: DataSource };
type Binding = { version: number; encoded: string; indices: number[] };

function TemplateText({
  value,
  initial,
  kind,
}: {
  value: SharedValue<string>;
  initial: string;
  kind: 'title' | 'body' | 'sum';
}) {
  const props = useAnimatedProps(() => ({ content: value.value }));
  return (
    <NativeText
      content={initial}
      kind={kind === 'title' ? 0 : kind === 'body' ? 1 : 2}
      animatedProps={props}
      style={{
        height: kind === 'body' ? 54 : 20,
        marginTop: kind === 'title' ? 0 : 2,
      }}
    />
  );
}
function Dot({ item, d }: { item: SharedValue<Item>; d: number }) {
  const style = useAnimatedStyle(() => ({
    backgroundColor: `hsl(${item.value.hue + d * 5}, 60%, 70%)`,
  }));
  return <Animated.View style={[styles.dot, style]} />;
}
function Slot({
  slot,
  binding,
  data,
  initial,
  rh,
  heavy,
  audit,
}: {
  slot: number;
  binding: SharedValue<Binding>;
  data: DataValue;
  initial: Item;
  rh: number;
  heavy: boolean;
  audit: boolean;
}) {
  // 다른 슬롯만 바뀌면 같은 index 이후의 무거운 계산을 반복하지 않는다.
  const index = useDerivedValue(() => binding.value.indices[slot] ?? slot);
  const item = useDerivedValue(() => {
    // JS 초기 평가에서 UI 소유 배열 전체를 역직렬화하지 않는다.
    if (getRuntimeKind() !== RuntimeKind.UI) return initial;
    const source = data.value;
    const i = index.value;
    if (Array.isArray(source)) return source[i] ?? initial;
    return columnItem(source, i) ?? initial;
  });
  const title = useDerivedValue(() => item.value.title);
  const body = useDerivedValue(() => item.value.body);
  const sum = useDerivedValue(() => {
    if (!heavy) return '';
    let acc = 0;
    for (let i = 0; i < 4000; i++)
      acc += Math.sqrt((i * (item.value.id + 1)) % 97);
    return `∑=${acc.toFixed(1)}`;
  });
  const style = useAnimatedStyle(() => ({
    backgroundColor: `hsl(${item.value.hue}, 60%, 92%)`,
  }));
  const props = useAnimatedProps(() =>
    audit ? { testID: `zl-row-${item.value.id}-h${rh}` } : {}
  );
  useEffect(() => {
    inst.mount();
    return () => inst.unmount();
  }, []);
  return (
    <View collapsable={false} style={[styles.slot, { height: rh }]}>
      <Animated.View
        collapsable={false}
        animatedProps={props}
        style={[styles.row, { height: rh }, style]}
      >
        {heavy ? (
          <>
            <View style={styles.imageRow}>
              <Image source={{ uri: IMG }} style={styles.thumb} />
              <View style={styles.flex}>
                <TemplateText
                  value={title}
                  initial={initial.title}
                  kind="title"
                />
                <TemplateText value={body} initial={initial.body} kind="body" />
                <TemplateText value={sum} initial="" kind="sum" />
              </View>
            </View>
            <View style={styles.grid}>
              {DOTS.map((d) => (
                <Dot key={d} d={d} item={item} />
              ))}
            </View>
          </>
        ) : (
          <TemplateText value={title} initial={initial.title} kind="title" />
        )}
      </Animated.View>
    </View>
  );
}
function useObjectData(items: Item[]) {
  const data = useSharedValue(items);
  useEffect(() => {
    data.value = items;
  }, [data, items]);
  return data;
}

function useCompactData(items: Item[]) {
  // UI 소유 데이터는 빈 배열로 시작한다. JS는 복원된 전체 값을 읽지 않는다.
  const data = useSharedValue<DataSource>([]);
  useEffect(() => {
    const start = performance.now();
    const columns = packItems(items);
    const encoded = JSON.stringify(columns);
    console.log(
      `[ZlData] phase=encode count=${items.length} chars=${encoded.length} ms=${performance.now() - start}`
    );
    scheduleOnUI((payload: string) => {
      'worklet';
      const start = performance.now();
      const decoded: Columns = JSON.parse(payload);
      data.value = decoded;
      console.log(
        `[ZlData] phase=decode count=${decoded.id.length} ms=${performance.now() - start}`
      );
    }, encoded);
    // 전달 문자열/열 배열을 shared value나 React 상태에 영구 보관하지 않는다.
    // 전체 스냅샷 복원 후 한 번에 공개하므로 스크롤 중 JS 재요청이 없다.
  }, [data, items]);
  return data;
}

function makeTemplateEngine(
  uiEvent: boolean,
  useData: (items: Item[]) => DataValue = useObjectData
) {
  return forwardRef<Scrollable, ListEngineProps>((p, ref) => {
    useNoopScrollable(ref);
    const { height } = useWindowDimensions();
    if (
      p.height !== 'fixed' ||
      !p.fixedHeight ||
      !['simple', 'heavy'].includes(p.cell)
    ) {
      throw new Error('템플릿 PoC는 고정 높이 simple/heavy 셀만 지원합니다.');
    }
    const rh = p.fixedHeight;
    const rows = p.bufferRows ?? 5;
    const n = Math.min(Math.ceil(height / rh) + 2 * rows, p.items.length);
    const indices = Array.from({ length: n }, (_, i) => i);
    const startupTrace = p.diagnostic === 'trace-startup';
    const startupRendered = useRef(false);
    if (startupTrace && !startupRendered.current) {
      startupRendered.current = true;
      console.log(`[ZlStartup] phase=render_begin wall=${Date.now()}`);
    }
    const data = useData(p.items);
    const startupReady = useSharedValue(false);
    useDerivedValue(() => {
      if (
        !startupTrace ||
        getRuntimeKind() !== RuntimeKind.UI ||
        startupReady.value
      )
        return;
      const source = data.value;
      const length = Array.isArray(source) ? source.length : source.id.length;
      if (length > 0) {
        startupReady.value = true;
        console.log(`[ZlStartup] phase=data_ready wall=${Date.now()}`);
      }
    });
    const binding = useSharedValue<Binding>({
      version: -1,
      encoded: indices.join(','),
      indices,
    });
    const trace = p.diagnostic === 'trace-binding';
    const onRecycleUI = useEvent<{ binds: string; version: number }>(
      (event) => {
        'worklet';
        if (event.version <= binding.value.version) return;
        if (trace)
          console.log(
            `[ZlBinding] phase=ui_receive version=${event.version} wall=${Date.now()}`
          );
        binding.value = {
          version: event.version,
          encoded: event.binds,
          indices: event.binds.split(',').map(Number),
        };
      },
      ['onRecycle']
    );
    const initialEncoded = indices.join(',');
    const props = useAnimatedProps(() => {
      // 첫 복원 중 발생한 재활용 요청은 binding에 남겨두되 아직 배치하지 않는다.
      // UI 데이터와 내용이 준비되는 같은 갱신에서 최신 매핑을 공개한다.
      if (getRuntimeKind() !== RuntimeKind.UI)
        return { committedBinds: initialEncoded, committedVersion: -1 };
      const source = data.value;
      const ready = Array.isArray(source)
        ? source.length > 0
        : source.id.length > 0;
      return ready
        ? {
            committedBinds: binding.value.encoded,
            committedVersion: binding.value.version,
          }
        : { committedBinds: initialEncoded, committedVersion: -1 };
    });
    return (
      <Pool
        style={styles.fill}
        animatedProps={props}
        preparationMode={0}
        preparationTrace={p.preparationTrace ?? false}
        count={p.items.length}
        rowHeight={rh}
        committedBinds={indices.join(',')}
        committedVersion={-1}
        overscan={rows}
        audit={p.audit ?? false}
        legacyRecycling={false}
        onRecycle={
          uiEvent
            ? onRecycleUI
            : (event: { nativeEvent: { binds: string; version: number } }) => {
                inst.cb();
                const { binds, version } = event.nativeEvent;
                if (trace)
                  console.log(
                    `[ZlBinding] phase=js_receive version=${version} wall=${Date.now()}`
                  );
                // shared value 비교와 대입을 UI 런타임에서 함께 처리한다.
                binding.modify((previous) => {
                  'worklet';
                  return version > previous.version
                    ? {
                        version,
                        encoded: binds,
                        indices: binds.split(',').map(Number),
                      }
                    : previous;
                });
              }
        }
      >
        {indices.map((slot) => (
          <Slot
            key={slot}
            slot={slot}
            initial={p.items[slot]!}
            data={data}
            binding={binding}
            rh={rh}
            heavy={p.cell === 'heavy'}
            audit={p.commonAudit ?? false}
          />
        ))}
      </Pool>
    );
  });
}
export const TemplateJSEngine = makeTemplateEngine(false);
export const TemplateWorkletEngine = makeTemplateEngine(true);
export const TemplateCompactEngine = makeTemplateEngine(true, useCompactData);
const styles = StyleSheet.create({
  fill: { flex: 1 },
  slot: { position: 'absolute', left: 0, right: 0 },
  row: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    justifyContent: 'center',
    gap: 8,
  },
  imageRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  flex: { flex: 1 },
  thumb: { width: 56, height: 56, borderRadius: 8, backgroundColor: '#ccc' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 2, marginTop: 6 },
  dot: { width: 18, height: 18, borderRadius: 4 },
});
