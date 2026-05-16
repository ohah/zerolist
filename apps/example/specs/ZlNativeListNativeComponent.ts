// app-local Fabric View 컴포넌트 spec — RN 내 네이티브 리스트
// 베이스라인(Fabric mount 오버헤드 분리). 네이티브가 RecyclerView/
// UICollectionView 로 셀을 직접 렌더, count 만 prop 으로 받는다.
import type { ViewProps } from 'react-native';
import type { Int32 } from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';

interface NativeProps extends ViewProps {
  count: Int32;
}

export default codegenNativeComponent<NativeProps>('ZlNativeList');
