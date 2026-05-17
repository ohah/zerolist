import { forwardRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import ZlPoolList from '../../../specs/ZlPoolListNativeComponent';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';
import { inst } from '../instrument';
import { renderCell, useNoopScrollable } from './shared';

// ZeroList③ N3: POOL 개 슬롯(JSX, position:absolute)만 마운트. 네이티브
// (ZlPoolList)가 스크롤/플링 + Zig 로 windowStart 산출 후 매 프레임
// slot s 를 offsets[start+s]-scrollY 에 배치(JS 0). 경계 횡단 시에만
// onRecycle{start} → 여기서 slot s 내용을 data[start+s] 로 교체.
// 무한 스크롤되며 JS 작업은 리사이클 시에만(프레임 ≫ 리사이클). 측정 무효.
const POOL = 14;

export const ZigPoolEngine = forwardRef<Scrollable, ListEngineProps>(
  (p, ref) => {
    useNoopScrollable(ref);
    const rh = p.fixedHeight ?? 88;
    const Cell = renderCell(p);
    const [start, setStart] = useState(0);
    const data = p.items;
    return (
      <ZlPoolList
        count={data.length}
        rowHeight={rh}
        // 인라인 타입: codegen 이벤트 타입을 tsc 가 해석 못 함(앱-local
        // spec). spec 의 DirectEventHandler 가 단일 출처이고 여기선 그
        // 형태만 손으로 맞춘다(start: Double↔number).
        onRecycle={(e: { nativeEvent: { start: number } }) => {
          // JS-0 계측: ③ 의 JS 콜백은 스크롤마다가 아니라 경계 횡단시만.
          inst.cb();
          setStart(e.nativeEvent.start);
        }}
        style={styles.fill}
      >
        {Array.from({ length: Math.min(POOL, data.length) }, (_, s) => {
          const item = data[start + s];
          return (
            // collapsable=false: Fabric view-flattening 이 슬롯 래퍼를
            // 제거하면 호스트 직속 자식이 슬롯이 아닌 셀 내부뷰가 됨
            // → 슬롯 단위 네이티브 배치가 깨진다. 평탄화 비활성 필수.
            <View
              key={s}
              collapsable={false}
              style={[styles.slot, { height: rh }]}
            >
              {item ? Cell({ item }) : null}
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
