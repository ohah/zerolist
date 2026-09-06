"""공통 화면 검사와 메모리/CPU/프레임을 분리한 준비량 비교.
PLATFORM=android/ios MODE=audit/perf BLOCK_MS=160 REPEATS=1 CONFIGS=... OUT=새경로
"""
from pathlib import Path
import os,subprocess,time,re,json,math,statistics,struct
D=Path(os.environ['OUT']);D.mkdir(parents=True,exist_ok=True)
platform=os.getenv('PLATFORM','android');mode=os.getenv('MODE','audit');block=int(os.getenv('BLOCK_MS','160'));repeats=int(os.getenv('REPEATS','1'))
configs=[{'name':f'{e}-{b}','engine':e,'rows':b,'preparation':'baseline'} for e in ['flatlist','flashlist','legend','zerolist','zigpool'] for b in [2,5,12]]
configs += [{'name':f'stable-{b}','engine':'zigpool','rows':b,'preparation':'adaptive-stable'} for b in [5,12]]
if os.getenv('CONFIGS'):configs=[c for c in configs if c['name'] in os.environ['CONFIGS'].split(',')]
assert configs
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554'];U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
def run(*a):return subprocess.check_output(list(a),stderr=subprocess.STDOUT,timeout=60)
def adb(*a):return run(*(A+list(a)))
def p95(v):return sorted(v)[max(0,math.ceil(.95*len(v))-1)] if v else None
def memory(pid):
 if platform=='ios':return int(run('ps','-o','rss=','-p',str(pid)).strip())/1024
 return int(re.search(r'TOTAL PSS:\s+(\d+)',adb('shell','dumpsys','meminfo','zerolist.example').decode())[1])/1024
# 반대 플랫폼의 측정용 앱이 JS 부하를 계속 실행하지 않도록 정리한다.
if platform=='ios':
 adb('shell','am','force-stop','zerolist.example')
 assert not subprocess.run(A+['shell','pidof','zerolist.example'],capture_output=True).stdout.strip()
else:
 subprocess.run(['xcrun','simctl','terminate',U,'zerolist.example'],capture_output=True)
 assert subprocess.run(['pgrep','-x','ZerolistExample'],capture_output=True).returncode==1
clock_ticks=int(adb('shell','getconf','CLK_TCK').strip()) if platform=='android' else None
def cpu(pid):
 if platform=='android':
  f=adb('shell','cat',f'/proc/{pid}/stat').decode().rsplit(')',1)[1].split();return (int(f[11])+int(f[12]))/clock_ticks
 s=run('ps','-o','time=','-p',str(pid)).decode().strip();parts=s.split(':');return sum(float(v)*60**i for i,v in enumerate(reversed(parts)))
def swipe(reverse=False,fast=True):
 if platform=='android':
  a,b=(400,1900) if reverse else ((1900,400) if fast else (1800,600));adb('shell','input','swipe','540',str(a),'540',str(b),'120' if fast else '300')
 else:
  a,b=(150,780) if reverse else ((780,150) if fast else (750,220));run('idb','ui','swipe','200',str(a),'200',str(b),'--duration','.12' if fast else '.3','--udid',U)
def warmup():
 for _ in range(12):swipe()
 if platform=='android':adb('shell','input','tap','540','1200')
 else:run('idb','ui','tap','200','500','--udid',U)
 time.sleep(2)
def counts(raw):
 found=re.findall(r'\[JS0\].*?renders=(\d+) cbs=(\d+) mounts=(\d+) unmounts=(\d+)',raw)
 return dict(zip(['renders','callbacks','mounts','unmounts'],map(int,found[-1]))) if found else None
conditions={'platform':platform,'mode':mode,'configs':configs,'block_ms':block,'repeats':repeats,'count':100000,'cell':'heavy','warmup_swipes':12,'measured_swipes':18,'versions':{'react-native':'0.87.1','flash-list':'2.3.1','legend-list':'2.0.19'},'clock_ticks':clock_ticks,'initial_rows':'FlatList/ZeroList: ceil(viewport / rowHeight)','legend_fixed_hint':True,'other_platform_benchmark_app_stopped':True}
if platform=='android':
 size=struct.unpack('>II',adb('exec-out','screencap','-p')[16:24]);assert size==(1080,2400),size
 conditions.update(screen=size,renderer=adb('shell','getprop','debug.hwui.renderer').decode().strip(),atrace=adb('shell','getprop','debug.atrace.tags.enableflags').decode().strip())
