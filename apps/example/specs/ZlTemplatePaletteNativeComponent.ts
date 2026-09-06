import type React from 'react';
import type { HostComponent, ViewProps } from 'react-native';
import type { Double } from 'react-native/Libraries/Types/CodegenTypes';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';
import { codegenNativeCommands } from 'react-native';
interface NativeProps extends ViewProps {
  hue: Double;
}
type ComponentType = HostComponent<NativeProps>;
interface NativeCommands {
  updateHue: (viewRef: React.ElementRef<ComponentType>, hue: Double) => void;
}
export const Commands = codegenNativeCommands<NativeCommands>({
  supportedCommands: ['updateHue'],
});
export default codegenNativeComponent<NativeProps>('ZlTemplatePalette');
