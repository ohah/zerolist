import { describe, it, expect, jest } from '@jest/globals';
import { retainMeasurements } from '../measurements';

describe('키 기반 동적 크기 캐시', () => {
  it('순서가 바뀌어도 같은 키의 측정값과 0 크기를 유지하고 삭제된 키를 회수한다', () => {
    const previous = new Map([
      ['a', 300],
      ['b', 0],
      ['removed', 999],
    ]);
    const keys = ['b', 'new', 'a'];
    const next = retainMeasurements(previous, keys.length, (i) => keys[i]!);
    expect([...next]).toEqual([
      ['b', 0],
      ['a', 300],
    ]);
    expect(previous.size).toBe(3);
  });
  it('데이터가 비면 측정 캐시도 비운다', () => {
    expect(retainMeasurements(new Map([['a', 100]]), 0, String).size).toBe(0);
  });
  it('측정이 없거나 앞부분 측정만 있는 10만 건 추가에서 불필요하게 끝까지 순회하지 않는다', () => {
    const keyOf = jest.fn((i: number) => String(i));
    retainMeasurements(new Map(), 100000, keyOf);
    expect(keyOf).not.toHaveBeenCalled();
    retainMeasurements(
      new Map([
        ['0', 50],
        ['1', 70],
      ]),
      100000,
      keyOf
    );
    expect(keyOf).toHaveBeenCalledTimes(2);
  });
});
