"""비슷한 메모리 구간의 후보를 실제 JS 160ms/40ms 부하에서 별도로 녹화한다.
정량 시험 종료 후 실행한다. 서로 다른 실행이며 프레임별 동기 비교가 아니다.
"""
from pathlib import Path
import os,subprocess,time,signal,json,hashlib
D=Path(__file__).resolve().parent;R=Path('/private/tmp/zerolist-rn087-videos');R.mkdir(exist_ok=True)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554'];U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
def run(*a):return subprocess.check_output(list(a),stderr=subprocess.STDOUT,timeout=60)
def adb(*a):return run(*A,*a)
def duration(p):return float(run('ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)))
def swipe(platform,a,b,ms):
 if platform=='android':adb('shell','input','swipe','540',str(a),'540',str(b),str(ms))
 else:run('idb','ui','swipe','200',str(a),'200',str(b),'--duration',str(ms/1000),'--udid',U)
manifest=[]
for platform in ['android','ios']:
 for engine,rows,variant in ([('flatlist',5,'baseline'),('flashlist',2,'baseline'),('zigpool',5,'baseline')] if platform=='android' else [('flatlist',5,'baseline'),('flashlist',12,'baseline'),('zigpool',12,'adaptive-stable')]):
  name=f'{platform}-{engine}-{rows}-block'
  if platform=='android':
   adb('shell','am','force-stop','zerolist.example')
   adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--ei','bufferRows',str(rows),'--ei','jsBlockMs','160','--es','preparation',variant,'--ei','count','100000','--es','cell','heavy','--ei','bindingDelayMs','0')
  else:
   env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_COUNT='100000',SIMCTL_CHILD_ZL_CELL='heavy',SIMCTL_CHILD_ZL_ENGINE=engine,SIMCTL_CHILD_ZL_BUFFER_ROWS=str(rows),SIMCTL_CHILD_ZL_COMMON_AUDIT='0',SIMCTL_CHILD_ZL_PREPARATION=variant,SIMCTL_CHILD_ZL_DELAY='0',SIMCTL_CHILD_ZL_AUDIT='0',SIMCTL_CHILD_ZL_FRAMES='0',SIMCTL_CHILD_ZL_PREPARATION_TRACE='0',SIMCTL_CHILD_ZL_BLOCK_MS='160',SIMCTL_CHILD_ZL_LEGACY='0')
   subprocess.run(['xcrun','simctl','launch','--terminate-running-process',U,'zerolist.example'],env=env,check=True,capture_output=True)
  time.sleep(3)
  for _ in range(12):swipe(platform,1900 if platform=='android' else 780,400 if platform=='android' else 150,120)
  if platform=='android':adb('shell','input','tap','540','1200')
  else:run('idb','ui','tap','200','500','--udid',U)
  time.sleep(2)
  if platform=='android':
   raw=R/(name+'.webm');start=time.monotonic()
   adb('emu','screenrecord','start','--size','540x1200','--fps','60','--bit-rate','4M','--time-limit','35',str(raw))
  else:
   raw=R/(name+'.mp4');recorder=subprocess.Popen(['xcrun','simctl','io',U,'recordVideo','--codec=h264','--force',str(raw)],stderr=subprocess.PIPE,text=True)
   for line in recorder.stderr:
    if 'Recording started' in line:break
   else:raise RuntimeError('녹화 시작 실패')
   start=time.monotonic()
  events=[]
  try:
   time.sleep(1)
   phases=[('normal',3,False,300),('fast',6,False,120),('reverse',6,True,120),('settle',3,False,300)]
   for phase,n,reverse,ms in phases:
    for _ in range(n):
     a,b=((400,1900) if reverse else ((1900,400) if ms<200 else (1800,600))) if platform=='android' else ((150,780) if reverse else ((780,150) if ms<200 else (750,220)))
     events.append({'t':time.monotonic()-start,'phase':phase,'duration_ms':ms})
     swipe(platform,a,b,ms)
   time.sleep(2)
  finally:
   elapsed=time.monotonic()-start
   if platform=='android':adb('emu','screenrecord','stop')
   else:recorder.send_signal(signal.SIGINT);recorder.wait(timeout=30)
  seconds=duration(raw)
  if abs(seconds-elapsed)>.35:raise RuntimeError((name,seconds,elapsed))
  manifest.append({'name':name,'platform':platform,'engine':engine,'buffer_rows':rows,'variant':variant,'delay_ms':0,'js_block_ms':160,'source':str(raw),'seconds':seconds,'wall_seconds':elapsed,'events':events,'sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
  (D/'capture-manifest.json').write_text(json.dumps(manifest,indent=2));print('녹화',name,seconds,flush=True)
  if platform=='android':adb('shell','am','force-stop','zerolist.example')
  else:run('xcrun','simctl','terminate',U,'zerolist.example')
for r in manifest:
 out=D/(r['name']+'.mp4')
 run('ffmpeg','-v','error','-y','-i',r['source'],'-vf','scale=540:-2','-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-fps_mode','passthrough','-movflags','+faststart',str(out))
 run('ffmpeg','-v','error','-i',str(out),'-f','null','-')
