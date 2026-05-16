import type { ScrollScenario } from './types';
import { nextFrame } from './util';

export interface Scrollable {
  scrollToOffset: (offset: number, animated?: boolean) => void;
}

// 결정론적 "스크립트 오프셋 순회" — 프레임마다 오프셋을 강제한다.
// 실제 네이티브 모멘텀/플링 물리가 아니므로 모멘텀 성능이라 부르면
// 안 됨(엔진에 동일 입력을 주기 위한 합성 입력). 라벨도 그렇게 표기.
export async function drive(
  target: Scrollable,
  scenario: ScrollScenario,
  contentHeight: number,
  viewport: number
): Promise<void> {
  const maxOffset = Math.max(0, contentHeight - viewport);

  if (scenario === 'fastJump') {
    const stops = [0.0, 0.85, 0.15, 0.97, 0.4, 0.75, 0.05, 1.0];
    for (const s of stops) {
      target.scrollToOffset(s * maxOffset, false);
      for (let f = 0; f < 8; f++) await nextFrame();
    }
    return;
  }

  // fling/jsBlocked: cubic ease-out 로 다운→업 1회씩 (합성 감속곡선).
  const passes: Array<[number, number]> = [
    [0, maxOffset],
    [maxOffset, 0],
  ];
  for (const [from, to] of passes) {
    const FRAMES = 90; // ≈1.5s @60fps
    for (let f = 0; f <= FRAMES; f++) {
      const t = f / FRAMES;
      const eased = 1 - Math.pow(1 - t, 3);
      target.scrollToOffset(from + (to - from) * eased, false);
      await nextFrame();
    }
  }
}
