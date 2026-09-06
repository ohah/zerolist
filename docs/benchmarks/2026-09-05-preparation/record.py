"""내용 준비 PoC 행렬. PLATFORM=android/ios, MODE=audit/perf.
정확성·준비 시간은 audit에서, 지연 프레임·메모리는 별도 perf에서 수집한다.
"""
from pathlib import Path
import os, subprocess, time, re, json, struct, statistics

D=Path(os.environ.get('OUT','/private/tmp/zerolist-preparation'));D.mkdir(parents=True,exist_ok=True)
platform=os.environ.get('PLATFORM','android'); mode=os.environ.get('MODE','audit')
variants=os.environ.get('VARIANTS','baseline,wide,adaptive-small,adaptive,coalesce,memo,combined,adaptive-stable,combined-stable').split(',')
delays=[int(x) for x in os.environ.get('DELAYS','0,120,400' if mode=='audit' else '0').split(',')]
repeats=int(os.environ.get('REPEATS','1' if mode=='audit' else '3'))
A=[os.environ.get('ADB','/Users/yoonhb/Library/Android/sdk/platform-tools/adb'),'-s','emulator-5554']
U=os.environ.get('UDID','ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D')
def run(*args):return subprocess.check_output(list(args),stderr=subprocess.STDOUT,timeout=60)
def adb(*args):return run(*(A+list(args)))
def warmup():
 for _ in range(int(os.environ.get('WARMUP','12'))):
  if platform=='android':adb('shell','input','swipe','540','1900','540','400','120')
  else:run('idb','ui','swipe','200','780','200','150','--duration','.12','--udid',U)
 if int(os.environ.get('WARMUP','12')):
  if platform=='android':adb('shell','input','tap','540','1200')
  else:run('idb','ui','tap','200','500','--udid',U)
  time.sleep(2)
def memory(pid):
 if platform=='ios':return int(run('ps','-o','rss=','-p',str(pid)).strip())/1024
 raw=adb('shell','dumpsys','meminfo','zerolist.example').decode()
 m=re.search(r'TOTAL PSS:\s+(\d+)',raw)
 if not m:raise RuntimeError('PSS 없음')
 return int(m[1])/1024
if platform=='android':
 screen=adb('exec-out','screencap','-p');size=struct.unpack('>II',screen[16:24])
 if size!=(1080,2400):raise RuntimeError(f'세로 1080x2400 필요: {size}')
 conditions={'screen':size,'renderer':adb('shell','getprop','debug.hwui.renderer').decode().strip(),'atrace':adb('shell','getprop','debug.atrace.tags.enableflags').decode().strip()}
else:conditions={'udid':U,'frame_metric':'CADisplayLink 시각 간격: 실제 표시 지연 아님'}
conditions.update(platform=platform,mode=mode,variants=variants,delays=delays,repeats=repeats,count=100000,cell='heavy',js_block_ms=int(os.environ.get('BLOCK_MS','0')),scenario=os.environ.get('SCENARIO','mixed'),warmup_swipes=int(os.environ.get('WARMUP','12')),memory='시작/종료 PSS' if platform=='android' else '시작/종료 RSS')
(D/'conditions.json').write_text(json.dumps(conditions,ensure_ascii=False,indent=2))
def percentile(values,q):
 return sorted(values)[max(0,int(__import__('math').ceil(len(values)*q))-1)] if values else None
