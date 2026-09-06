import { useWindowDimensions } from 'react-native';
import NativePalette from '../../specs/ZlTemplatePaletteNativeComponent';

export function PaletteDecoration({ hue }: { hue: number }) {
  const { width } = useWindowDimensions();
  const columns = Math.max(1, Math.floor((width - 28 + 2) / 20));
  return (
    <NativePalette
      hue={hue}
      style={{ height: Math.ceil(64 / columns) * 20 - 2, marginTop: 6 }}
    />
  );
}
