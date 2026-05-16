import type { FrameStats } from './types';
import { now, percentile } from './util';

/** 프레임 간격 배열 → 통계. 다회 run 풀링 결과에도 그대로 적용. */
export function statsFromDeltas(
  deltas: number[],
  budgetMs = 1000 / 60
): FrameStats {
  let dropped = 0;
  let total = 0;
  for (const d of deltas) {
    total += d;
    if (d > budgetMs * 1.5) dropped++;
  }
  const sorted = [...deltas].sort((a, b) => a - b);
  return {
    p50: percentile(sorted, 0.5),
    p95: percentile(sorted, 0.95),
    p99: percentile(sorted, 0.99),
    dropped,
    frames: deltas.length,
    durationMs: total,
  };
}

// rAF 간격으로 프레임 통계를 근사한다. JS 스레드에서 관측하는
// 값이라 네이티브 프레임타임이 아님 — 방향성 지표. 정밀 측정은
// 네이티브 훅(Choreographer/CADisplayLink) = Phase B 합류 후.
export class FrameRecorder {
  private deltas: number[] = [];
  private last = 0;
  private raf = 0;
  private running = false;

  start() {
    this.deltas = [];
    this.last = 0;
    this.running = true;
    const tick = () => {
      if (!this.running) return;
      const t = now();
      if (this.last) this.deltas.push(t - this.last);
      this.last = t;
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  /** stop() 후 원시 프레임 간격 — 여러 run 풀링용. */
  getDeltas(): number[] {
    return this.deltas;
  }

  stop(budgetMs = 1000 / 60): FrameStats {
    this.running = false;
    cancelAnimationFrame(this.raf);
    return statsFromDeltas(this.deltas, budgetMs);
  }
}

// scenario='jsBlocked': 스크롤 중 JS 스레드를 주기적으로 점유.
// 주의: 이 hog 가 막는 스레드가 FrameRecorder 의 rAF 가 도는
// 바로 그 스레드라, 결과는 JS 스레드 cadence 자체일 뿐 off-JS-thread
// 엔진의 우위를 측정하지 못한다 → 교차엔진 비교 무효(comparable=false).
// 진짜 측정은 네이티브 프레임소스 필요(Phase B 이후).
export class JsThreadHog {
  private timer: ReturnType<typeof setInterval> | null = null;

  start(busyMs = 8, everyMs = 16) {
    this.timer = setInterval(() => {
      const end = now() + busyMs;
      while (now() < end) {
        // 의도적 동기 점유
      }
    }, everyMs);
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }
}
