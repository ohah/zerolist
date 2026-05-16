// ZeroList③ 본질: 네이티브 스레드 Zig 가 JSX 셀 풀을 구동.
// JS 는 고정 풀 슬롯(children, position:absolute)을 렌더, 네이티브가
// 스크롤·가시범위·배치를 매 프레임 처리(JS 0). 리사이클 경계를
// 넘을 때만 onRecycle{start} 1회 → JS 가 슬롯 내용만 갱신(N3).
import type { ViewProps } from 'react-native';
import type {
  Double,
  DirectEventHandler,
  Int32,
} from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';

interface NativeProps extends ViewProps {
  count: Int32;
  rowHeight: Int32;
  // 풀 윈도우 시작 데이터 인덱스가 바뀔 때만(경계 횡단) 발신.
  onRecycle?: DirectEventHandler<Readonly<{ start: Double }>> | null;
}

export default codegenNativeComponent<NativeProps>('ZlPoolList');
