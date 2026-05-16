import { useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  type LayoutChangeEvent,
} from 'react-native';
import { nativeLog, jsRef } from '@ohah/zerolist';
import type {
  BenchConfig,
  CellType,
  EngineId,
  FrameStats,
  HeightMode,
  ScrollScenario,
} from './types';
import { makeItems, nominalExtent } from './data';
import { FrameRecorder, JsThreadHog, statsFromDeltas } from './metrics';
import { drive, type Scrollable } from './flingDriver';
import { ENGINES, ENGINE_LABEL, ENGINE_HINT } from './engines';

const MIN_FRAMES = 150; // 이 미만이면 p95/p99 통계적으로 약함

const ENGINE_IDS: EngineId[] = [
  'flatlist',
  'legend',
  'flashlist',
  'native',
  'zerolist',
];
const CELLS: CellType[] = ['simple', 'image', 'complex', 'heavy'];
const HEIGHTS: HeightMode[] = ['fixed', 'variable', 'dynamic'];
const SCENARIOS: ScrollScenario[] = ['fling', 'jsBlocked', 'fastJump'];
// 렌더 harness 크기 — Phase A 연산 마이크로벤치(N=1e6)와 다른 척도.
const COUNTS = [200, 2000, 20000];
const WARMUP = 1;
const RUNS = 4; // 수동 Run
const SWEEP_RUNS = 3; // 전수 sweep(런타임 관리)

// 변별력 매트릭스: 시뮬 Release n=2000 은 너무 쉬워 3 JS 엔진이
// 동률로 나옴(테스트 무력). 큰 N(20k) + 무거운 셀(complex) +
// fixed/dynamic + fling/fastJump 로 엔진 차이가 드러나는 지점을 찾음.
const AUTO_MATRIX = true;
const BIG_N = 20000;
const SWEEP: BenchConfig[] = [];
for (const engine of ['flatlist', 'legend', 'flashlist'] as EngineId[]) {
  for (const height of ['fixed', 'dynamic'] as HeightMode[]) {
    for (const scenario of ['fling', 'fastJump'] as ScrollScenario[]) {
      SWEEP.push({
        engine,
        cell: 'heavy',
        height,
        count: BIG_N,
        scenario,
      });
    }
  }
}

