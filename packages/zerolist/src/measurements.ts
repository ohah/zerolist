// 같은 키의 측정은 다음 onLayout까지 유지한다. 새 객체라는 이유만으로
// 지우면 실제 크기가 같아 onLayout이 재발생하지 않을 때 측정을 잃는다.
// 항목 객체를 캐시에 보관하지 않으며 제거된 키는 회수한다.
export function retainMeasurements(
  previous: ReadonlyMap<string, number>,
  count: number,
  keyOf: (index: number) => string
): Map<string, number> {
  const next = new Map<string, number>();
  if (previous.size === 0) return next;
  for (let i = 0; i < count; i++) {
    const key = keyOf(i);
    const length = previous.get(key);
    if (length != null) next.set(key, length);
    if (next.size === previous.size) break;
  }
  return next;
}
