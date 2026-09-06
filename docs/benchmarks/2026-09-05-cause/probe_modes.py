"""계측 자체가 결과에 미치는 영향을 같은 APK에서 교차 확인한다."""
from pathlib import Path
import subprocess,time,json,re,os
P=Path(__file__).resolve().parent;O=Path(os.environ.get('OUT','/private/tmp/zerolist-probe-modes'));O.mkdir(parents=True,exist_ok=True)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554']
def adb(*a):return subprocess.check_output(A+list(a),timeout=40)
full=(P/'trace.cfg').read_text();ftrace=full.replace('data_sources { config { name: "android.surfaceflinger.frametimeline" } }','')
configs={'full':full,'ftrace':ftrace,'timeline':'buffers { size_kb: 8192 }\nduration_ms: 9000\ndata_sources { config { name: "android.surfaceflinger.frametimeline" } }\n'}
if os.environ.get('STAGE') == 'categories':
 configs = {
  'sched': 'buffers { size_kb: 16384 }\nduration_ms: 9000\ndata_sources { config { name: "linux.ftrace" ftrace_config { ftrace_events: "sched/sched_switch" ftrace_events: "sched/sched_waking" } } }',
 }
 for category in ['gfx','view','app']:
  body = 'atrace_apps: "zerolist.example"' if category == 'app' else 'atrace_categories: "'+category+'"'
  configs[category] = 'buffers { size_kb: 16384 }\nduration_ms: 9000\ndata_sources { config { name: "linux.ftrace" ftrace_config { '+body+' } } }'
for name,cfg in configs.items():
 f=O/(name+'.cfg');f.write_text(cfg);adb('push',str(f),'/data/misc/perfetto-configs/zl-'+name+'.cfg')
variants=['off','binding','ftrace','timeline','full'] if os.environ.get('STAGE') != 'categories' else ['off','sched','gfx','view','app']
if os.environ.get('VARIANTS'):variants=os.environ['VARIANTS'].split(',')
rows=[]
for rep in range(int(os.environ.get('REPEATS','3'))):
 for name in variants[rep:]+variants[:rep]:
  stem=str(rep+1)+'-'+name
  adb('shell','am','force-stop','zerolist.example')
  adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine','zigpool','--es','cell','heavy','--ei','count','100000','--es','diagnostic','trace-binding' if name=='binding' else 'normal','--ez','trace','true')
  time.sleep(3);pid=adb('shell','pidof','zerolist.example').decode().strip();adb('logcat','-c');adb('shell','dumpsys','gfxinfo','zerolist.example','reset')
  if name in configs:adb('shell','perfetto','--background-wait','--txt','-c','/data/misc/perfetto-configs/zl-'+name+'.cfg','-o','/data/misc/perfetto-traces/zl-probe.perfetto-trace')
  start=time.monotonic()
  for _ in range(12):adb('shell','input','swipe','540','1800','540','600','300')
  time.sleep(max(0,10-(time.monotonic()-start)))
  if name in configs:adb('pull','/data/misc/perfetto-traces/zl-probe.perfetto-trace',str(O/(stem+'.perfetto-trace')))
  gfx=adb('shell','dumpsys','gfxinfo','zerolist.example','framestats').decode();(O/(stem+'-gfx.txt')).write_text(gfx)
  (O/(stem+'.log')).write_bytes(adb('logcat','-d','--pid='+pid,'-v','brief','ZlBinding:I','ZlFrame:I','ReactNativeJS:I','*:S'))
  m=re.search(r'Janky frames: (\d+) \(([\d.]+)%\)',gfx);r={'run':rep+1,'probe':name,'jank_count':int(m[1]),'jank_percent':float(m[2]),'p95_ms':int(re.search(r'95th percentile: (\d+)ms',gfx)[1])};rows.append(r);(O/'results.json').write_text(json.dumps(rows,indent=2));print(r,flush=True)
