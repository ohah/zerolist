"""iOS 시뮬레이터 보조 측정: UI 화면 갱신 콜백 간격과 프로세스 RSS.
실제 GPU 프레임 지연률이 아니다. 녹화/정확성 검사/다른 기기 측정과 분리한다.
"""
import os,subprocess,time,pathlib,json,re,statistics
P=pathlib.Path(os.environ.get('OUT','/tmp/zerolist-perf-ios'));P.mkdir(exist_ok=True,parents=True)
U=os.environ.get('UDID','ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D')
variants=['flatlist','legend','flashlist','zerolist','zigpool','zigpool-legacy']
if os.environ.get('VARIANTS'):variants=os.environ['VARIANTS'].split(',')
def run(*args):return subprocess.run(list(args),capture_output=True,check=True,timeout=45)
def rss(pid):return int(run('ps','-o','rss=','-p',str(pid)).stdout.strip())/1024
results=[]
for rep in range(int(os.environ.get('REPEATS','5'))):
 shift=rep%len(variants)
 for variant in variants[shift:]+variants[:shift]:
  name=f'{rep+1}-{variant}';engine='zigpool' if variant=='zigpool-legacy' else variant
  env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_ENGINE=engine,SIMCTL_CHILD_ZL_FRAMES='1',SIMCTL_CHILD_ZL_LEGACY='1' if variant=='zigpool-legacy' else '0',SIMCTL_CHILD_ZL_AUDIT='0',SIMCTL_CHILD_ZL_DELAY='0')
  logPath=P/(name+'.log')
  with logPath.open('w') as log:
   proc=subprocess.Popen(['xcrun','simctl','launch','--terminate-running-process','--console',U,'zerolist.example'],env=env,stdout=log,stderr=subprocess.STDOUT)
   try:
    time.sleep(3)
    text=logPath.read_text();match=re.search(r'ZerolistExample\[(\d+):',text)
    if not match or 'ZlFrame ios' not in text:raise RuntimeError('No frame probe: '+name)
    pid=int(match[1]);before=rss(pid);samples=[]
    for _ in range(12):
     run('idb','ui','swipe','200','750','200','220','--duration','.3','--udid',U)
     samples.append(rss(pid))
    time.sleep(1.2);after=rss(pid)
    if rep==0:run('xcrun','simctl','io',U,'screenshot',str(P/(name+'.png')))
   finally:
    run('xcrun','simctl','terminate',U,'zerolist.example');proc.wait(timeout=15)
  frames=[];downs=[];ups=[]
  for line in logPath.read_text().splitlines():
   d={k:float(v) for k,v in re.findall(r'(\w+)=([\d.]+)',line)}
   if 'ZlFrame ios' in line:frames.append(d)
   if 'ZlTouch action=' in line:(downs if d['action']==0 else ups).append(d['timestamp'])
  if len(downs)!=12 or len(ups)!=12:raise RuntimeError('Input count: '+name+str((len(downs),len(ups))))
  intervals=[];late=0
  for a,b in zip(frames,frames[1:]):
   if downs[0]<=b['timestamp']<=ups[-1]+1.2:
    gap=b['timestamp']-a['timestamp'];budget=a['target']-a['timestamp']
    intervals.append(gap*1000);late+=gap>budget*1.5
  if not intervals:raise RuntimeError('No frame intervals')
  vals=sorted(intervals)
  r={'run':rep+1,'variant':variant,'callbacks':len(vals),'late_callbacks':late,'late_callback_percent':late/len(vals)*100,'callback_p50_ms':statistics.median(vals),'callback_p95_ms':vals[int(.95*(len(vals)-1))],'callback_max_ms':max(vals),'rss_before_mib':before,'rss_after_mib':after,'rss_sampled_peak_mib':max([before,after]+samples),'rss_samples_mib':samples,'note':'UI callback intervals, not presented frames or GPU deadlines; RSS is sampled simulator process memory, not peak device memory.'}
  results.append(r);(P/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['rss_samples_mib','note']}),flush=True)
print('COMPLETE')
