import { it, expect, jest } from '@jest/globals';
import { useState } from 'react';
import { Text } from 'react-native';
import { render, fireEvent, act } from '@testing-library/react-native';
import { ZeroList, type ZeroListHandle } from '../list';

jest.mock('../pool-host', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    __esModule: true,
    poolAvailable: true,
    default: React.forwardRef((p: object, ref: unknown) =>
      React.createElement(View, { ...p, ref })
    ),
  };
});
const make = (n: number) =>
  Array.from({ length: n }, (_, id) => ({ id, label: `row-${id}` }));
type Row = ReturnType<typeof make>[number];
const fixed = (_: unknown, index: number) => ({
  length: 100,
  offset: index * 100,
  index,
});
const draw = ({ item }: { item: Row }) => (
  <Text testID={`item-${item.id}`}>{item.label}</Text>
);
const defaults = {
  testID: 'unified',
  renderItem: draw,
  getItemLayout: fixed,
  initialNumToRender: 2,
  windowSize: 1,
};

it('같은 ZeroList API의 고정 높이 경로가 네이티브 풀을 구동한다', () => {
  const v = render(<ZeroList {...defaults} data={make(20)} />);
  expect(v.getByTestId('unified').props.committedBinds).toBe('0,1');
  fireEvent(v.getByTestId('unified'), 'recycle', {
    nativeEvent: { binds: '5,6', version: 2, dataVersion: 0 },
  });
  expect(v.getByTestId('item-5')).toBeTruthy();
  expect(v.queryByTestId('item-0')).toBeNull();
  fireEvent(v.getByTestId('unified'), 'recycle', {
    nativeEvent: { binds: '0,1', version: 1, dataVersion: 0 },
  });
  expect(v.getByTestId('item-5')).toBeTruthy();
});

it('슬롯이 다른 항목으로 바뀌면 이전 항목의 로컬 상태를 전달하지 않는다', () => {
  function Stateful({ item }: { item: Row }) {
    const [n, setN] = useState(0);
    return (
      <Text testID={`state-${item.id}`} onPress={() => setN(n + 1)}>
        {n}
      </Text>
    );
  }
  const v = render(
    <ZeroList
      {...defaults}
      data={make(10)}
      renderItem={({ item }) => <Stateful item={item} />}
    />
  );
  fireEvent.press(v.getByTestId('state-0'));
  fireEvent(v.getByTestId('unified'), 'recycle', {
    nativeEvent: { binds: '2,3', version: 1, dataVersion: 0 },
  });
  expect(v.getByTestId('state-2').props.children).toBe(0);
  expect(v.queryByTestId('state-0')).toBeNull();
});

it('재정렬 시 살아 있는 항목의 상태는 같은 슬롯에서 보존한다', () => {
  function Stateful({ item }: { item: Row }) {
    const [n, setN] = useState(0);
    return (
      <Text testID={`state-${item.id}`} onPress={() => setN(n + 1)}>
        {n}
      </Text>
    );
  }
  const data = make(2);
  const renderItem = ({ item }: { item: Row }) => <Stateful item={item} />;
  const v = render(
    <ZeroList {...defaults} data={data} renderItem={renderItem} />
  );
  fireEvent.press(v.getByTestId('state-0'));
  v.rerender(
    <ZeroList
      {...defaults}
      data={[data[1]!, data[0]!]}
      renderItem={renderItem}
    />
  );
  expect(v.getByTestId('state-0').props.children).toBe(1);
  expect(v.getByTestId('unified').props.committedBinds).toBe('1,0');
});

it('새 데이터 이후 오래된 네이티브 이벤트와 오래된 JS 핸들러를 거부한다', () => {
  const data = make(10);
  const v = render(<ZeroList {...defaults} data={data} />);
  const old = v.getByTestId('unified').props.onRecycle;
  v.rerender(<ZeroList {...defaults} data={data.slice(1)} />);
  const epoch = v.getByTestId('unified').props.dataVersion;
  fireEvent(v.getByTestId('unified'), 'recycle', {
    nativeEvent: { binds: '5,6', version: 99, dataVersion: 0 },
  });
  act(() =>
    old({ nativeEvent: { binds: '5,6', version: 100, dataVersion: epoch } })
  );
  expect(v.getByTestId('item-1')).toBeTruthy();
  expect(v.queryByTestId('item-6')).toBeNull();
});

