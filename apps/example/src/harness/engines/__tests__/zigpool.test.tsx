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
