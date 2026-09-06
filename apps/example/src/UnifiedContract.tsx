// 정량 실행과 분리한 실제 네이티브 화면의 상태·변경·스크롤 검증.
import { useEffect, useRef, useState } from 'react';
import { View, Text } from 'react-native';
import { ZeroList, type ZeroListHandle } from '@ohah/zerolist';
type Item = { id: number; label: string; height: number };
const initial = () =>
  Array.from({ length: 60 }, (_, id) => ({
    id,
    label: `항목 ${id}`,
    height: 100,
  }));
const fixed = (_: unknown, index: number) => ({
  length: 100,
  offset: 100 * index,
  index,
});
function Row({
  item,
  index,
  step,
}: {
  item: Item;
  index: number;
  step: string;
}) {
  const [value, setValue] = useState(0);
  const node = useRef<View>(null);
  useEffect(() => {
    if (step === '선택' && item.id === 0) setValue(1);
  }, [step, item.id]);
  useEffect(() => {
    const timer = setTimeout(
      () =>
        node.current?.measureInWindow((x, y, width, height) =>
          console.log(
            `[ZlContractRow] ${JSON.stringify({ step, id: item.id, index, value, x, y, width, height, label: item.label })}`
          )
        ),
      500
    );
    return () => clearTimeout(timer);
  }, [step, item, index, value]);
  return (
    <View
      ref={node}
      collapsable={false}
      style={{
        height: item.height,
        backgroundColor: index % 2 ? '#e1f2ed' : '#f1f5fa',
        padding: 14,
      }}
    >
      <Text
        style={{ fontSize: 22, color: '#14263b' }}
      >{`${item.label} / 위치 ${index} / 상태 ${value}`}</Text>
    </View>
  );
}
export function UnifiedContract() {
  const [data, setData] = useState(initial);
  const [step, setStep] = useState('초기');
  const [dynamic, setDynamic] = useState(false);
  const ref = useRef<ZeroListHandle<Item>>(null);
  useEffect(() => {
    const actions: [number, string, () => void][] = [
      [2000, '선택', () => {}],
      [4000, '재정렬', () => setData((p) => [p[1]!, p[0]!, ...p.slice(2)])],
      [
        6000,
        '앞 삽입',
        () => setData((p) => [{ id: 99, label: '새 항목', height: 100 }, ...p]),
      ],
      [
        8000,
        '내용 교체',
        () =>
          setData((p) =>
            p.map((x) => (x.id === 0 ? { ...x, label: '변경된 항목 0' } : x))
          ),
      ],
      [
        10000,
        '먼 항목 이동',
        () => ref.current?.scrollToIndex({ index: 30, animated: false }),
      ],
      [
        12000,
        '처음 이동',
        () => ref.current?.scrollToOffset({ offset: 0, animated: false }),
      ],
      [14000, '비우기', () => setData([])],
      [16000, '복원', () => setData(initial())],
      [
        18000,
        '동적 높이',
        () => {
          setDynamic(true);
          setData((p) => p.map((x, i) => ({ ...x, height: i % 2 ? 150 : 80 })));
        },
      ],
      [
        20000,
        '동적 크기 변경',
        () =>
          setData((p) =>
            p.map((x, i) => (i === 0 ? { ...x, height: 180 } : x))
          ),
      ],
    ];
    const timers = actions.map(([delay, name, action]) =>
      setTimeout(() => {
        setStep(name);
        action();
        console.log(`[ZlContract] step=${name}`);
      }, delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <View style={{ flex: 1, paddingTop: 55, backgroundColor: '#fff' }}>
      <Text style={{ fontSize: 22, height: 50, color: '#14263b' }}>
        ZeroList 통합 검증 · {step}
      </Text>
      <ZeroList
        ref={ref}
        style={{ flex: 1 }}
        data={data}
        renderItem={({ item, index }) => (
          <Row item={item} index={index} step={step} />
        )}
        getItemLayout={dynamic ? undefined : fixed}
        keyExtractor={(item) => String(item.id)}
        windowSize={2}
        initialNumToRender={10}
        estimatedItemSize={100}
        onScroll={(e) =>
          console.log(
            `[ZlContractScroll] step=${step} y=${e.nativeEvent.contentOffset.y}`
          )
        }
      />
    </View>
  );
}
