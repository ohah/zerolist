// Android 네이티브 스크롤 좌표·큰 인덱스·터치·크기 변경의 별도 검증 화면.
import { useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';
import { ZeroList, type ZeroListHandle } from '@ohah/zerolist';
type Item = { id: number };
function Row({
  item,
  index,
  height,
}: {
  item: Item;
  index: number;
  height: number;
}) {
  const [value, setValue] = useState(0);
  return (
    <View
      collapsable={false}
      style={{
        height,
        backgroundColor: index % 2 ? '#e1f2ed' : '#f1f5fa',
        padding: 14,
      }}
    >
      <Text
        testID={`pool-touch-${item.id}`}
        style={{ fontSize: 22, color: '#14263b' }}
        onPress={() => {
          setValue((v) => v + 1);
          console.log(
            `[ZlAndroidTouch] id=${item.id} index=${index} value=${value + 1}`
          );
        }}
      >{`항목 ${item.id} / 위치 ${index} / 선택 ${value}`}</Text>
    </View>
  );
}
export function AndroidPoolContract() {
  const [data, setData] = useState<Item[]>(() =>
    Array.from({ length: 100000 }, (_, id) => ({ id }))
  );
  const [height, setHeight] = useState(100);
  const [step, setStep] = useState('초기');
  const ref = useRef<ZeroListHandle<Item>>(null);
  useEffect(() => {
    const actions: [number, string, () => void][] = [
      [
        2000,
        '99980 이동 · 첫 행을 눌러 확인',
        () => ref.current?.scrollToIndex({ index: 99980, animated: false }),
      ],
      [6000, '먼 위치에서 앞 삽입', () => setData((p) => [{ id: -1 }, ...p])],
      [9000, '20개로 축소', () => setData((p) => p.slice(0, 20))],
      [
        12000,
        '처음 이동',
        () => ref.current?.scrollToOffset({ offset: 0, animated: false }),
      ],
      [15000, '고정 높이 140 변경', () => setHeight(140)],
      [
        18000,
        '끝으로 이동',
        () => ref.current?.scrollToEnd({ animated: false }),
      ],
    ];
    const timers = actions.map(([ms, name, fn]) =>
      setTimeout(() => {
        setStep(name);
        fn();
        console.log(`[ZlAndroidStep] ${name}`);
      }, ms)
    );
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <View style={{ flex: 1, paddingTop: 55, backgroundColor: '#fff' }}>
      <Text
        style={{ fontSize: 20, height: 60, color: '#14263b' }}
      >{`Android 좌표 검증 · ${step}`}</Text>
      <ZeroList
        ref={ref}
        style={{ flex: 1 }}
        data={data}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item, index }) => (
          <Row item={item} index={index} height={height} />
        )}
        getItemLayout={(_, index) => ({
          index,
          length: height,
          offset: height * index,
        })}
        initialNumToRender={10}
        windowSize={2}
        onScroll={(e) =>
          console.log(
            `[ZlAndroidScroll] step=${step} y=${e.nativeEvent.contentOffset.y}`
          )
        }
      />
    </View>
  );
}
