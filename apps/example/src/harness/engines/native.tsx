import { forwardRef, useImperativeHandle } from 'react';
import { StyleSheet } from 'react-native';
import ZlNativeList from '../../../specs/ZlNativeListNativeComponent';
import type { ListEngineProps } from '../types';
import type { Scrollable } from '../flingDriver';

// RN 내 Fabric 호스트 네이티브 리스트(베이스라인). 네이티브가
// RecyclerView 로 셀을 직접 렌더 — 순수 Native 와 동일 셀.
// 주의: 스크롤은 네이티브 내부 처리 → onScrollY/onRender 미호출이라
// in-app Run/logRow(valid 게이트) 경로는 이 엔진에 무의미. 권위 있는
// 측정은 gfxinfo/Maestro 경로뿐. gfxinfo 는 프로세스 단위라 이 수치는
// harness chrome+RN런타임 포함 — 깨끗한 Fabric-mount 분리는 태스크 #18.
export const NativeFabricEngine = forwardRef<Scrollable, ListEngineProps>(
  ({ items }, ref) => {
    useImperativeHandle(ref, () => ({ scrollToOffset: () => {} }));
    return <ZlNativeList count={items.length} style={styles.fill} />;
  }
);

const styles = StyleSheet.create({ fill: { flex: 1 } });
