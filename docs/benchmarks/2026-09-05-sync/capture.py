"""두 플랫폼의 이전/수정 동작을 녹화한다. 수치 측정과 동시에 실행하지 않는다."""
from pathlib import Path
import os,subprocess,time,signal,json,hashlib
P=Path(__file__).resolve().parent
RAW=Path(os.environ.get('RAW','/tmp/zerolist-sync-videos')).resolve();RAW.mkdir(parents=True,exist_ok=True)
A=[os.environ.get('ADB','/Users/yoonhb/Library/Android/sdk/platform-tools/adb'),'-s','emulator-5554']
U=os.environ.get('UDID','ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D')
def run(*args):return subprocess.run(list(args),capture_output=True,check=True,timeout=45).stdout
def adb(*args):return run(*A,*args)
def duration(p):return float(run('ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)))
manifest=json.loads((P/'capture-manifest.json').read_text()) if os.environ.get('RESUME') else []
for platform in ['android','ios']:
 for delay in [0,120]:
  for legacy in [True,False]:
   mode='legacy' if legacy else 'fixed';name=f'{platform}-{mode}-{delay}'
   if any(e['name']==name for e in manifest):continue
   if platform=='android':
    adb('shell','am','force-stop','zerolist.example')
    adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine','zigpool','--ei','count','100000','--es','cell','heavy','--ez','legacyRecycling',str(legacy).lower(),'--ei','bindingDelayMs',str(delay),'--ez','audit','false','--ez','trace','false','--ez','scrollIndicator','false')
   else:
    env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_ENGINE='zigpool',SIMCTL_CHILD_ZL_AUDIT='0',SIMCTL_CHILD_ZL_FRAMES='0',SIMCTL_CHILD_ZL_LEGACY='1' if legacy else '0',SIMCTL_CHILD_ZL_DELAY=str(delay))
    subprocess.run(['xcrun','simctl','launch','--terminate-running-process',U,'zerolist.example'],env=env,capture_output=True,check=True)
   time.sleep(4)
   if platform=='android':
    pid=adb('shell','pidof','zerolist.example').decode().strip()
    assert '[JS0] zigpool' in adb('logcat','-d','--pid='+pid,'ReactNativeJS:I','*:S').decode(errors='replace')
    (P/(name+'-before.png')).write_bytes(adb('exec-out','screencap','-p'))
    raw=RAW/(name+'.webm');start=time.monotonic()
    adb('emu','screenrecord','start','--size','540x1200','--fps','60','--bit-rate','4M','--time-limit','40',str(raw))
   else:
    hierarchy=json.loads(run('idb','ui','describe-all','--udid',U,'--json'))
    # 사용자 정의 네이티브 컨테이너는 idb에 하위 텍스트를 노출하지 않는다.
    # 앱 식별과 저장된 전후 화면의 육안 검사를 함께 사용한다.
    assert any(x.get('AXLabel')=='ZerolistExample' for x in hierarchy),name
    run('xcrun','simctl','io',U,'screenshot',str(P/(name+'-before.png')))
    raw=RAW/(name+'.mp4')
    recorder=subprocess.Popen(['xcrun','simctl','io',U,'recordVideo','--codec=h264','--force',str(raw)],stderr=subprocess.PIPE,text=True)
    for line in recorder.stderr:
     if 'Recording started' in line:break
    else:raise RuntimeError('Recorder did not start: '+name)
    start=time.monotonic()
   events=[]
   try:
    time.sleep(1.5)
    gestures=([(1800,600,500)]*2+[(1900,400,120)]*4+[(400,1900,120)]*3) if platform=='android' else ([(750,220,500)]*2+[(780,150,120)]*4+[(150,780,120)]*3)
    for y1,y2,ms in gestures:
     events.append({'t':time.monotonic()-start,'from_y':y1,'to_y':y2,'duration_ms':ms})
     if platform=='android':adb('shell','input','swipe','540',str(y1),'540',str(y2),str(ms))
     else:run('idb','ui','swipe','200',str(y1),'200',str(y2),'--duration',str(ms/1000),'--udid',U)
     time.sleep(.3)
    time.sleep(1.5)
   finally:
    elapsed=time.monotonic()-start
    if platform=='android':adb('emu','screenrecord','stop')
    else:recorder.send_signal(signal.SIGINT);recorder.wait(timeout=30)
   time.sleep(.3);seconds=duration(raw)
   assert abs(seconds-elapsed)<.3,(name,elapsed,seconds)
   if platform=='android':(P/(name+'-after.png')).write_bytes(adb('exec-out','screencap','-p'))
   else:run('xcrun','simctl','io',U,'screenshot',str(P/(name+'-after.png')))
   manifest.append({'name':name,'platform':platform,'legacy':legacy,'binding_delay_ms':delay,'source':str(raw),'wall_seconds':elapsed,'encoded_seconds':seconds,'events':events,'sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
   (P/'capture-manifest.json').write_text(json.dumps(manifest,indent=2));print('녹화 완료',name,elapsed,seconds,flush=True)
# 모든 녹화가 끝난 뒤에만 변환한다.
for entry in manifest:
 run('ffmpeg','-v','error','-y','-i',entry['source'],'-vf','scale=540:-2','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-fps_mode','passthrough','-movflags','+faststart',str(P/(entry['name']+'.mp4')))
print('COMPLETE')
