// ZeroList③ 본질(#25): 네이티브 스레드 Zig 가 JSX 셀 풀을 구동.
// JS 는 고정 풀 슬롯(children, position:absolute)을 렌더, 네이티브가
// 스크롤·가시범위·배치를 처리(프레임당 JS 0). 네이티브가 slot↔
// dataIndex 의 단일 권위 — windowStart 변경시만 onRecycle{binds}
// (csv) 하달 → JS 는 그대로 적용(자체 파생 금지 = #24 desync 제거).
import type { ViewProps } from 'react-native';
import type {
  DirectEventHandler,
  Int32,
} from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';

interface NativeProps extends ViewProps {
  count: Int32;
  rowHeight: Int32;
  // #25: 네이티브가 slot↔dataIndex 의 단일 권위. binding 이 바뀔 때만
  // csv(슬롯 s → 데이터인덱스, 콤마구분) 하달 → JS 는 *적용만*(자체
  // ring 파생 금지 = #24 desync 원인). codegen-안전한 string 페이로드.
  onRecycle?: DirectEventHandler<Readonly<{ binds: string }>> | null;
}

export default codegenNativeComponent<NativeProps>('ZlPoolList');