results=[]
for rep in range(repeats):
 order=variants[rep%len(variants):]+variants[:rep%len(variants)]
 for delay in delays:
  for variant in order:
   name=f'{rep+1}-{variant}-{delay}'; engine='flatlist' if variant=='flatlist' else 'zigpool'
   logpath=D/(name+'.log'); proc=None; handle=None
   if logpath.exists():raise RuntimeError('새 OUT 경로를 사용하세요: '+str(logpath))
   if platform=='android':
    adb('shell','am','force-stop','zerolist.example')
    adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--es','preparation',variant,'--ei','count','100000','--es','cell','heavy','--ei','jsBlockMs',os.environ.get('BLOCK_MS','0'),'--ei','bindingDelayMs',str(delay),'--ez','audit',str(mode=='audit').lower(),'--ez','preparationTrace',str(mode=='audit').lower())
    time.sleep(3);warmup();pid=int(adb('shell','pidof','zerolist.example').strip());before=memory(pid) if mode=='perf' else None
    initial=adb('logcat','-d','--pid='+str(pid),'-v','brief','ReactNativeJS:I','*:S').decode()
    initial_counts=re.findall(r'renders=(\d+)',initial);initial_renders=int(initial_counts[-1]) if initial_counts else 0
    adb('logcat','-c');adb('shell','dumpsys','gfxinfo','zerolist.example','reset')
   else:
    env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_ENGINE=engine,SIMCTL_CHILD_ZL_PREPARATION=variant,SIMCTL_CHILD_ZL_AUDIT=str(int(mode=='audit')),SIMCTL_CHILD_ZL_PREPARATION_TRACE=str(int(mode=='audit')),SIMCTL_CHILD_ZL_FRAMES=str(int(mode=='perf')),SIMCTL_CHILD_ZL_BLOCK_MS=os.environ.get('BLOCK_MS','0'),SIMCTL_CHILD_ZL_DELAY=str(delay),SIMCTL_CHILD_ZL_LEGACY='0')
    handle=logpath.open('a');proc=subprocess.Popen(['xcrun','simctl','launch','--terminate-running-process','--console',U,'zerolist.example'],env=env,stdout=handle,stderr=subprocess.STDOUT)
    time.sleep(3);warmup();raw=logpath.read_text();m=re.search(r'ZerolistExample\[(\d+):',raw)
    if not m:raise RuntimeError('iOS 앱 시작 로그 없음: '+name)
    pid=int(m[1]);before=memory(pid) if mode=='perf' else None
    initial_counts=re.findall(r'renders=(\d+)',raw);initial_renders=int(initial_counts[-1]) if initial_counts else 0
    start=logpath.stat().st_size
   phases=[('normal',3,False,.3),('fast',6,False,.12),('reverse',6,True,.12),('settle',3,False,.3)] if mode=='audit' or os.environ.get('SCENARIO','mixed')=='mixed' else [('normal',12,False,.3)]
   try:
    for phase,number,reverse,duration in phases:
     if mode=='audit':
      if platform=='android':adb('shell','log','-t','ZlPhase',phase)
      else:handle.write('\nZlPhase '+phase+'\n');handle.flush()
     for _ in range(number):
      if platform=='android':
       a,b=(400,1900) if reverse else ((1900,400) if duration<.2 else (1800,600))
       adb('shell','input','swipe','540',str(a),'540',str(b),str(int(duration*1000)))
      else:
       a,b=(150,780) if reverse else ((780,150) if duration<.2 else (750,220))
       run('idb','ui','swipe','200',str(a),'200',str(b),'--duration',str(duration),'--udid',U)
    time.sleep(2 if mode=='audit' else 1.2)
    if platform=='android':
     raw=adb('logcat','-d','-v','brief','ZlAudit:I','ZlPrepare:I','ZlPhase:I','ReactNativeJS:I','*:S').decode();logpath.write_text(raw)
     gfx=adb('shell','dumpsys','gfxinfo','zerolist.example','framestats').decode();(D/(name+'-gfx.txt')).write_text(gfx)
    else:raw=logpath.read_bytes()[start:].decode(errors='replace')
    after=memory(pid) if mode=='perf' else None
   finally:
    if proc:
     run('xcrun','simctl','terminate',U,'zerolist.example');proc.wait(timeout=15);handle.close()
   if platform=='android' and not re.search(r'renders=(?:[2-9]\d*|1\d+)',raw):raise RuntimeError('내용 갱신 없음: '+name)
   row={'run':rep+1,'variant':variant,'delay_ms':delay,'js_block_ms':int(os.environ.get('BLOCK_MS','0'))}
   blocks=[float(v) for v in re.findall(r'\[ZlBlock\] elapsed=([\d.]+)',raw)]
   if mode=='audit' and row['js_block_ms'] and not blocks:raise RuntimeError('JS 부하 기록 없음')
   row['block_samples']=len(blocks);row['block_median_ms']=statistics.median(blocks) if blocks else None
   if mode=='audit':
    frames=[];latencies=[];requests=0;phase='normal';byphase={}
    request_versions={int(re.search(r'version=(\d+)',l)[1]) for l in raw.splitlines() if 'ZlPrepare' in l and 'phase=request' in l}
    for line in raw.splitlines():
     if 'ZlPhase' in line:
      phase=line.split()[-1];continue
     values={k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',line)}
     if 'ZlAudit' in line and 'frame=' in line:
      frames.append(values);byphase.setdefault(phase,[]).append(values)
     if 'ZlPrepare' in line and 'phase=ready' in line and int(values['version']) in request_versions:latencies.append(values['elapsed'])
     if 'ZlPrepare' in line and 'phase=request' in line:requests+=1
    if len(frames)<50 or not latencies:raise RuntimeError('진단 자료 부족: '+name)
    def summary(fs):
     moving=[b for a,b in zip(fs,fs[1:]) if b['y']!=a['y']]
     entered=sum(f['entered'] for f in fs);unready=sum(f['unready'] for f in fs)
     return {'frames':len(fs),'moving_frames':len(moving),'blank_moving_frames':sum(f['blank']>2 for f in moving),'wrong_frames':sum(f['wrong']>0 for f in fs),'overlap_frames':sum(f['overlap']>2 for f in fs),'entered':entered,'unready':unready,'entry_ready_percent':(entered-unready)/entered*100 if entered else None,'max_blank_px':max(f['blank'] for f in fs),'last_blank_px':fs[-1]['blank']}
    row.update(summary(frames));row.update(requests=requests,completed=len(latencies),ready_p50_ms=statistics.median(latencies),ready_p95_ms=percentile(latencies,.95),phases={p:summary(fs) for p,fs in byphase.items()})
   else:
    row.update(memory_before_mib=before,memory_after_mib=after)
    if platform=='android':
     total=int(re.search(r'Total frames rendered: (\d+)',gfx)[1]);m=re.search(r'Janky frames: (\d+) \(([\d.]+)%\)',gfx)
     if total<100:raise RuntimeError('프레임 부족: '+name)
     row.update(frames=total,late=int(m[1]),late_percent=float(m[2]),p95_ms=int(re.search(r'95th percentile: (\d+)ms',gfx)[1]))
    else:
     fs=[];downs=[];ups=[];positions=[]
     for line in raw.splitlines():
      d={k:float(v) for k,v in re.findall(r'(\w+)=([\d.]+)',line)}
      if 'ZlFrame ios' in line:fs.append(d)
      if 'ZlTouch action=' in line:
       (downs if d['action']==0 else ups).append(d['timestamp']);positions.append(d.get('y',-1))
     if len(downs)!=sum(p[1] for p in phases) or len(ups)!=sum(p[1] for p in phases):raise RuntimeError('iOS 입력 부족: '+name)
     if not positions or max(positions)-min(positions)<100:raise RuntimeError('실제 iOS 스크롤 이동 없음')
     row['scroll_min']=min(positions);row['scroll_max']=max(positions)
     pairs=[(a,b) for a,b in zip(fs,fs[1:]) if downs[0]<=b['timestamp']<=ups[-1]+1.2]
     gaps=[(b['timestamp']-a['timestamp'])*1000 for a,b in pairs]
     row.update(callbacks=len(pairs),late_callback_percent=sum(b['timestamp']-a['timestamp']>1.5*(a['target']-a['timestamp']) for a,b in pairs)/len(pairs)*100,callback_p95_ms=percentile(gaps,.95))
   counts=[int(m) for m in re.findall(r'renders=(\d+)',raw)];row['renders_last']=counts[-1] if counts else None;row['renders_initial']=initial_renders;row['renders_during']=counts[-1]-initial_renders if counts else None
   results.append(row);(D/'results.json').write_text(json.dumps(results,indent=2));print({k:v for k,v in row.items() if k!='phases'},flush=True)
