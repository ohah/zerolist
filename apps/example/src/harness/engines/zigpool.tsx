import { forwardRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import ZlPoolList from '../../../specs/ZlPoolListNativeComponent';
import { Cell } from '../cells';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import { inst } from '../instrument';
import { useNoopScrollable } from './shared';

// ZeroList③ #25: 네이티브가 slot↔dataIndex 의 단일 권위. POOL 슬롯은
// 고정 identity(key={s}, remount 없음). 네이티브가 스크롤·Zig 로
// binding 산출·자기배치(프레임당 JS 0). binding csv 변경시만 하달 →
// JS 는 **그대로 적용만**(자체 ring 파생 금지 = #24 의 JS-파생 desync
// 제거). slot s 내용 = data[binds[s]]; Cell(memo)라 바뀐 슬롯만 리렌더.
// 한계: 위치는 네이티브가 항상 정합하나, 내용은 이 setBinds 가 ~1
// 이벤트지연이라 빠른 플링 중 잠깐 직전 행이 보일 수 있다(at-rest
// 정합). 측정 무효(횟수 지표 전용, 시간 아님).
const POOL = 14;
const initBinds = (n: number) => Array.from({ length: n }, (_, i) => i);

export const ZigPoolEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    useNoopScrollable(ref);
    const rh = p.fixedHeight ?? 88;
    const data = p.items;
    const n = Math.min(POOL, data.length);
    const [binds, setBinds] = useState<number[]>(() => initBinds(n));
    return (
      <ZlPoolList
        count={data.length}
        rowHeight={rh}
        // 인라인 타입: codegen 이벤트 타입을 tsc 가 해석 못 함(앱-local).
        onRecycle={(e: { nativeEvent: { binds: string } }) => {
          inst.cb(); // ③ JS 콜백 = binding 변경시만(스크롤 프레임 아님)
          setBinds(e.nativeEvent.binds.split(',').map(Number));
        }}
        style={styles.fill}
      >
        {Array.from({ length: n }, (_, s) => {
          const item = data[binds[s] ?? s];
          return (
            <View
              key={s}
              collapsable={false}
              style={[styles.slot, { height: rh }]}
            >
              {item ? (
                <Cell
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
