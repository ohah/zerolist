// 벤치 harness 공용 타입.
// 측정은 전부 시뮬/에뮬 기준 — directional only, NOT device-validated.

export type CellType = 'simple' | 'image' | 'complex';
export type HeightMode = 'fixed' | 'variable' | 'dynamic';
export type ScrollScenario = 'fling' | 'jsBlocked' | 'fastJump';
export type EngineId =
  | 'flatlist'
  | 'legend'
  | 'flashlist'
  | 'native'
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

/** 모든 엔진 어댑터가 구현하는 공통 인터페이스. */
export interface ListEngineProps {
  items: Item[];
  cell: CellType;
  height: HeightMode;
  /** dynamic 모드에서 셀이 측정 높이를 보고. */
  onMeasure?: (id: number, h: number) => void;
}
