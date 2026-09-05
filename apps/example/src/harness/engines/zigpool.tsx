import {
  forwardRef,
  memo,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';
import { StyleSheet, View, useWindowDimensions } from 'react-native';
import ZlPoolList from '../../../specs/ZlPoolListNativeComponent';
import { Cell } from '../cells';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import { inst } from '../instrument';
import { useNoopScrollable } from './shared';

// React가 내용과 committedBinds를 같은 커밋으로 전달한다.
// 네이티브는 요청한 미래 인덱스 대신 실제 반영된 매핑으로 셀을 배치한다.
// 지연된 이벤트는 버전으로 거르고, 양방향 여유 셀로 역스크롤을 준비한다.
const POOL = 14;
// Cell 자체는 이미 memo다. 이 PoC는 슬롯 래퍼와 자식 element 생성만 분리한다.
const Slot = memo(function Slot({
  item,
  rh,
  cell,
  height,
  onMeasure,
  onRender,
  commonAudit,
}: {
  item: ListEngineProps['items'][number] | undefined;
  rh: number;
} & Pick<
  ListEngineProps,
  'cell' | 'height' | 'onMeasure' | 'onRender' | 'commonAudit'
>) {
  return (
    <View collapsable={false} style={[styles.slot, { height: rh }]}>
      {item ? (
        <Cell
          commonAudit={commonAudit}
          item={item}
          cell={cell}
          height={height}
          onMeasure={onMeasure}
          onRender={onRender}
        />
      ) : null}
    </View>
  );
});
const initBinds = (n: number) => Array.from({ length: n }, (_, i) => i);

export const ZigPoolEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    useNoopScrollable(ref);
    const rh = p.fixedHeight ?? 88;
    const data = p.items;
    const { height } = useWindowDimensions();
    const preparation = p.preparation ?? 'baseline';
    const adaptive = [
      'adaptive-small',
      'adaptive',
      'combined',
      'adaptive-stable',
      'combined-stable',
      'priority-stable',
      'pending-stable',
      'priority-pending-stable',
    ].includes(preparation);
    const coalesce = ['coalesce', 'combined', 'combined-stable'].includes(
      preparation
    );
    const memoSlots = ['memo', 'combined', 'combined-stable'].includes(
      preparation
    );
    const extra = [
      'wide',
      'adaptive',
      'combined',
      'adaptive-stable',
      'combined-stable',
    ].includes(preparation)
      ? 24
      : 10;
    const n = Math.min(
      p.bufferRows != null && p.bufferRows >= 0
        ? Math.ceil(height / rh) + 2 * p.bufferRows
        : p.legacyRecycling
          ? POOL
          : Math.max(POOL, Math.ceil(height / rh) + extra),
      data.length
    );
    const [binding, setBinding] = useState(() => ({
      version: -1,
      binds: initBinds(n),
    }));
    const binds = binding.binds;
    const traceBinding = p.diagnostic === 'trace-binding';
    if (traceBinding)
      console.log(
        `[ZlBinding] phase=render version=${binding.version} wall=${Date.now()}`
      );
    useLayoutEffect(() => {
      if (traceBinding)
        console.log(
          `[ZlBinding] phase=react_layout version=${binding.version} wall=${Date.now()}`
        );
    }, [binding.version, traceBinding]);
    const timers = useRef(new Set<ReturnType<typeof setTimeout>>());
    useEffect(() => {
      const pending = timers.current;
      return () => {
        for (const timer of pending) clearTimeout(timer);
        pending.clear();
      };
    }, []);
    return (
      <ZlPoolList
        preparationMode={
          (adaptive ? 1 : 0) |
          (coalesce ? 2 : 0) |
          (preparation.endsWith('-stable') ? 4 : 0) |
          (preparation.includes('pending') ? 8 : 0) |
          (preparation.startsWith('priority') ? 16 : 0)
        }
        preparationTrace={p.preparationTrace ?? false}
        committedVersion={binding.version}
        count={data.length}
        rowHeight={rh}
        committedBinds={binds.join(',')}
        overscan={
          p.bufferRows != null && p.bufferRows >= 0
            ? p.bufferRows
            : p.legacyRecycling
              ? 0
              : preparation === 'wide'
                ? 12
                : 5
        }
        legacyRecycling={p.legacyRecycling ?? false}
        audit={p.audit ?? false}
        // 인라인 타입: codegen 이벤트 타입을 tsc 가 해석 못 함(앱-local).
        onRecycle={(e: { nativeEvent: { binds: string; version: number } }) => {
          inst.cb(); // ③ JS 콜백 = binding 변경시만(스크롤 프레임 아님)
          if (p.diagnostic !== 'freeze-content') {
            const { binds: encoded, version } = e.nativeEvent;
            if (traceBinding)
              console.log(
                `[ZlBinding] phase=receive version=${version} wall=${Date.now()}`
              );
            const apply = () =>
              setBinding((previous) =>
                version > previous.version
                  ? { version, binds: encoded.split(',').map(Number) }
                  : previous
              );
            if (p.bindingDelayMs) {
              const timer = setTimeout(() => {
                timers.current.delete(timer);
                apply();
              }, p.bindingDelayMs);
              timers.current.add(timer);
            } else apply();
          }
        }}
        style={styles.fill}
      >
        {Array.from({ length: n }, (_, s) => {
          const item = data[binds[s] ?? s];
          if (memoSlots)
            return (
              <Slot
                commonAudit={p.commonAudit}
                key={s}
                item={item}
                rh={rh}
                cell={p.cell}
                height={p.height}
                onMeasure={p.onMeasure}
                onRender={p.onRender}
              />
            );
          return (
            <View
              key={s}
              collapsable={false}
              style={[styles.slot, { height: rh }]}
            >
              {item ? (
                <Cell
                  commonAudit={p.commonAudit}
                  item={item}
                  cell={p.cell}
                  height={p.height}
                  onMeasure={p.onMeasure}
                  onRender={p.onRender}
                />
              ) : null}
            </View>
          );
        })}
      </ZlPoolList>
    );
  }
);

const styles = StyleSheet.create({
  fill: { flex: 1 },
  slot: { position: 'absolute', left: 0, right: 0 },
});
