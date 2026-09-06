// 초기 React 구조와 UI 워클릿이 공유하는, 상태 없는 읽기 전용 문자열 속성.
import type React from 'react';
import type { HostComponent, ViewProps } from 'react-native';
import type { Int32 } from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';
import { codegenNativeCommands } from 'react-native';
interface NativeProps extends ViewProps {
  content: string;
  kind: Int32;
}
type ComponentType = HostComponent<NativeProps>;
interface NativeCommands {
  updateContent: (
    viewRef: React.ElementRef<ComponentType>,
    content: string
  ) => void;
}
export const Commands = codegenNativeCommands<NativeCommands>({
  supportedCommands: ['updateContent'],
});
export default codegenNativeComponent<NativeProps>('ZlTemplateText');
