// ZeroList③ 본질: 네이티브 스레드 Zig 가 JSX 셀 풀을 구동.
// JS 는 고정 풀 슬롯(children, position:absolute)을 1회 렌더,
// 네이티브가 각 슬롯 translationY 를 set(프레임당 JS 0). 슬롯 내용
// 변경(리사이클)만 React 가 처리. N1 = 풀 표시 + 네이티브 위치 유지.
import type { ViewProps } from 'react-native';
import type { Int32 } from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';

interface NativeProps extends ViewProps {
  count: Int32;
  rowHeight: Int32;
}

export default codegenNativeComponent<NativeProps>('ZlPoolList');
