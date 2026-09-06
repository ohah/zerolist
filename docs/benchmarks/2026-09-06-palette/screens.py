"""성능 측정과 분리한 실제 화면 캡처. 64개 칸의 색·위치를 비교한다."""
from pathlib import Path
import subprocess,os,time,json
D=Path(__file__).resolve().parent;out=D/'screens';out.mkdir(exist_ok=True)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554'];U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
def run(*a):return subprocess.check_output(a,stderr=subprocess.STDOUT,timeout=60)
for platform in ['ios','android']:
 if platform=='ios':run(*A,'shell','am','force-stop','zerolist.example')
 else:subprocess.run(['xcrun','simctl','terminate',U,'zerolist.example'],capture_output=True)
 for engine in ['flatlist','flatlist-palette','template-compact','template-palette']:
  if platform=='ios':
   env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_ENGINE=engine,SIMCTL_CHILD_ZL_COUNT='100000',SIMCTL_CHILD_ZL_CELL='heavy',SIMCTL_CHILD_ZL_BUFFER_ROWS='5',SIMCTL_CHILD_ZL_BLOCK_MS='0',SIMCTL_CHILD_ZL_AUDIT='0',SIMCTL_CHILD_ZL_COMMON_AUDIT='0',SIMCTL_CHILD_ZL_FRAMES='0',SIMCTL_CHILD_ZL_DIAGNOSTIC='normal')
   subprocess.run(['xcrun','simctl','launch','--terminate-running-process',U,'zerolist.example'],env=env,check=True,capture_output=True)
  else:
   run(*A,'shell','am','force-stop','zerolist.example')
   run(*A,'shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--ei','count','100000','--es','cell','heavy','--ei','bufferRows','5','--ei','jsBlockMs','0')
  time.sleep(3)
  for step in ['initial','after-scroll']:
   if step=='after-scroll':
    if platform=='ios':run('idb','ui','swipe','200','780','200','150','--duration','.3','--udid',U);run('idb','ui','tap','200','500','--udid',U)
    else:run(*A,'shell','input','swipe','540','1900','540','400','300');run(*A,'shell','input','tap','540','1200')
    time.sleep(1)
   p=out/f'{platform}-{engine}-{step}.png'
   if platform=='ios':run('xcrun','simctl','io',U,'screenshot',str(p))
   else:p.write_bytes(run(*A,'exec-out','screencap','-p'))
  if platform=='ios':run('xcrun','simctl','terminate',U,'zerolist.example')
  else:run(*A,'shell','am','force-stop','zerolist.example')
  print(platform,engine,'captured',flush=True)
