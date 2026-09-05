import { describe, it, expect, jest, afterEach } from '@jest/globals';
import { render, fireEvent, act } from '@testing-library/react-native';
import { ZigPoolEngine } from '../zigpool';
import type { ListEngineProps } from '../../types';

jest.mock('../../../../specs/ZlPoolListNativeComponent', () => {
  const React = require('react');
  const { View } = require('react-native');
  return (props: object) =>
    React.createElement(View, { ...props, testID: 'pool' });
});

const props: ListEngineProps = {
  items: Array.from({ length: 100 }, (_, id) => ({
    id,
    title: `#${id}`,
    body: '',
    height: 234,
    hue: 0,
  })),
  cell: 'simple',
  height: 'fixed',
  offsets: null,
  fixedHeight: 234,
};
const encoded = (first: number) =>
  Array.from({ length: 14 }, (_, i) => first + i).join(',');

afterEach(() => {
  jest.useRealTimers();
});

describe('ZigPool 내용과 배치 매핑의 커밋', () => {
  it('새 매핑과 실제 행 내용을 함께 반영하고 뒤늦게 온 이전 이벤트를 무시한다', () => {
    const view = render(<ZigPoolEngine {...props} legacyRecycling />);
    fireEvent(view.getByTestId('pool'), 'recycle', {
      nativeEvent: { binds: encoded(20), version: 2 },
    });
    expect(view.getByText('#20')).toBeTruthy();
    expect(view.queryByText('#0')).toBeNull();
    expect(view.getByTestId('pool').props.committedBinds).toBe(encoded(20));
    fireEvent(view.getByTestId('pool'), 'recycle', {
      nativeEvent: { binds: encoded(0), version: 1 },
    });
    expect(view.getByTestId('pool').props.committedBinds).toBe(encoded(20));
    expect(view.getByText('#20')).toBeTruthy();
    expect(view.queryByText('#0')).toBeNull();
  });

  it('반영 지연 중에는 이전 내용과 이전 매핑을 함께 유지한다', () => {
    jest.useFakeTimers();
    const view = render(
      <ZigPoolEngine {...props} legacyRecycling bindingDelayMs={120} />
    );
    fireEvent(view.getByTestId('pool'), 'recycle', {
      nativeEvent: { binds: encoded(20), version: 1 },
    });
    expect(view.getByText('#0')).toBeTruthy();
    expect(view.getByTestId('pool').props.committedBinds).toBe(encoded(0));
    act(() => jest.advanceTimersByTime(120));
    expect(view.queryByText('#0')).toBeNull();
    expect(view.getByText('#20')).toBeTruthy();
    expect(view.getByTestId('pool').props.committedBinds).toBe(encoded(20));
  });

  it('화면을 제거하면 아직 반영하지 않은 진단 타이머도 정리한다', () => {
    jest.useFakeTimers();
    const view = render(<ZigPoolEngine {...props} bindingDelayMs={400} />);
    fireEvent(view.getByTestId('pool'), 'recycle', {
      nativeEvent: { binds: encoded(20), version: 1 },
    });
    expect(jest.getTimerCount()).toBeGreaterThan(0);
    view.unmount();
    expect(jest.getTimerCount()).toBe(0);
  });
});

describe('내용 준비 PoC의 React 계약', () => {
  it('확대한 풀도 작은 데이터의 범위를 넘지 않고 커밋 버전을 내용과 함께 전달한다', () => {
    const view = render(
      <ZigPoolEngine
        {...props}
        items={props.items.slice(0, 4)}
        preparation="combined"
      />
    );
    expect(view.getByTestId('pool').props.committedBinds).toBe('0,1,2,3');
    fireEvent(view.getByTestId('pool'), 'recycle', {
      nativeEvent: { binds: '3,2,1,0', version: 7 },
    });
    expect(view.getByTestId('pool').props.committedVersion).toBe(7);
    expect(view.getByTestId('pool').props.committedBinds).toBe('3,2,1,0');
    expect(view.getByText('#3')).toBeTruthy();
  });

  it('슬롯을 메모화해도 같은 ID의 새 데이터와 새 콜백을 반영한다', () => {
    const view = render(<ZigPoolEngine {...props} preparation="memo" />);
    const onRender = jest.fn();
    const items = props.items.map((item) =>
      item.id === 0 ? { ...item, title: '#0 변경' } : item
    );
    view.rerender(
      <ZigPoolEngine
        {...props}
        items={items}
        preparation="memo"
        onRender={onRender}
      />
    );
    expect(view.getByText('#0 변경')).toBeTruthy();
    expect(view.queryByText('#0')).toBeNull();
    expect(onRender).toHaveBeenCalledWith(0);
  });
});
