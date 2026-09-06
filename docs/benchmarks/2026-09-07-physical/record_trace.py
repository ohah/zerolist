"""제품 코드를 바꾸지 않고 모든 FrameMetrics와 선택적 view/sched 추적을 수집한다."""
from pathlib import Path
import os,subprocess,time,json,random,signal
D=Path(__file__).resolve().parent;O=Path(os.environ.get('OUT','/private/tmp/zerolist-physical-traces'));O.mkdir(exist_ok=False)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s',os.environ['ANDROID_SERIAL']]
def adb(*a):return subprocess.check_output(A+list(a),stderr=subprocess.STDOUT,timeout=45)
def host():
 raw=subprocess.check_output(['ps','-axo','pid=,pcpu=,comm='],text=True)
 return {'time':time.time(),'load':os.getloadavg(),'processes':[{'pid':int(v[0]),'cpu':float(v[1]),'name':Path(v[2]).name} for l in raw.splitlines() if len(v:=l.strip().split(None,2))==3 and float(v[1])>=5]}
def swipe(a,b,ms):adb('shell','input','swipe','540',str(a),'540',str(b),str(ms))
adb('shell','settings','put','system','user_rotation','0')
subprocess.run(['xcrun','simctl','terminate','ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D','zerolist.example'],capture_output=True)
adb('push',str(D/'trace.cfg'),'/data/misc/perfetto-configs/zl-pinpoint.cfg')
jobs=[]
jobs += [(f'trace-{x}',x,True) for x in ['zero','flat','before']]
(O/'conditions.json').write_text(json.dumps({'source':'74ed97a','physical_device':True,'model':'SM-S731N','refresh_hz':60,'rn':'0.87.1','count':100000,'cell':'heavy','bufferRows':5,'jsBlockMs':0,'renderer':adb('shell','getprop','debug.hwui.renderer').decode().strip(),'warmup_swipes':12,'measured_swipes':18,'jobs':jobs,'note':'모든 실행은 FrameMetrics 계측 진단이며 정식 비용 순위가 아님. gfx 추적은 켜지 않음.'},ensure_ascii=False,indent=2))
for name,variant,traced in jobs:
 time.sleep(10)
 adb('shell','am','force-stop','zerolist.example')
 adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine','flatlist' if variant=='flat' else 'zerolist','--es','diagnostic','pool-baseline' if variant=='before' else 'normal','--es','cell','heavy','--ei','count','100000','--ei','bufferRows','5','--ei','jsBlockMs','0','--ez','trace','true')
 time.sleep(3)
 for _ in range(12):swipe(1900,400,120)
 adb('shell','input','tap','540','1200');time.sleep(2)
 pid=adb('shell','pidof','zerolist.example').decode().strip()
 initial=adb('logcat','-d','--pid='+pid,'-v','brief','ReactNativeJS:I','*:S');(O/(name+'-startup.log')).write_bytes(initial);assert b'[ZlRuntime] rn=0.87.1' in initial
 adb('shell','dumpsys','gfxinfo','zerolist.example','reset')
 h=host();fh=(O/(name+'.log')).open('wb');log=subprocess.Popen(A+['logcat','--pid='+pid,'-T','1','-v','brief','ZlFrame:I','ReactNativeJS:I','AndroidRuntime:E','*:S'],stdout=fh,stderr=subprocess.STDOUT)
 try:
  if traced:adb('shell','perfetto','--background-wait','--txt','-c','/data/misc/perfetto-configs/zl-pinpoint.cfg','-o','/data/misc/perfetto-traces/zl-pinpoint.trace')
  start=time.monotonic()
  for n,a,b,ms in [(3,1800,600,300),(6,1900,400,120),(6,400,1900,120),(3,1800,600,300)]:
   for _ in range(n):swipe(a,b,ms)
  time.sleep(2)
  (O/(name+'-gfx.txt')).write_bytes(adb('shell','dumpsys','gfxinfo','zerolist.example','framestats'))
  if traced:
   time.sleep(max(0,16-(time.monotonic()-start)))
   adb('pull','/data/misc/perfetto-traces/zl-pinpoint.trace',str(O/(name+'.trace')))
 finally:
  log.terminate();log.wait(timeout=10);fh.close();adb('shell','am','force-stop','zerolist.example')
 (O/(name+'-host.json')).write_text(json.dumps([h,host()],indent=2));print(name,flush=True)
