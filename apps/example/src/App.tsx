import { useMemo } from 'react';
import { Text, View, StyleSheet, ScrollView } from 'react-native';
import {
  engineInfo,
  nativeLog,
  buildOffsetsZig,
  visibleChecksumZig,
  jsRef,
} from '@ohah/zerolist';

const SIZES = [10_000, 100_000, 1_000_000];
const K = 4_000;
const VIEWPORT = 800;
const WARMUP = 1;
const RUNS = 5;

function now() {
  return global.performance?.now?.() ?? Date.now();
}

// 워밍업 1회 폐기 후 RUNS 회 측정 → median/p95 (단일 샘플 금지).
function measure(fn: () => void) {
  for (let w = 0; w < WARMUP; w++) fn();
  const ts: number[] = [];
  for (let r = 0; r < RUNS; r++) {
    const t = now();
    fn();
    ts.push(now() - t);
  }
  ts.sort((a, b) => a - b);
  const median = ts[ts.length >> 1]!;
  const p95 = ts[Math.min(ts.length - 1, Math.ceil(ts.length * 0.95) - 1)]!;
  return { median, p95 };
}

type Row = {
  n: number;
  build: { jsMed: number; zigMed: number; jsP95: number; ok: boolean };
  scan: { jsMed: number; zigMed: number; jsP95: number; ok: boolean };
};

function benchOne(n: number): Row {
  const heights = new Float32Array(n);
  for (let i = 0; i < n; i++) heights[i] = 40 + ((i * 37) % 100);
  const offJs = new Float64Array(n + 1);
  const offZig = new Float64Array(n + 1);

  const build = {
    js: measure(() => jsRef.buildOffsets(heights, offJs)),
    zig: measure(() => buildOffsetsZig(heights, offZig)),
  };

  const total = offJs[n]!;
  const span = Math.max(1, total - VIEWPORT);
  const scrolls = new Float64Array(K);
  for (let q = 0; q < K; q++) scrolls[q] = (q / K) * span;

  let csJs = 0;
  let csZig = 0;
  const scan = {
    js: measure(() => {
      csJs = jsRef.visibleChecksum(offJs, n, VIEWPORT, scrolls);
    }),
    zig: measure(() => {
      csZig = visibleChecksumZig(offZig, n, VIEWPORT, scrolls);
    }),
  };

  return {
    n,
    build: {
      jsMed: build.js.median,
      zigMed: build.zig.median,
      jsP95: build.js.p95,
      ok: Math.abs(offJs[n]! - offZig[n]!) < 1,
    },
    scan: {
      jsMed: scan.js.median,
      zigMed: scan.zig.median,
      jsP95: scan.js.p95,
      ok: csJs === csZig,
    },
  };
}

export default function App() {
  const { info, rows } = useMemo(() => {
    const ei = engineInfo();
    const rs = SIZES.map(benchOne);
    for (const r of rs) {
      nativeLog(
        `[PhaseA][sim-only] ${ei} N=${r.n} ` +
          `build js=${r.build.jsMed.toFixed(2)}(p95 ${r.build.jsP95.toFixed(2)}) ` +
          `zig=${r.build.zigMed.toFixed(2)} ok=${r.build.ok} | ` +
          `scan(K=${K}) js=${r.scan.jsMed.toFixed(2)} zig=${r.scan.zigMed.toFixed(2)} ` +
          `ok=${r.scan.ok} x=${(r.scan.jsMed / r.scan.zigMed).toFixed(2)}`
      );
    }
    return { info: ei, rows: rs };
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.c}>
      <Text style={styles.h}>ZeroList · Phase A</Text>
      <Text style={styles.warn}>
        ⚠ 시뮬/에뮬 · directional only · NOT device-validated
      </Text>
      <Text style={styles.mono}>{info}</Text>
      <Text style={styles.sub}>
        median of {RUNS} runs (warmup {WARMUP} discarded)
      </Text>
      {rows.map((r) => (
        <View key={r.n} style={styles.card}>
          <Text style={styles.n}>N = {r.n.toLocaleString()}</Text>
          <Text>
            누적오프셋 build: JS {r.build.jsMed.toFixed(2)}ms (p95{' '}
            {r.build.jsP95.toFixed(2)}) · Zig {r.build.zigMed.toFixed(2)}ms{' '}
            {r.build.ok ? '✅' : '❌'}
          </Text>
          <Text>
            가시범위 scan(K={K}): JS {r.scan.jsMed.toFixed(2)}ms · Zig{' '}
            {r.scan.zigMed.toFixed(2)}ms {r.scan.ok ? '✅' : '❌'}
          </Text>
          <Text style={styles.hl}>
            scan {(r.scan.jsMed / r.scan.zigMed).toFixed(2)}x (sim, 방향성만)
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  c: { padding: 20, gap: 8 },
  h: { fontSize: 22, fontWeight: '700' },
  warn: { color: '#b00', fontWeight: '600', fontSize: 12 },
  mono: { fontFamily: 'Courier', fontSize: 11, color: '#555' },
  sub: { fontSize: 11, color: '#777' },
  card: { padding: 14, backgroundColor: '#f0f0f5', borderRadius: 12, gap: 3 },
  n: { fontWeight: '700' },
  hl: { fontWeight: '700', marginTop: 4 },
});