it('빈 데이터·재삽입·같은 키의 새 내용·extraData를 반영한다', () => {
  const data = make(2);
  let selected = 0;
  const renderItem = ({ item }: { item: Row }) => (
    <Text testID={`item-${item.id}`}>{`${item.label}:${selected}`}</Text>
  );
  const v = render(
    <ZeroList
      {...defaults}
      data={data}
      renderItem={renderItem}
      extraData={selected}
    />
  );
  selected = 1;
  v.rerender(
    <ZeroList
      {...defaults}
      data={[{ ...data[0]!, label: 'changed' }, data[1]!]}
      renderItem={renderItem}
      extraData={selected}
    />
  );
  expect(v.getByTestId('item-0').props.children).toBe('changed:1');
  v.rerender(<ZeroList {...defaults} data={[]} />);
  expect(v.queryByTestId('item-0')).toBeNull();
  v.rerender(<ZeroList {...defaults} data={data} />);
  expect(v.getByTestId('item-0')).toBeTruthy();
});

it('잘못된 인덱스·중복·누락 매핑은 현재 내용을 변경하지 않는다', () => {
  const v = render(<ZeroList {...defaults} data={make(10)} />);
  for (const binds of ['0,0', '0,100', '0', 'NaN,1', '-1,1'])
    fireEvent(v.getByTestId('unified'), 'recycle', {
      nativeEvent: { binds, version: 3, dataVersion: 0 },
    });
  expect(v.getByTestId('unified').props.committedBinds).toBe('0,1');
});

it('스크롤 ref와 끝 도달 콜백이 실제 네이티브 요청에 연결된다', () => {
  const ref = { current: null as ZeroListHandle<Row> | null };
  const onEnd = jest.fn();
  const onScroll = jest.fn();
  const v = render(
    <ZeroList
      {...defaults}
      ref={ref}
      data={make(10)}
      onEndReached={onEnd}
      onScroll={onScroll}
    />
  );
  fireEvent(v.getByTestId('unified'), 'layout', {
    nativeEvent: { layout: { width: 400, height: 200 } },
  });
  act(() =>
    ref.current!.scrollToIndex({ index: 5, viewPosition: 0.5, animated: false })
  );
  expect(v.getByTestId('unified').props.scrollCommand).toMatch(/,450,0$/);
  act(() => ref.current!.scrollToEnd({ animated: false }));
  expect(v.getByTestId('unified').props.scrollCommand).toMatch(/,800,0$/);
  for (let i = 0; i < 2; i++)
    fireEvent(v.getByTestId('unified'), 'poolScroll', {
      nativeEvent: { offset: 800, viewport: 200 },
    });
  expect(onEnd).toHaveBeenCalledTimes(1);
  expect(onScroll).toHaveBeenLastCalledWith(
    expect.objectContaining({
      nativeEvent: expect.objectContaining({ contentOffset: { x: 0, y: 800 } }),
    })
  );
});

it('동적 높이·헤더·가시성·ScrollView 추가 기능은 기존 동작을 유지한다', () => {
  for (const extra of [
    { getItemLayout: undefined },
    { ListHeaderComponent: <Text>header</Text> },
    { onViewableItemsChanged: () => {} },
    { horizontal: true },
    { onMomentumScrollEnd: () => {} },
  ]) {
    const v = render(<ZeroList {...defaults} data={make(4)} {...extra} />);
    expect(v.getByTestId('unified').props.committedBinds).toBeUndefined();
    v.unmount();
  }
});

it('onScroll 구독이 없어도 데이터 갱신 시 마지막 준비 창을 유지한다', () => {
  const data = make(100);
  const v = render(<ZeroList {...defaults} data={data} />);
  fireEvent(v.getByTestId('unified'), 'recycle', {
    nativeEvent: { binds: '50,51', version: 1, dataVersion: 0 },
  });
  v.rerender(<ZeroList {...defaults} data={data.map((x) => ({ ...x }))} />);
  expect(v.getByTestId('item-50')).toBeTruthy();
  expect(v.queryByTestId('item-0')).toBeNull();
});

it('공개 API의 기본 스크롤바와 명시적 숨김을 네이티브에 전달한다', () => {
  const data = make(10);
  const v = render(<ZeroList {...defaults} data={data} />);
  expect(v.getByTestId('unified').props.scrollIndicator).toBe(1);
  v.rerender(
    <ZeroList {...defaults} data={data} showsVerticalScrollIndicator={false} />
  );
  expect(v.getByTestId('unified').props.scrollIndicator).toBe(0);
});
