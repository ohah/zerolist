import { useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  type LayoutChangeEvent,
} from 'react-native';
import { nativeLog } from '@ohah/zerolist';
import type {
  BenchConfig,
  CellType,
  EngineId,
  FrameStats,
  HeightMode,
  ScrollScenario,
} from './types';
import { makeItems } from './data';
import { FrameRecorder, JsThreadHog, statsFromDeltas } from './metrics';
import { drive, type Scrollable } from './flingDriver';
import { ENGINES, ENGINE_LABEL } from './engines';

const ENGINE_IDS: EngineId[] = [
  'flatlist',
  'legend',
  'flashlist',
  'native',
  'zerolist',
];
const CELLS: CellType[] = ['simple', 'image', 'complex'];
const HEIGHTS: HeightMode[] = ['fixed', 'variable', 'dynamic'];
const SCENARIOS: ScrollScenario[] = ['fling', 'jsBlocked', 'fastJump'];
// 렌더 harness 크기 — Phase A 연산 마이크로벤치(N=1e6)와 다른 척도.
const COUNTS = [200, 2000, 20000];
const WARMUP = 1;
const RUNS = 4;

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

  const Engine = ENGINES[cfg.engine];
  const items = useMemo(
    () => makeItems(cfg.count, cfg.height),
    [cfg.count, cfg.height]
  );
  useEffect(() => {
    measured.current.clear();
  }, [items]);

  const set = <K extends keyof BenchConfig>(k: K, v: BenchConfig[K]) =>
    setCfg((c) => ({ ...c, [k]: v }));

  // run 시점에 실제 순회 범위를 다시 계산한다. dynamic 모드는
  // 측정 높이가 ref 로만 들어와 렌더에 안 잡히므로 여기서 읽는다.
  function extent(): number {
    let s = 0;
    for (const it of items) {
      s +=
        cfg.height === 'dynamic'
          ? (measured.current.get(it.id) ?? it.height)
          : it.height;
    }
    return s;
  }

  const comparable = cfg.scenario !== 'jsBlocked';

  async function run() {
    if (!Engine || running || !listRef.current) return;
    setRunning(true);
    setStats(null);
    await new Promise((r) => setTimeout(r, 300)); // 초기 렌더 대기(고정 슬립)

    const hog = new JsThreadHog();
    if (cfg.scenario === 'jsBlocked') hog.start();
    const pooled: number[] = [];
    try {
      for (let i = 0; i < WARMUP; i++) {
        await drive(listRef.current, cfg.scenario, extent(), viewport.current);
      }
      for (let r = 0; r < RUNS; r++) {
        const rec = new FrameRecorder();
        rec.start();
        await drive(listRef.current, cfg.scenario, extent(), viewport.current);
        rec.stop();
        pooled.push(...rec.getDeltas());
      }
    } finally {
      hog.stop();
      const s = statsFromDeltas(pooled);
      setStats(s);
      setRunning(false);
      nativeLog(
        `[Harness][sim-only] ${ENGINE_LABEL[cfg.engine]} cell=${cfg.cell} ` +
          `h=${cfg.height} n=${cfg.count} sc=${cfg.scenario}(scripted) ` +
          `runs=${RUNS} comparable=${comparable} | ` +
          `p50=${s.p50.toFixed(1)} p95=${s.p95.toFixed(1)} ` +
          `p99=${s.p99.toFixed(1)} drop=${s.dropped}/${s.frames}`
      );
    }
  }

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
            onMeasure={(id, hgt) => measured.current.set(id, hgt)}
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
