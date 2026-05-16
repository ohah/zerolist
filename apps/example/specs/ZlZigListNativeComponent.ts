// ZeroList③ 아키텍처 PoC 의 Fabric View spec.
// JS 는 count/rowHeight 만 넘기고, 네이티브가 RecyclerView 를 렌더하되
// **가시범위 결정을 네이티브 스크롤 스레드에서 Zig(JNI)로 계산**한다
// (프레임당 JS 0). 본질 데이터 경로 검증용 — 성능은 미검증(PoC).
import type { ViewProps } from 'react-native';
import type { Int32 } from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';

interface NativeProps extends ViewProps {
  count: Int32;
  rowHeight: Int32;
}

export default codegenNativeComponent<NativeProps>('ZlZigList');
