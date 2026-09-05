import { forwardRef, useEffect } from 'react';
import { Image, StyleSheet, View, useWindowDimensions } from 'react-native';
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

// WishList의 템플릿 발상을 현재 RN/Worklets API로 검증하는 별도 PoC.
// React는 구조를 한 번 만들고, UI 런타임이 이미 존재하는 네이티브 속성을 갱신한다.
// 일반 Text children, 임의 renderItem, 동적 높이를 지원하는 drop-in API가 아니다.
const Pool = Animated.createAnimatedComponent(ZlPoolList);
const NativeText = Animated.createAnimatedComponent(ZlTemplateText);
const IMG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAFklEQVR4nGNgYGD4z4AHMA4qAQAB/wQEZxJ3HQAAAABJRU5ErkJggg==';
const DOTS = Array.from({ length: 64 }, (_, i) => i);
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
  data: SharedValue<Item[]>;
  initial: Item;
  rh: number;
  heavy: boolean;
  audit: boolean;
}) {
  // 다른 슬롯만 바뀌면 같은 index 이후의 무거운 계산을 반복하지 않는다.
  const index = useDerivedValue(() => binding.value.indices[slot] ?? slot);
  const item = useDerivedValue(() => data.value[index.value] ?? initial);
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
function makeTemplateEngine(uiEvent: boolean) {
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
    // 비교하는 두 템플릿 모두 같은 실제 데이터 사본을 UI 런타임에 전달한다.
    const data = useSharedValue(p.items);
    const binding = useSharedValue<Binding>({
      version: -1,
      encoded: indices.join(','),
      indices,
    });
    useEffect(() => {
      data.value = p.items;
    }, [data, p.items]);
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
    const props = useAnimatedProps(() => ({
      committedBinds: binding.value.encoded,
      committedVersion: binding.value.version,
    }));
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
