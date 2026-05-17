import { memo, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  type LayoutChangeEvent,
} from 'react-native';
import type { Item, CellType, HeightMode } from './types';
import { inst } from './instrument';

// 결정론적 데이터-URI 이미지(네트워크 비결정성 제거). 실제 대용량
// 사진 디코드 비용은 별도 축 — 여기선 Image 파이프라인/레이아웃 비용.
const IMG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAFklEQVR4nGNgYGD4z4AHMA4qAQAB/wQEZxJ3HQAAAABJRU5ErkJggg==';

function hsl(h: number, l = 70) {
  return `hsl(${h}, 60%, ${l}%)`;
}

interface Props {
  item: Item;
  cell: CellType;
  height: HeightMode;
  onMeasure?: (id: number, h: number) => void;
  onRender?: (id: number) => void;
}

const DOTS = Array.from({ length: 64 }, (_, i) => i);
const HEAVY_ITERS = 4000; // 셀당 동기 연산 부하 (변별용 코스트 knob)

// 무거운 셀: 렌더마다 동기 연산 + 64 서브뷰 + 이미지. 실제 무거운
// 앱의 행을 모사 — 재활용/재렌더 비용을 표면화한다.
function HeavyCell({ item }: { item: Item }) {
  let acc = 0;
  for (let i = 0; i < HEAVY_ITERS; i++)
    acc += Math.sqrt((i * (item.id + 1)) % 97);
  return (
    <>
      <View style={styles.imageRow}>
        <Image source={{ uri: IMG }} style={styles.thumb} />
        <View style={styles.flex}>
          <Text style={styles.title} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.body}>{item.body}</Text>
          <Text style={styles.body}>∑={acc.toFixed(1)}</Text>
        </View>
      </View>
      <View style={styles.grid}>
        {DOTS.map((d) => (
          <View
            key={d}
            style={[styles.dot, { backgroundColor: hsl(item.hue + d * 5) }]}
          />
        ))}
      </View>
    </>
  );
}

function CellInner({ item, cell, height, onMeasure, onRender }: Props) {
  onRender?.(item.id); // 실제 렌더 검증(측정 유효성)
  // 카운트 지표: 셀 인스턴스 mount/unmount churn(시간 아님). ③ 고정
  // 풀 = 초기 후 ≈0, FlatList = 스크롤 따라 생성/파괴.
  useEffect(() => {
    inst.mount();
    return () => inst.unmount();
  }, []);
  // fixed/variable 는 사전 확정 높이를 강제, dynamic 은 콘텐츠가 결정.
  const sized = height !== 'dynamic';
  const onLayout =
    height === 'dynamic' && onMeasure
      ? (e: LayoutChangeEvent) =>
          onMeasure(item.id, e.nativeEvent.layout.height)
      : undefined;

  const style = [
    styles.row,
    { backgroundColor: hsl(item.hue, 92) },
    sized ? { height: item.height } : null,
  ];

  if (cell === 'simple') {
    return (
      <View style={style} onLayout={onLayout}>
        <Text style={styles.title} numberOfLines={1}>
          {item.title}
        </Text>
      </View>
    );
  }

  if (cell === 'image') {
    return (
      <View style={[style, styles.imageRow]} onLayout={onLayout}>
        <Image source={{ uri: IMG }} style={styles.thumb} />
        <View style={styles.flex}>
          <Text style={styles.title} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.body} numberOfLines={2}>
            {item.body}
          </Text>
        </View>
      </View>
    );
  }

  if (cell === 'heavy') {
    return (
      <View style={[style, styles.complex]} onLayout={onLayout}>
        <HeavyCell item={item} />
      </View>
    );
  }

  return (
    <View style={[style, styles.complex]} onLayout={onLayout}>
      <View style={styles.imageRow}>
        <Image source={{ uri: IMG }} style={styles.thumb} />
        <View style={styles.flex}>
          <Text style={styles.title} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.body}>{item.body}</Text>
        </View>
      </View>
      <View style={styles.tags}>
        {[0, 1, 2].map((t) => (
          <View
            key={t}
            style={[styles.tag, { backgroundColor: hsl(item.hue + t * 40) }]}
          >
            <Text style={styles.tagText}>tag{t}</Text>
          </View>
        ))}
        <View style={styles.btn}>
          <Text style={styles.btnText}>open</Text>
        </View>
      </View>
    </View>
  );
}

export const Cell = memo(CellInner);

const styles = StyleSheet.create({
  row: { paddingHorizontal: 14, paddingVertical: 10, justifyContent: 'center' },
  imageRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  complex: { gap: 8 },
  flex: { flex: 1 },
  thumb: { width: 56, height: 56, borderRadius: 8, backgroundColor: '#ccc' },
  title: { fontSize: 15, fontWeight: '700', color: '#111' },
  body: { fontSize: 13, color: '#444', marginTop: 2 },
  tags: { flexDirection: 'row', gap: 6, alignItems: 'center' },
  tag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10 },
  tagText: { fontSize: 11, color: '#222' },
  btn: {
    marginLeft: 'auto',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: '#222',
  },
  btnText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 2, marginTop: 6 },
  dot: { width: 18, height: 18, borderRadius: 4 },
});
