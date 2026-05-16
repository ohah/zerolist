import { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import { jsRef } from '@ohah/zerolist';
import { ENGINES } from './harness/engines';
import { makeItems } from './harness/data';
import type { CellType, EngineId } from './harness/types';

// chrome-free 측정 루트 — harness UI(헤더/Seg/Run) 없이 선택된 엔진만
// 풀스크린 렌더. engine/count/cell 은 SoloActivity 가 intent extra →
// initialProps 로 주입. gfxinfo(프로세스 단위)가 엔진+RN루트+Fabric
// mount 만 보게 해 Native(맨 Activity)와 깨끗하게 비교(태스크 #18).
export default function Solo(props: {
  engine?: string;
  count?: number;
  cell?: string;
}) {
  const engineId = (props.engine ?? 'flatlist') as EngineId;
  const count = Number(props.count ?? 20000);
  const cell = (props.cell ?? 'complex') as CellType;
  const Engine = ENGINES[engineId];

  const items = useMemo(() => makeItems(count, 'fixed'), [count]);
  const offsets = useMemo(() => {
    const hs = new Float32Array(items.length);
    for (let i = 0; i < items.length; i++) hs[i] = items[i]!.height;
    const o = new Float64Array(items.length + 1);
    jsRef.buildOffsets(hs, o);
    return o;
  }, [items]);
  const fixedHeight = items[0]?.height ?? null;

  if (!Engine) return <View style={s.fill} />;
  return (
    <View style={s.fill}>
      <Engine
        items={items}
        cell={cell}
        height="fixed"
        offsets={offsets}
        fixedHeight={fixedHeight}
      />
    </View>
  );
}

const s = StyleSheet.create({ fill: { flex: 1 } });
