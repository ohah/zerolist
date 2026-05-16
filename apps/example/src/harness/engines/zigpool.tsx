import { forwardRef } from 'react';
import { StyleSheet, View } from 'react-native';
import ZlPoolList from '../../../specs/ZlPoolListNativeComponent';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import { renderCell, useNoopScrollable } from './shared';

// ZeroList③ N2: 고정 풀 슬롯(JSX, position:absolute)을 1회 렌더,
// 네이티브(ZlPoolList)가 네이티브 스크롤/플링 + Zig 가시범위로 매
// 프레임 각 슬롯 translationY 를 set(JS 0). 리사이클은 N3 — 아직
// 슬롯 i = 데이터 i 고정이라 풀(POOL) 넘어가면 빈다. 측정 무효.
const POOL = 14;

export const ZigPoolEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    useNoopScrollable(ref);
    const rh = p.fixedHeight ?? 88;
    const Cell = renderCell(p);
    const slots = p.items.slice(0, POOL);
    return (
      <ZlPoolList count={p.items.length} rowHeight={rh} style={styles.fill}>
        {slots.map((item, i) => (
          // collapsable=false: Fabric view-flattening 이 슬롯 래퍼를
          // 제거하면 호스트 직속 자식이 슬롯이 아닌 셀 내부뷰가 됨
          // → 슬롯 단위 네이티브 배치가 깨진다. 평탄화 비활성 필수.
          <View
            key={i}
            collapsable={false}
            style={[styles.slot, { height: rh }]}
          >
            {Cell({ item })}
          </View>
        ))}
      </ZlPoolList>
    );
  }
);

const styles = StyleSheet.create({
  fill: { flex: 1 },
  slot: { position: 'absolute', left: 0, right: 0 },
});
