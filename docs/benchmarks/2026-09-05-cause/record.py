"""원인 분리용 추적. 감사/녹화와 병행하지 않으며 정식 성능 순위에 합치지 않는다."""
from pathlib import Path
import subprocess,time,os,json
P=Path(__file__).resolve().parent
O=Path(os.environ.get('OUT','/private/tmp/zerolist-cause'));O.mkdir(parents=True,exist_ok=True)
A=[os.environ.get('ADB','/Users/yoonhb/Library/Android/sdk/platform-tools/adb'),'-s','emulator-5554']
def adb(*args):return subprocess.check_output(A+list(args),timeout=40)
adb('push',str(P/'trace.cfg'),'/data/misc/perfetto-configs/zl-cause.cfg')
variants=[('flatlist','flatlist','heavy','normal'),('zigpool','zigpool','heavy','trace-binding'),('frozen','zigpool','heavy','freeze-content'),('simple','zigpool','simple','trace-binding')]
for name,engine,cell,diagnostic in variants:
 adb('shell','am','force-stop','zerolist.example')
 adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--es','cell',cell,'--ei','count','100000','--es','diagnostic',diagnostic,'--ez','trace','true')
 time.sleep(3)
 pid=adb('shell','pidof','zerolist.example').decode().strip()
 adb('logcat','-c');adb('shell','dumpsys','gfxinfo','zerolist.example','reset')
 adb('shell','perfetto','--background-wait','--txt','-c','/data/misc/perfetto-configs/zl-cause.cfg','-o','/data/misc/perfetto-traces/zl-'+name+'.perfetto-trace')
 events=[];start=time.monotonic()
 for _ in range(12):
  events.append(time.monotonic()-start)
  adb('shell','input','swipe','540','1800','540','600','300')
 time.sleep(max(0,10-(time.monotonic()-start)))
 adb('pull','/data/misc/perfetto-traces/zl-'+name+'.perfetto-trace',str(O/(name+'.perfetto-trace')))
 (O/(name+'.log')).write_bytes(adb('logcat','-d','--pid='+pid,'-v','brief','ZlBinding:I','ZlFrame:I','ReactNativeJS:I','*:S'))
 (O/(name+'-gfx.txt')).write_bytes(adb('shell','dumpsys','gfxinfo','zerolist.example','framestats'))
 (O/(name+'-gestures.json')).write_text(json.dumps(events))
 print('추적 완료',name,flush=True)