function Seg<T extends string>(props: {
  label: string;
  value: T;
  options: T[];
  fmt?: (v: T) => string;
  onChange: (v: T) => void;
}) {
  return (
    <View style={styles.segRow}>
      <Text style={styles.segLabel}>{props.label}</Text>
      <View style={styles.segBtns}>
        {props.options.map((o) => (
          <Pressable
            key={o}
            onPress={() => props.onChange(o)}
            style={[styles.seg, props.value === o && styles.segOn]}
          >
            <Text style={[styles.segTxt, props.value === o && styles.segTxtOn]}>
              {props.fmt ? props.fmt(o) : o}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

export default function Harness() {
  const [cfg, setCfg] = useState<BenchConfig>({
    engine: 'flatlist',
    cell: 'simple',
    height: 'fixed',
    count: 2000,
    scenario: 'fling',
  });
  const [stats, setStats] = useState<FrameStats | null>(null);
  const [running, setRunning] = useState(false);

  const listRef = useRef<Scrollable>(null);
  const viewport = useRef(600);
  const measured = useRef(new Map<number, number>());
  const maxY = useRef(0); // 측정 중 실제 도달한 스크롤 오프셋(커버리지)
  const renderedIds = useRef(new Set<number>()); // 측정 중 실제 렌더된 셀

  const Engine = ENGINES[cfg.engine];
  const items = useMemo(
    () => makeItems(cfg.count, cfg.height),
    [cfg.count, cfg.height]
  );
  // 패리티: 모든 엔진에 동일 레이아웃 힌트 전달.
  const offsets = useMemo(() => {
    if (cfg.height === 'dynamic') return null;
    const hs = new Float32Array(items.length);
    for (let i = 0; i < items.length; i++) hs[i] = items[i]!.height;
    const o = new Float64Array(items.length + 1);
    jsRef.buildOffsets(hs, o);
    return o;
  }, [items, cfg.height]);
  const fixedHeight =
    cfg.height === 'fixed' ? (items[0]?.height ?? null) : null;

  useEffect(() => {
    measured.current.clear();
  }, [items]);

  const set = <K extends keyof BenchConfig>(k: K, v: BenchConfig[K]) =>
    setCfg((c) => ({ ...c, [k]: v }));

  interface MeasureResult {
    stats: FrameStats;
    maxY: number;
    rendered: number;
    maxOffset: number;
  }

  async function measureConfig(
    c: BenchConfig,
    runs: number
  ): Promise<MeasureResult> {
    const list = listRef.current!;
    // 순회 범위 = 공칭 높이 합(결정론적, 객체 미생성). dynamic 실제
    // 높이는 콘텐츠 의존이라 근사 — flingDriver/메모리에 명시된 한계.
    const maxOffset = Math.max(
      0,
      nominalExtent(c.count, c.height) - viewport.current
    );
    maxY.current = 0;
    const hog = new JsThreadHog();
    if (c.scenario === 'jsBlocked') hog.start();
    const pooled: number[] = [];
    try {
      for (let i = 0; i < WARMUP; i++) await drive(list, c.scenario, maxOffset);
      renderedIds.current.clear(); // 측정 구간 렌더만 집계
      for (let r = 0; r < runs; r++) {
        const rec = new FrameRecorder();
        rec.start();
        await drive(list, c.scenario, maxOffset);
        rec.stop();
        pooled.push(...rec.getDeltas());
      }
    } finally {
      hog.stop();
    }
    return {
      stats: statsFromDeltas(pooled),
      maxY: maxY.current,
      rendered: renderedIds.current.size,
      maxOffset,
    };
  }

  function logRow(tag: string, c: BenchConfig, runs: number, r: MeasureResult) {
    const s = r.stats;
    // 유효: 충분히 렌더 + 순회 범위의 80% 이상 실제 커버(블랭크/
    // 조기절단 아티팩트를 valid=true 로 흘리지 않게).
    const valid =
      r.rendered >= 30 && r.maxY >= 0.8 * r.maxOffset && r.maxOffset > 0;
    const lowSample = s.frames < MIN_FRAMES;
    nativeLog(
      `[${tag}][sim-only] ${ENGINE_LABEL[c.engine]} cell=${c.cell} ` +
        `h=${c.height} n=${c.count} sc=${c.scenario}(animated) runs=${runs} ` +
        `hint=${ENGINE_HINT[c.engine]} ` +
        `comparable=${c.scenario !== 'jsBlocked'} | ` +
        `p50=${s.p50.toFixed(1)} p95=${s.p95.toFixed(1)} ` +
        `p99=${s.p99.toFixed(1)} drop=${s.dropped}/${s.frames} ` +
        `maxY=${r.maxY | 0}/${r.maxOffset | 0} rendered=${r.rendered} ` +
        `valid=${valid} lowSample=${lowSample}`
    );
  }

  async function run() {
    if (!Engine || running || !listRef.current) return;
    setRunning(true);
    setStats(null);
    await new Promise((r) => setTimeout(r, 300)); // 초기 렌더 정착(고정 슬립)
    try {
      const res = await measureConfig(cfg, RUNS);
      setStats(res.stats);
      logRow('Harness', cfg, RUNS, res);
    } finally {
      setRunning(false);
    }
  }

  // 헤드리스 전수 측정: SWEEP 순회하며 [Matrix] 로그.
  const matrixRan = useRef(false);
  useEffect(() => {
    if (!AUTO_MATRIX || matrixRan.current) return;
    matrixRan.current = true;
    (async () => {
      setRunning(true);
      for (const c of SWEEP) {
        if (!ENGINES[c.engine]) continue;
        setCfg(c);
        // 엔진 교체·마운트·레이아웃 정착 대기(고정 슬립 — 정확한
        // 신호가 없어 보수적으로 길게. 너무 짧으면 이전 엔진 측정 위험).
        await new Promise((r) => setTimeout(r, 900));
        if (!listRef.current) continue;
        try {
          const res = await measureConfig(c, SWEEP_RUNS);
          setStats(res.stats);
          logRow('Matrix', c, SWEEP_RUNS, res);
        } catch {
          nativeLog(`[Matrix][sim-only] ${ENGINE_LABEL[c.engine]} FAILED`);
        }
      }
      setRunning(false);
      nativeLog('[Matrix][sim-only] DONE');
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const comparable = cfg.scenario !== 'jsBlocked';
  const disabled = !Engine || running;
  const runLabel = !Engine
    ? `${ENGINE_LABEL[cfg.engine]} 미구현`
    : running
      ? '측정 중…'
      : `Run (${WARMUP}+${RUNS})`;

  return (
    <View style={styles.root}>
      <Text style={styles.h}>ZeroList · Harness</Text>
      <Text style={styles.warn}>
        ⚠ 시뮬/에뮬 · rAF 근사 · scripted traversal(모멘텀 아님) · directional
        only · NOT device-validated
      </Text>
      <Seg
        label="engine"
        value={cfg.engine}
        options={ENGINE_IDS}
        fmt={(e) => ENGINE_LABEL[e]}
        onChange={(v) => set('engine', v)}
      />
      <Seg
        label="cell"
        value={cfg.cell}
        options={CELLS}
        onChange={(v) => set('cell', v)}
      />
      <Seg
        label="height"
        value={cfg.height}
        options={HEIGHTS}
        onChange={(v) => set('height', v)}
      />
      <Seg
        label="count"
        value={String(cfg.count)}
        options={COUNTS.map(String)}
        onChange={(v) => set('count', Number(v))}
      />
      <Seg
        label="scenario"
        value={cfg.scenario}
        options={SCENARIOS}
        onChange={(v) => set('scenario', v)}
      />

      {!comparable && (
        <Text style={styles.warn}>
          ⚠ jsBlocked: 측정기가 막힌 JS 스레드에 있어 교차엔진 비교 무효
          (comparable=false). 네이티브 프레임소스는 Phase B 이후.
        </Text>
      )}

      <Pressable
        onPress={run}
        disabled={disabled}
        style={[styles.run, disabled && styles.runOff]}
      >
        <Text style={styles.runTxt}>{runLabel}</Text>
      </Pressable>

      {stats && (
        <Text style={styles.result}>
          p50 {stats.p50.toFixed(1)}ms · p95 {stats.p95.toFixed(1)}ms · p99{' '}
          {stats.p99.toFixed(1)}ms · drop {stats.dropped}/{stats.frames}
          {comparable ? '' : ' · (비교 무효)'}
        </Text>
      )}

      <View
        style={styles.listBox}
        onLayout={(e: LayoutChangeEvent) => {
          viewport.current = e.nativeEvent.layout.height;
        }}
      >
        {Engine ? (
          <Engine
            ref={listRef}
            items={items}
            cell={cfg.cell}
            height={cfg.height}
            offsets={offsets}
            fixedHeight={fixedHeight}
            onMeasure={(id, hgt) => measured.current.set(id, hgt)}
            onScrollY={(y) => {
              if (y > maxY.current) maxY.current = y;
            }}
            onRender={(id) => renderedIds.current.add(id)}
          />
        ) : (
          <Text style={styles.todo}>
            {ENGINE_LABEL[cfg.engine]} 어댑터는 다음 Phase 에서 합류
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 10, gap: 6 },
  h: { fontSize: 18, fontWeight: '700' },
  warn: { color: '#b00', fontWeight: '600', fontSize: 11 },
  segRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  segLabel: { width: 58, fontSize: 11, color: '#555' },
  segBtns: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, flex: 1 },
  seg: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#e6e6ee',
  },
  segOn: { backgroundColor: '#222' },
  segTxt: { fontSize: 11, color: '#333' },
  segTxtOn: { color: '#fff' },
  run: {
    backgroundColor: '#1a7',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  runOff: { backgroundColor: '#999' },
  runTxt: { color: '#fff', fontWeight: '700' },
  result: { fontSize: 12, fontWeight: '600', color: '#114' },
  listBox: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    overflow: 'hidden',
  },
  todo: { padding: 20, color: '#777' },
});
