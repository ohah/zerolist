"""정량 시험 이후 별도 진단. 관측 경로를 바꾸는 gfx 범주는 켜지 않는다."""
from pathlib import Path
import subprocess,time,json,re,zipfile
D=Path(__file__).resolve().parent;O=Path('/private/tmp/zerolist-command-traces');O.mkdir(exist_ok=False)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554']
def adb(*a):return subprocess.check_output(A+list(a),stderr=subprocess.STDOUT,timeout=40)
subprocess.run(['xcrun','simctl','terminate','ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D','zerolist.example'],capture_output=True)
adb('push',str(D/'trace.cfg'),'/data/misc/perfetto-configs/zl-command.cfg')
rows=[]
for engine in ['template-palette','template-palette-command','template-command']:
 adb('shell','am','force-stop','zerolist.example')
 adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--es','cell','heavy','--ei','count','100000','--ei','bufferRows','5','--ei','jsBlockMs','160','--es','diagnostic','normal','--ez','commonAudit','false')
 time.sleep(3)
 for _ in range(12):adb('shell','input','swipe','540','1900','540','400','120')
 adb('shell','input','tap','540','1200');time.sleep(2)
 adb('shell','dumpsys','gfxinfo','zerolist.example','reset')
 remote='/data/misc/perfetto-traces/zl-command.perfetto-trace'
 adb('shell','perfetto','--background-wait','--txt','-c','/data/misc/perfetto-configs/zl-command.cfg','-o',remote)
 start=time.monotonic()
 for n,a,b,ms in [(3,1800,600,300),(6,1900,400,120),(6,400,1900,120),(3,1800,600,300)]:
  for _ in range(n):adb('shell','input','swipe','540',str(a),'540',str(b),str(ms))
 gesture_seconds=time.monotonic()-start
 time.sleep(max(0,16-gesture_seconds))
 adb('pull',remote,str(O/(engine+'.perfetto-trace')))
 gfx=adb('shell','dumpsys','gfxinfo','zerolist.example','framestats').decode();(O/(engine+'-gfx.txt')).write_text(gfx)
 row=dict(engine=engine,diagnostic_only=True,trace_seconds=15,gesture_seconds=gesture_seconds,jank_percent=float(re.search(r'Janky frames: \d+ \(([\d.]+)%\)',gfx)[1]),p95_ms=int(re.search(r'95th percentile: (\d+)ms',gfx)[1]))
 rows.append(row);print(row,flush=True)
(D/'trace-results.json').write_text(json.dumps(rows,indent=2))
with zipfile.ZipFile(D/'trace-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in O.iterdir():z.write(p,p.name)
adb('shell','am','force-stop','zerolist.example')
