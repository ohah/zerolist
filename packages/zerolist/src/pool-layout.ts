// 풀 경로는 현재 고정 높이·연속 좌표만 처리한다. 추정값을 확정 높이로 쓰지 않는다.
export function uniformLength<T>(
  data: readonly T[],
  layout: (
    data: readonly T[],
    index: number
  ) => { length: number; offset: number }
): number | null {
  if (!data.length) return null;
  const height = layout(data, 0).length;
  if (!Number.isSafeInteger(height) || height <= 0) return null;
  for (let i = 0; i < data.length; i++) {
    const row = layout(data, i);
    if (row.length !== height || Math.abs(row.offset - i * height) > 0.001)
      return null;
  }
  return height;
}

export type PoolSlot = { index: number; key: string };
// 슬롯의 위치가 아니라 항목 정체성으로 기존 슬롯을 보존한다.
export function reconcileSlots(
  previous: readonly PoolSlot[],
  wanted: readonly number[],
  keyOf: (index: number) => string
): PoolSlot[] {
  const desired = new Map(wanted.map((index) => [keyOf(index), index]));
  const result: (PoolSlot | undefined)[] = Array(wanted.length);
  for (let slot = 0; slot < result.length; slot++) {
    const old = previous[slot];
    if (old && desired.has(old.key)) {
      result[slot] = { key: old.key, index: desired.get(old.key)! };
      desired.delete(old.key);
    }
  }
  const remaining = desired.entries();
  return Array.from(result, (value) => {
    if (value) return value;
    const [key, index] = remaining.next().value!;
    return { key, index };
  });
}

export function decodeBinding(
  encoded: string,
  count: number,
  capacity: number
): number[] | null {
  if (!encoded) return null;
  const indices = encoded.split(',').map(Number);
  if (
    indices.length !== capacity ||
    new Set(indices).size !== indices.length ||
    indices.some((i) => !Number.isSafeInteger(i) || i < 0 || i >= count)
  )
    return null;
  return indices;
}
