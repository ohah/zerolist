import { forwardRef } from 'react';
import { StyleSheet, View } from 'react-native';
import ZlPoolList from '../../../specs/ZlPoolListNativeComponent';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import { renderCell, useNoopScrollable } from './shared';

// ZeroList③ N1: 고정 풀 슬롯(JSX, position:absolute)을 1회 렌더,
// 네이티브(ZlPoolList)가 각 슬롯 translationY 를 set. 아직 스크롤·
// 리사이클 없음 — JSX 셀이 Fabric 호스트 안에서 보이고 네이티브
// 위치가 적용/유지되는지(N1 리스크) 검증용. 측정 무효(스크롤 없음).
// N1 한정 임의 풀 크기(스크롤 없어 뷰포트 무관). N2 에서 동적화.
const POOL = 14;

export const ZigPoolEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    useNoopScrollable(ref);
    const rh = p.fixedHeight ?? 88;
    const Cell = renderCell(p);
    const slots = p.items.slice(0, POOL);
    return (
      <ZlPoolList rowHeight={rh} style={styles.fill}>
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
