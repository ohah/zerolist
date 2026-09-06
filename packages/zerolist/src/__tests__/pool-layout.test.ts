import { it, expect } from '@jest/globals';
import { uniformLength, reconcileSlots } from '../pool-layout';
it('끝부분의 비균일 높이·offset도 검사하고 추정 크기를 풀 높이로 쓰지 않는다', () => {
  const data = Array.from({ length: 100000 }, (_, i) => i);
  expect(
    uniformLength(data, (_, i) => ({
      length: i === 99999 ? 101 : 100,
      offset: i * 100,
    }))
  ).toBeNull();
  expect(
    uniformLength(data, (_, i) => ({ length: 100, offset: i * 100 + 1 }))
  ).toBeNull();
  expect(
    uniformLength(data, (_, i) => ({ length: 100, offset: i * 100 }))
  ).toBe(100);
});
it('이동 창의 교집합은 슬롯을 유지하고 새 항목만 빈 슬롯에 배치한다', () => {
  const key = (i: number) => String(i);
  const first = reconcileSlots([], [0, 1, 2], key);
  expect(reconcileSlots(first, [1, 2, 3], key)).toEqual([
    { index: 3, key: '3' },
    { index: 1, key: '1' },
    { index: 2, key: '2' },
  ]);
});
