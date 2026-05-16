import ZlZigList from '../../../specs/ZlZigListNativeComponent';
import { makeNativeHostEngine } from './shared';

// ZeroList③ 아키텍처 PoC. 네이티브가 RecyclerView 를 렌더하되 가시범위
// 결정을 네이티브 스크롤 스레드에서 Zig(JNI zero-copy)로 계산 —
// 프레임당 JS 0. 셀은 native 베이스라인과 동일(공정 비교).
// 주의: native 와 같이 onScrollY/onRender 미호출(in-app valid 게이트
// 무의미). 성능 미검증(PoC). rowHeight 88 = NativeList.kt dp(88) 와 일치.
export const NativeZigEngine = makeNativeHostEngine(ZlZigList, (p) => ({
  count: p.items.length,
  rowHeight: p.fixedHeight ?? 88,
}));
