// 벤치 harness 공용 타입.
// 측정은 전부 시뮬/에뮬 기준 — directional only, NOT device-validated.

export type CellType = 'simple' | 'image' | 'complex' | 'heavy';
export type HeightMode = 'fixed' | 'variable' | 'dynamic';
export type ScrollScenario = 'fling' | 'jsBlocked' | 'fastJump';
export type EngineId =
  | 'flatlist'
  | 'legend'
  | 'flashlist'
  | 'native'
  | 'nativezig'
  | 'zerolist';

export interface BenchConfig {
  engine: EngineId;
  cell: CellType;
  height: HeightMode;
  count: number;
  scenario: ScrollScenario;
}

export interface Item {
  id: number;
  title: string;
  body: string;
  /** variable/fixed 모드에서 사전 확정된 높이. dynamic 모드에선 무시. */
  height: number;
  hue: number;
}

export interface FrameStats {
  /** rAF 간격(ms) — JS 스레드에서 관측한 근사치. 네이티브 프레임타임 아님. */
  p50: number;
  p95: number;
  p99: number;
  /** 기대 프레임 예산의 1.5배 초과한 프레임 수(드랍 근사). */
  dropped: number;
  frames: number;
  durationMs: number;
}

/** 모든 엔진 어댑터가 구현하는 공통 인터페이스.
 * 레이아웃 힌트 패리티: fixed/variable 에선 모든 엔진이 동일한
 * offsets/fixedHeight 를 받아 각 엔진의 최강 등가 API 에 연결한다
 * (한 엔진만 getItemLayout 받는 불공정 방지). dynamic 에선 둘 다 null. */
export interface ListEngineProps {
  items: Item[];
  cell: CellType;
  height: HeightMode;
  /** 누적 오프셋(길이 n+1). dynamic 이면 null. */
  offsets: Float64Array | null;
  /** 고정 높이값. fixed 가 아니면 null. */
  fixedHeight: number | null;
  /** dynamic 모드에서 셀이 측정 높이를 보고. */
  onMeasure?: (id: number, h: number) => void;
  /** 실제 스크롤 검증용 — 현재 contentOffset.y 보고. */
  onScrollY?: (y: number) => void;
  /** 렌더 검증용 — 셀이 실제 렌더될 때 id 보고(렌더 0이면 측정 무효). */
  onRender?: (id: number) => void;
}
