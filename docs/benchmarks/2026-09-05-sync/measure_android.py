"""다섯 정상 목록과 이전 ZigPool 방식을 같은 앱에서 비교한다."""
import os, subprocess, time, pathlib, re, json
OUT = pathlib.Path(os.environ.get('OUT', '/tmp/zerolist-ablation'))
OUT.mkdir(parents=True, exist_ok=True)
ADB = [os.environ.get('ADB', 'adb'), '-s', os.environ.get('SERIAL', 'emulator-5554')]
PKG = 'zerolist.example'
TRACE = os.environ.get('TRACE', '0') == '1'
VARIANTS = [(e, e, 'normal') for e in ['flatlist', 'legend', 'flashlist', 'zerolist', 'zigpool']]
VARIANTS += [('zigpool-legacy', 'zigpool', 'normal')]
# Stage 2 is selected explicitly and uses its own APK/results directory.
if os.environ.get('STAGE') == 'cadence':
    VARIANTS = [('zigpool', 'zigpool', 'normal'), ('zigpool-keep-alive', 'zigpool', 'normal')]
if os.environ.get('VARIANTS'):
    selected = os.environ['VARIANTS'].split(',')
    VARIANTS = [v for v in VARIANTS if v[0] in selected]

def adb(*args, binary=False):
    r = subprocess.run(ADB + list(args), capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors='replace'))
    return r.stdout if binary else r.stdout.decode(errors='replace')

def counters(pid, engine):
    log = adb('logcat', '-d', '--pid=' + pid, '-v', 'brief', 'ReactNativeJS:I', 'ZlPool:I', 'ZlFrame:I', '*:S')
    rows = re.findall(r'\[JS0\] ' + engine + r' renders=(\d+) cbs=(\d+) mounts=(\d+) unmounts=(\d+)', log)
    return ([int(x) for x in rows[-1]] if rows else None), log

results = []
for rep in range(int(os.environ.get('REPEATS', '1' if TRACE else '5'))):
    shift = rep % len(VARIANTS)
    for variant, engine, mode in VARIANTS[shift:] + VARIANTS[:shift]:
        name = f'{rep+1}-{variant}'
        adb('shell', 'am', 'force-stop', PKG)
        adb('shell', 'am', 'start', '-W', '-n', PKG + '/.SoloActivity', '--es', 'engine', engine, '--ei', 'count', '100000', '--es', 'cell', 'heavy', '--es', 'diagnostic', mode, '--ez', 'trace', 'true' if TRACE else 'false', '--ez', 'keepAlive', 'false', '--ez', 'legacyRecycling', 'true' if variant == 'zigpool-legacy' else 'false')
        time.sleep(3)
        pid = adb('shell', 'pidof', PKG).strip()
        baseline, _ = counters(pid, engine)
        if baseline is None:
            raise RuntimeError('Missing readiness: ' + name)
        if rep == 0:
            (OUT / (name + '-before.png')).write_bytes(adb('exec-out', 'screencap', '-p', binary=True))
        adb('shell', 'dumpsys', 'gfxinfo', PKG, 'reset')
        start = time.monotonic()
        gestures = []
        for _ in range(12):
            gestures.append(round(time.monotonic() - start, 4))
            adb('shell', 'input', 'swipe', '540', '1800', '540', '600', '300')
        time.sleep(1.2)
        gfx = adb('shell', 'dumpsys', 'gfxinfo', PKG, 'framestats')
        final, log = counters(pid, engine)
        if final is None:
            raise RuntimeError('Missing final counters: ' + name)
        (OUT / (name + '-gfx.txt')).write_text(gfx)
        (OUT / (name + '-log.txt')).write_text(log)
        if rep == 0:
            (OUT / (name + '-after.png')).write_bytes(adb('exec-out', 'screencap', '-p', binary=True))
            adb('shell', 'uiautomator', 'dump', '/data/local/tmp/zerolist-window.xml')
            (OUT / (name + '-ui.xml')).write_text(adb('shell', 'cat', '/data/local/tmp/zerolist-window.xml'))
        def match(pattern):
            m = re.search(pattern, gfx)
            if not m:
                raise RuntimeError('Missing gfx metric: ' + pattern)
            return m.group(1)
        row = {'run': rep+1, 'variant': variant, 'engine': engine, 'mode': mode, 'trace': TRACE, 'legacy_recycling': variant == 'zigpool-legacy',
               'frames': int(match(r'Total frames rendered: (\d+)')),
               'jank_count': int(match(r'Janky frames: (\d+)')),
               'jank_percent': float(match(r'Janky frames: \d+ \(([\d.]+)%\)')),
               'p50_ms': int(match(r'50th percentile: (\d+)ms')),
               'p95_ms': int(match(r'95th percentile: (\d+)ms')),
               'slow_ui': int(match(r'Number Slow UI thread: (\d+)')),
               'slow_draw': int(match(r'Number Slow issue draw commands: (\d+)')),
               'baseline': baseline, 'final': final,
               'delta': [b-a for a,b in zip(baseline,final)], 'gesture_host_seconds': gestures}
        results.append(row)
        (OUT / 'results.json').write_text(json.dumps(results, indent=2))
        print(json.dumps({k: row[k] for k in ['run','variant','frames','jank_count','jank_percent','p95_ms','delta']}), flush=True)
print('COMPLETE')
