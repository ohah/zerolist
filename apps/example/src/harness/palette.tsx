import { View } from 'react-native';

// 웹은 네이티브 장식 통합 실험 대상이 아니다. 기존 뷰 구조로 표시한다.
export function PaletteDecoration({ hue }: { hue: number }) {
  return (
    <View
      style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 2, marginTop: 6 }}
    >
      {Array.from({ length: 64 }, (_, i) => (
        <View
          key={i}
          style={{
            width: 18,
            height: 18,
            borderRadius: 4,
            backgroundColor: `hsl(${hue + i * 5}, 60%, 70%)`,
          }}
        />
      ))}
    </View>
  );
}
