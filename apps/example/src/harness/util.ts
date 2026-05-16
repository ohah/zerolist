// 시간/프레임/통계 공용 유틸 (harness 단일 소스).

const clock = global.performance?.now ? () => performance.now() : Date.now;

export function now(): number {
  return clock();
}

export function nextFrame(): Promise<void> {
  return new Promise((res) => requestAnimationFrame(() => res()));
}

/** 최근접 순위(nearest-rank) 백분위. sorted 는 오름차순. */
export function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const i = Math.min(sorted.length - 1, Math.ceil(sorted.length * p) - 1);
  return sorted[i]!;
}
