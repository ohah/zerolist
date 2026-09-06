import { AndroidPoolContract } from './AndroidPoolContract';
import { UnifiedContract } from './UnifiedContract';
import { useEffect, useMemo } from 'react';
import { View, StyleSheet, useWindowDimensions, Platform } from 'react-native';
import { jsRef } from '@ohah/zerolist';
import { ENGINES } from './harness/engines';
import { makeItems } from './harness/data';
import { fixedCellHeight } from './harness/cellLayout';
import { inst } from './harness/instrument';
import type { CellType, EngineId, Preparation } from './harness/types';

// chrome-free 측정 루트 — harness UI(헤더/Seg/Run) 없이 선택된 엔진만
// 풀스크린 렌더. engine/count/cell 은 SoloActivity 가 intent extra →
// initialProps 로 주입. gfxinfo(프로세스 단위)가 엔진+RN루트+Fabric
// mount 만 보게 해 Native(맨 Activity)와 깨끗하게 비교(태스크 #18).
export default function Solo(props: {
  bufferRows?: number;
  commonAudit?: boolean;
  jsBlockMs?: number;
  preparation?: Preparation;
  preparationTrace?: boolean;
  engine?: string;
  count?: number;
  cell?: string;
  diagnostic?:
    | 'unified-contract'
    | 'normal'
    | 'freeze-content'
    | 'freeze-position'
    | 'trace-binding'
    | 'trace-startup';
  legacyRecycling?: boolean;
  audit?: boolean;
  bindingDelayMs?: number;
}) {
  const engineId = (props.engine ?? 'flatlist') as EngineId;
  const count = Number(props.count ?? 20000);
  const cell = (props.cell ?? 'complex') as CellType;
  const Engine = ENGINES[engineId];

  const { width, fontScale } = useWindowDimensions();
  const rowHeight = fixedCellHeight(cell, width, fontScale);
  const items = useMemo(
    () => makeItems(count, 'fixed', rowHeight),
    [count, rowHeight]
  );
  const offsets = useMemo(() => {
    const hs = new Float32Array(items.length);
    for (let i = 0; i < items.length; i++) hs[i] = items[i]!.height;
    const o = new Float64Array(items.length + 1);
    jsRef.buildOffsets(hs, o);
    return o;
  }, [items]);
  const fixedHeight = items[0]?.height ?? null;

  // 설치된 네이티브 코어 버전을 측정 시작 전에 확인한다.
  useEffect(() => {
    const v = Platform.constants.reactNativeVersion;
    console.log(`[ZlRuntime] rn=${v.major}.${v.minor}.${v.patch}`);
  }, []);

  // JS-0 정량 계측: 결정적 스크롤에서 renders/cbs 누적을 주기 로깅.
  useEffect(() => inst.start(engineId), [engineId]);

  // 지연 타이머와 별도로 JS 스레드가 실제로 점유되는 부하 조건이다.
  useEffect(() => {
    const duration = Math.min(400, Math.max(0, props.jsBlockMs ?? 0));
    if (!duration) return;
    const timer = setInterval(() => {
      const start = performance.now();
      while (performance.now() - start < duration) {
        /* 측정용 CPU 점유 */
      }
      if (props.preparationTrace)
        console.log(`[ZlBlock] elapsed=${performance.now() - start}`);
    }, duration + 40);
    return () => clearInterval(timer);
  }, [props.jsBlockMs, props.preparationTrace]);

  if (props.diagnostic === 'android-pool-contract')
    return <AndroidPoolContract />;
  if (props.diagnostic === 'unified-contract') return <UnifiedContract />;
  if (!Engine) return <View style={s.fill} />;
  return (
    <View style={s.fill}>
      <Engine
        bufferRows={props.bufferRows}
        commonAudit={props.commonAudit}
        preparation={props.preparation}
        preparationTrace={props.preparationTrace}
        diagnostic={props.diagnostic}
        legacyRecycling={props.legacyRecycling}
        audit={props.audit}
        bindingDelayMs={props.bindingDelayMs}
        items={items}
        cell={cell}
        height="fixed"
        offsets={offsets}
        fixedHeight={fixedHeight}
        onRender={inst.render}
        onScrollY={inst.cb}
      />
    </View>
  );
}

const s = StyleSheet.create({ fill: { flex: 1 } });
