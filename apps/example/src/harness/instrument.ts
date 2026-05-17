// JS-0 구조 검증 계측 — "시간"이 아니라 "JS 스레드 작업 횟수"를 센다.
// 결정적 스크롤(동일 adb swipe)에서 정수 카운트라 재현 가능하고,
// 속도 주장이 아니라 *구조적 사실*("③ 는 스크롤당 JS 작업이
// O(리사이클) ≪ FlatList 의 O(스크롤)")을 입증한다. 전략 안전.
let renders = 0; // renderItem(=Cell) 실제 렌더 횟수(전 엔진 동일 Cell)
let cbs = 0; // JS 스크롤/리사이클 콜백 진입 횟수
let timer: ReturnType<typeof setInterval> | null = null;

export const inst = {
  render() {
    renders++;
  },
  cb() {
    cbs++;
  },
  // 누적 카운트를 주기 로깅(스크롤 정착 후 값이 수렴 → 그 값을 읽음).
  start(tag: string) {
    renders = 0;
    cbs = 0;
    if (timer) clearInterval(timer);
    timer = setInterval(() => {
      // logcat/simctl 에서 grep: "[JS0]"
      console.log(`[JS0] ${tag} renders=${renders} cbs=${cbs}`);
    }, 1000);
  },
};