resume=os.getenv('RESUME')=='1'
if resume:
 assert json.loads((D/'conditions.json').read_text())==conditions, 'resume conditions changed'
elif (D/'results.json').exists():raise RuntimeError('existing results; use a new path')
(D/'conditions.json').write_text(json.dumps(conditions,ensure_ascii=False,indent=2))
results=json.loads((D/'results.json').read_text()) if resume else []
for rep in range(repeats):
 order=configs[rep%len(configs):]+configs[:rep%len(configs)]
 for cfg in order:
  if any(r['run']==rep+1 and r['name']==cfg['name'] for r in results):continue
  name=f'{rep+1}-{cfg["name"]}';path=D/f'{name}.log'
  if resume and path.exists():path.rename(path.with_suffix('.failed-'+str(time.time_ns())+'.log'))
  assert not path.exists(),path
  proc=None;handle=None
  if platform=='android':
   adb('shell','am','force-stop','zerolist.example')
   adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',cfg['engine'],'--es','preparation',cfg['preparation'],'--ei','bufferRows',str(cfg['rows']),'--ei','count','100000','--es','cell','heavy','--ei','jsBlockMs',str(block),'--ez','commonAudit',str(mode=='audit').lower(),'--ez','audit',str(os.getenv('CROSS_AUDIT','0')=='1').lower(),'--ez','preparationTrace',str(mode=='audit').lower())
   time.sleep(3);warmup();pid=int(adb('shell','pidof','zerolist.example').strip())
   initial=adb('logcat','-d','--pid='+str(pid),'-v','brief','ReactNativeJS:I','*:S').decode();initial_counts=counts(initial)
   adb('logcat','-c');adb('shell','dumpsys','gfxinfo','zerolist.example','reset')
  else:
   env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_COUNT='100000',SIMCTL_CHILD_ZL_CELL='heavy',SIMCTL_CHILD_ZL_ENGINE=cfg['engine'],SIMCTL_CHILD_ZL_PREPARATION=cfg['preparation'],SIMCTL_CHILD_ZL_BUFFER_ROWS=str(cfg['rows']),SIMCTL_CHILD_ZL_COMMON_AUDIT=str(int(mode=='audit')),SIMCTL_CHILD_ZL_AUDIT=os.getenv('CROSS_AUDIT','0'),SIMCTL_CHILD_ZL_PREPARATION_TRACE=str(int(mode=='audit')),SIMCTL_CHILD_ZL_FRAMES='1',SIMCTL_CHILD_ZL_BLOCK_MS=str(block),SIMCTL_CHILD_ZL_DELAY='0',SIMCTL_CHILD_ZL_LEGACY='0')
   handle=path.open('a');proc=subprocess.Popen(['xcrun','simctl','launch','--terminate-running-process','--console',U,'zerolist.example'],env=env,stdout=handle,stderr=subprocess.STDOUT)
   time.sleep(3);warmup();initial=path.read_text();m=re.search(r'ZerolistExample\[(\d+):',initial);assert m,name
   pid=int(m[1]);initial_counts=counts(initial);start=path.stat().st_size
  if '[ZlRuntime] rn=0.87.1' not in initial:
   if proc:
    run('xcrun','simctl','terminate',U,'zerolist.example');proc.wait(timeout=15);handle.close()
   else:adb('shell','am','force-stop','zerolist.example')
   raise RuntimeError(('native RN version not verified', name))
  before=memory(pid);cpu0=cpu(pid);wall0=time.monotonic()
  try:
   for phase,n,reverse,fast in [('normal',3,False,False),('fast',6,False,True),('reverse',6,True,True),('settle',3,False,False)]:
    for _ in range(n):swipe(reverse,fast)
   time.sleep(2)
   cpu1=cpu(pid);elapsed=time.monotonic()-wall0;after=memory(pid)
   if platform=='android':
    raw=adb('logcat','-d','-v','brief','ZlCommon:I','ZlAudit:I','ZlPrepare:I','ReactNativeJS:I','*:S').decode();path.write_text(raw)
    gfx=adb('shell','dumpsys','gfxinfo','zerolist.example','framestats').decode();(D/f'{name}-gfx.txt').write_text(gfx)
   else:raw=path.read_bytes()[start:].decode(errors='replace')
  finally:
   if proc:run('xcrun','simctl','terminate',U,'zerolist.example');proc.wait(timeout=15);handle.close()
   else:adb('shell','am','force-stop','zerolist.example')
  c=counts(raw)
  row=dict(cfg,run=rep+1,mode=mode,block_ms=block,memory_before_mib=before,memory_after_mib=after,cpu_seconds=cpu1-cpu0,wall_seconds=elapsed,cpu_one_core_percent=(cpu1-cpu0)/elapsed*100,initial_counts=initial_counts,final_counts=c)
  row['work']={k:c[k]-initial_counts[k] for k in c} if c and initial_counts else None
  if mode=='audit':
   fs=[]
   for line in raw.splitlines():
    if 'ZlCommon' in line and 'frame=' in line:fs.append({k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',line)})
   assert len(fs)>50,(name,'검사 프레임 부족',len(fs))
   moving=[b for a,b in zip(fs,fs[1:]) if abs(b['y']-a['y'])>.1]
   entered=sum(f['entered'] for f in fs);unready=sum(f['unready'] for f in fs)
   blanks=[max(0,f['blank']-2)/f['viewport']*100 for f in moving]
   row.update(frames=len(fs),moving_frames=len(moving),entry_ready_percent=(entered-unready)/entered*100 if entered else None,entered=entered,unready=unready,blank_moving_percent=sum(f['blank']>2 for f in moving)/len(moving)*100,mean_blank_area_percent=statistics.mean(blanks),max_blank_area_percent=max(blanks),wrong_frames=sum(f['wrong']>0 for f in fs),overlap_frames=sum(f['overlap']>2 for f in fs),last_blank_px=fs[-1]['blank'],scroll_min=min(f['y'] for f in fs),scroll_max=max(f['y'] for f in fs),attached_max=max(f['attached'] for f in fs),travel_rows=sum(abs(b['y']-a['y'])/b['rh'] for a,b in zip(fs,fs[1:])))
   assert row['scroll_max']-row['scroll_min']>1000,(name,'이동 부족')
   assert c and row['work']['renders']>0,(name,'내용 갱신 없음')
   bs=[float(v) for v in re.findall(r'\[ZlBlock\] elapsed=([\d.]+)',raw)];row['block_samples']=len(bs);row['block_median_ms']=statistics.median(bs) if bs else None
   if block:assert len(bs)>5 and statistics.median(bs)>=block,(name,'JS 부하 없음')
  elif platform=='android':
   m=re.search(r'Janky frames: (\d+) \(([\d.]+)%\)',gfx);total=int(re.search(r'Total frames rendered: (\d+)',gfx)[1]);assert total>100
   row.update(frames=total,late=int(m[1]),late_percent=float(m[2]),p95_ms=int(re.search(r'95th percentile: (\d+)ms',gfx)[1]))
   assert c and row['work']['renders']>0,(name,'내용 갱신 없음')
  else:
   fs=[];downs=[];ups=[];positions=[]
   for line in raw.splitlines():
    d={k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',line)}
    if 'ZlFrame ios' in line:fs.append(d)
    if 'ZlTouch action=' in line:
     (downs if d['action']==0 else ups).append(d['timestamp']);positions.append(d.get('y',-1))
   assert len(downs)==18 and len(ups)==18,(name,'입력 부족')
   assert max(positions)-min(positions)>1000,(name,'이동 부족')
   pairs=[(a,b) for a,b in zip(fs,fs[1:]) if downs[0]<=b['timestamp']<=ups[-1]+1.2]
   row.update(scroll_min=min(positions),scroll_max=max(positions),callbacks=len(pairs),late_callback_percent=sum(b['timestamp']-a['timestamp']>1.5*(a['target']-a['timestamp']) for a,b in pairs)/len(pairs)*100,callback_p95_ms=p95([(b['timestamp']-a['timestamp'])*1000 for a,b in pairs]))
  results.append(row);(D/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(row,ensure_ascii=False),flush=True)
