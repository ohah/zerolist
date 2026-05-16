import { describe, it, expect, jest } from '@jest/globals';
import { Text } from 'react-native';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { ZeroList } from '../list';

type Row = { id: number; label: string };
const make = (n: number): Row[] =>
  Array.from({ length: n }, (_, i) => ({ id: i, label: `row-${i}` }));

const layout = (testID: string, w: number, h: number) =>
  fireEvent(screen.getByTestId(testID), 'layout', {
    nativeEvent: { layout: { x: 0, y: 0, width: w, height: h } },
  });

const scrollTo = (testID: string, y: number) =>
  fireEvent.scroll(screen.getByTestId(testID), {
    nativeEvent: {
      contentOffset: { x: 0, y },
      contentSize: { width: 0, height: 0 },
      layoutMeasurement: { width: 0, height: 0 },
    },
  });

const renderRow = ({ item }: { item: Row }) => (
  <Text testID={`cell-${item.id}`}>{item.label}</Text>
);

describe('ZeroList — FlatList drop-in 동작', () => {
  it('초기 렌더: 빈 데이터면 ListEmptyComponent', () => {
    render(
      <ZeroList
        testID="zl"
        data={[]}
        renderItem={renderRow}
        ListEmptyComponent={<Text testID="empty">none</Text>}
      />
    );
    expect(screen.getByTestId('empty')).toBeTruthy();
  });

  it('header/footer 렌더 + 첫 화면 initialNumToRender 만큼 셀', () => {
    render(
      <ZeroList
        testID="zl"
        data={make(1000)}
        renderItem={renderRow}
        estimatedItemSize={100}
        initialNumToRender={8}
        ListHeaderComponent={<Text testID="hd">H</Text>}
        ListFooterComponent={<Text testID="ft">F</Text>}
      />
    );
    expect(screen.getByTestId('hd')).toBeTruthy();
    expect(screen.getByTestId('ft')).toBeTruthy();
    expect(screen.getByTestId('cell-0')).toBeTruthy();
    // 첫 스크롤 전 최소 initialNumToRender 보장
    expect(screen.getByTestId('cell-7')).toBeTruthy();
  });

  it('스크롤하면 윈도우가 이동해 먼 셀이 렌더된다', () => {
    render(
      <ZeroList
        testID="zl"
        data={make(1000)}
        renderItem={renderRow}
        estimatedItemSize={100}
        windowSize={1}
      />
    );
    layout('zl', 400, 500); // 뷰포트 500
    scrollTo('zl', 50_000); // 500행 근처
    expect(screen.getByTestId('cell-500')).toBeTruthy();
    expect(screen.queryByTestId('cell-0')).toBeNull();
  });

  it('keyExtractor 미지정 시 id 기반 키로 정상 렌더', () => {
    render(<ZeroList testID="zl" data={make(5)} renderItem={renderRow} />);
    expect(screen.getByTestId('cell-3')).toBeTruthy();
  });

  it('ItemSeparatorComponent 가 셀 사이에 들어간다', () => {
    render(
      <ZeroList
        testID="zl"
        data={make(3)}
        renderItem={renderRow}
        estimatedItemSize={50}
        ItemSeparatorComponent={() => <Text testID="sep">—</Text>}
      />
    );
    // 3개 중 마지막 제외 2개 구분자
    expect(screen.getAllByTestId('sep')).toHaveLength(2);
  });

  it('onEndReached: 끝 근처 스크롤 시 1회 발화', () => {
    const onEndReached = jest.fn();
    render(
      <ZeroList
        testID="zl"
        data={make(100)}
        renderItem={renderRow}
        estimatedItemSize={100}
        onEndReached={onEndReached}
        onEndReachedThreshold={0.5}
      />
    );
    layout('zl', 400, 500);
    scrollTo('zl', 9600); // content 10000, 끝까지 400 <= 0.5*500
    expect(onEndReached).toHaveBeenCalledTimes(1);
  });

  it('onViewableItemsChanged: 가시 토큰 보고', () => {
    const onVic = jest.fn<(i: { viewableItems: { key: string }[] }) => void>();
    render(
      <ZeroList
        testID="zl"
        data={make(100)}
        renderItem={renderRow}
        estimatedItemSize={100}
        onViewableItemsChanged={onVic}
      />
    );
    layout('zl', 400, 300);
    scrollTo('zl', 1000); // 행 10~12 가시
    expect(onVic).toHaveBeenCalled();
    const last = onVic.mock.calls.at(-1)![0];
    expect(last.viewableItems.some((t) => t.key === '10')).toBe(true);
  });

  it('numColumns: 행 그룹 렌더', () => {
    render(
      <ZeroList
        testID="zl"
        data={make(6)}
        renderItem={renderRow}
        numColumns={3}
        estimatedItemSize={50}
      />
    );
    expect(screen.getByTestId('cell-0')).toBeTruthy();
    expect(screen.getByTestId('cell-5')).toBeTruthy();
  });

  it('onScrollToIndexFailed: 범위 밖 index 면 발화', () => {
    const fail = jest.fn();
    const ref = { current: null as null | import('../list').ZeroListHandle };
    render(
      <ZeroList
        testID="zl"
        ref={ref as never}
        data={make(10)}
        renderItem={renderRow}
        estimatedItemSize={50}
        onScrollToIndexFailed={fail}
      />
    );
    ref.current!.scrollToIndex({ index: 999 });
    expect(fail).toHaveBeenCalledTimes(1);
    expect(fail.mock.calls[0]![0]).toMatchObject({ index: 999 });
  });

  it('ScrollView prop 패스스루: onMomentumScrollEnd 전달', () => {
    const onMom = jest.fn();
    render(
      <ZeroList
        testID="zl"
        data={make(20)}
        renderItem={renderRow}
        estimatedItemSize={50}
        onMomentumScrollEnd={onMom as never}
      />
    );
    fireEvent(screen.getByTestId('zl'), 'momentumScrollEnd', {
      nativeEvent: {
        contentOffset: { x: 0, y: 0 },
        contentSize: { width: 0, height: 0 },
        layoutMeasurement: { width: 0, height: 0 },
      },
    });
    expect(onMom).toHaveBeenCalled();
  });

  it('scrollToIndex viewPosition 지정해도 throw 안 함', () => {
    const ref = { current: null as null | import('../list').ZeroListHandle };
    render(
      <ZeroList
        testID="zl"
        ref={ref as never}
        data={make(50)}
        renderItem={renderRow}
        estimatedItemSize={100}
      />
    );
    expect(() =>
      ref.current!.scrollToIndex({ index: 25, viewPosition: 0.5 })
    ).not.toThrow();
  });

  it('imperative ref: scrollToOffset/Index/End 호출', () => {
    const ref = { current: null as null | import('../list').ZeroListHandle };
    render(
      <ZeroList
        testID="zl"
        ref={ref as never}
        data={make(50)}
        renderItem={renderRow}
        estimatedItemSize={100}
      />
    );
    expect(ref.current).not.toBeNull();
    // 호출이 throw 하지 않으면 OK(내부 ScrollView 위임)
    expect(() => {
      ref.current!.scrollToOffset({ offset: 500 });
      ref.current!.scrollToIndex({ index: 10 });
      ref.current!.scrollToEnd();
      ref.current!.flashScrollIndicators();
      ref.current!.recordInteraction();
    }).not.toThrow();
    expect(ref.current!.getScrollableNode()).toBeTruthy();
  });
});
