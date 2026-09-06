"""동일 APK에서 기본 목록·재터치 수정 전·후를 교차 측정한다.

CROSS=true TRACE=false MOTION=false OUT=... python3 -I record.py
진단 비교는 CROSS 생략, RESUME=false/true, 기본 TRACE/MOTION=true로 실행한다.
화면을 1080×2400 세로로 맞춰야 하며 스크립트가 화면 설정을 변경하지는 않는다.
"""
from pathlib import Path
import subprocess, time, json, os, re, struct

O = Path(os.environ.get('OUT', '/private/tmp/zerolist-scroll'))
O.mkdir(parents=True, exist_ok=True)
A = [os.environ.get('ADB', '/Users/yoonhb/Library/Android/sdk/platform-tools/adb'), '-s', 'emulator-5554']
def adb(*args):
    return subprocess.check_output(A + list(args), timeout=40)

screen = adb('exec-out', 'screencap', '-p')
width, height = struct.unpack('>II', screen[16:24])
if (width, height) != (1080, 2400):
    raise RuntimeError(f'세로 1080x2400 필요: {width}x{height}')
trace = os.environ.get('TRACE', 'true')
motion = os.environ.get('MOTION', 'true')
cross = os.environ.get('CROSS') == 'true'
variants = ['flatlist', 'zigpool-before', 'zigpool-after'] if cross else ['flatlist', 'zigpool']
(O / 'conditions.json').write_text(json.dumps({'screen': [width, height], 'trace': trace, 'motion': motion, 'cross': cross, 'resume': os.environ.get('RESUME', 'false'), 'gap': os.environ.get('GAP', '0'), 'renderer': adb('shell', 'getprop', 'debug.hwui.renderer').decode().strip(), 'atrace_flags': adb('shell', 'getprop', 'debug.atrace.tags.enableflags').decode().strip()}, indent=2))
rows = []
for rep in range(int(os.environ.get('REPEATS', '3'))):
    order = variants[rep % len(variants):] + variants[:rep % len(variants)]
    for variant in order:
        engine = 'flatlist' if variant == 'flatlist' else 'zigpool'
        resume = str(variant == 'zigpool-after').lower() if cross else os.environ.get('RESUME', 'false')
        name = f'{rep+1}-{variant}'
        adb('shell', 'am', 'force-stop', 'zerolist.example')
        adb('shell', 'am', 'start', '-W', '-n', 'zerolist.example/.SoloActivity', '--es', 'engine', engine, '--ei', 'count', '100000', '--es', 'cell', 'heavy', '--ez', 'trace', trace, '--ez', 'motionTrace', motion, '--ez', 'resumeDrag', resume)
        time.sleep(3)
        pid = adb('shell', 'pidof', 'zerolist.example').decode().strip()
        adb('logcat', '-c')
        adb('shell', 'dumpsys', 'gfxinfo', 'zerolist.example', 'reset')
        for _ in range(12):
            adb('shell', 'input', 'swipe', '540', '1800', '540', '600', '300')
            time.sleep(float(os.environ.get('GAP', '0')))
        time.sleep(1.2)
        log = adb('logcat', '-d', '--pid=' + pid, '-v', 'brief', 'ZlMotion:I', 'ZlFrame:I', 'ReactNativeJS:I', '*:S').decode()
        (O / (name + '.log')).write_text(log)
        gfx = adb('shell', 'dumpsys', 'gfxinfo', 'zerolist.example', 'framestats').decode()
        (O / (name + '-gfx.txt')).write_text(gfx)
        if trace == 'true' and (log.count('touch action=0') != 12 or log.count('touch action=1') != 12 or log.count('frame intended=') < 100):
            raise RuntimeError(f'{name}: 유효 입력/프레임 부족')
        if motion == 'true' and not re.search(r'phase=predraw .* y=[1-9]\d*', log):
            raise RuntimeError(f'{name}: 스크롤 이동 없음')
        total = int(re.search(r'Total frames rendered: (\d+)', gfx)[1])
        if total < 100 or not re.search(r'renders=[2-9]\d*|renders=1\d+', log):
            raise RuntimeError(f'{name}: 프레임/내용 갱신 부족')
        m = re.search(r'Janky frames: (\d+) \(([\d.]+)%\)', gfx)
        row = {'run': rep + 1, 'variant': variant, 'engine': engine, 'resume': resume, 'total': total, 'late': int(m[1]), 'percent': float(m[2]), 'p95_ms': int(re.search(r'95th percentile: (\d+)ms', gfx)[1]), 'pipeline': re.search(r'Pipeline=([^\n]+)', gfx)[1]}
        rows.append(row)
        (O / 'results.json').write_text(json.dumps(rows, indent=2))
        print(row, flush=True)
