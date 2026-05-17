// JS-0 구조 검증 계측 — "시간"이 아니라 "JS 스레드 작업 횟수"를 센다.
// 결정적 스크롤(동일 adb swipe)에서 정수 카운트라 재현 가능하고,
// 속도 주장이 아니라 *구조적 사실*("③ 는 스크롤당 JS 작업이
// O(리사이클) ≪ FlatList 의 O(스크롤)")을 입증한다. 전략 안전.
let renders = 0; // renderItem(=Cell) 실제 렌더 횟수(전 엔진 동일 Cell)
let cbs = 0; // JS 스크롤/리사이클 콜백 진입 횟수
let mounts = 0; // Cell 컴포넌트 인스턴스 생성(=mount churn)
let unmounts = 0; // Cell 인스턴스 파괴
let timer: ReturnType<typeof setInterval> | null = null;

// 전부 *횟수* 지표(시간 아님). 결정적 입력이면 OS 스케줄링과 무관하게
// 같은 정수 → 시뮬/에뮬에서도 재현 가능, 속도 주장 아님(전략 안전).
// mount/unmount 는 아키텍처 차이를 가장 잘 드러냄: ③ 고정 풀 = 초기
// 후 ≈0, FlatList = 스크롤 따라 셀 생성/파괴 churn.
export const inst = {
  render() {
    renders++;
  },
  cb() {
    cbs++;
  },
  mount() {
    mounts++;
  },
  unmount() {
    unmounts++;
  },
  start(tag: string) {
    renders = 0;
    cbs = 0;
    mounts = 0;
    unmounts = 0;
    if (timer) clearInterval(timer);
    timer = setInterval(() => {
      // logcat/simctl 에서 grep: "[JS0]"
      console.log(
        `[JS0] ${tag} renders=${renders} cbs=${cbs} mounts=${mounts} unmounts=${unmounts}`
      );
    }, 1000);
  },
};
