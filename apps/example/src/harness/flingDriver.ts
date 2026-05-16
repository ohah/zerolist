import type { ScrollScenario } from './types';
import { nextFrame, now } from './util';

export interface Scrollable {
  scrollToOffset: (offset: number, animated?: boolean) => void;
}

// 네이티브 애니메이션 스크롤로 구동(animated:true) — 리사이클러
// 엔진이 윈도우를 실제 렌더하게 한다(매 프레임 순간이동은 백지
// 렌더 → 측정 무효였음, 스크린샷 입증). 단 물리 플링은 아니므로
// "animated traversal" 로 표기.
//
// 핵심: 각 패스를 "도착까지"가 아니라 **고정 시간** 동안 샘플한다.
// 도착/정착 휴리스틱은 느린·jank 엔진의 스크롤 이벤트가 늦게 와서
// 조기 종료 → 그 엔진만 적게 측정되는 불공정을 유발했다. 고정
// 시간이면 모든 엔진이 동일 창에서 동일 프레임 수로 측정된다.

const PASS_MS = 1500;
const JUMP_MS = 500;

async function animateFor(
  target: Scrollable,
  to: number,
  ms: number
): Promise<void> {
  target.scrollToOffset(to, true);
  const end = now() + ms;
  while (now() < end) await nextFrame();
}

export async function drive(
  target: Scrollable,
  scenario: ScrollScenario,
  maxOffset: number
): Promise<void> {
  if (scenario === 'fastJump') {
    for (const s of [0.0, 0.85, 0.15, 0.97, 0.4, 0.75, 0.05, 1.0]) {
      await animateFor(target, s * maxOffset, JUMP_MS);
    }
    return;
  }
  // fling/jsBlocked: 끝까지 내렸다가 다시 위로(고정 시간 1왕복).
  await animateFor(target, maxOffset, PASS_MS);
  await animateFor(target, 0, PASS_MS);
}
