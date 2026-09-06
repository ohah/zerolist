from pathlib import Path
import subprocess as s,time,os,signal
D=Path(os.environ.get('CONTRACT_OUT','/private/tmp/zerolist-unified-contract-new'));D.mkdir(exist_ok=False)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554'];U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
def run(*a,**kw):return s.run(a,check=True,stdout=s.PIPE,stderr=s.STDOUT,**kw).stdout
run(*A,'shell','am','force-stop','zerolist.example');run(*A,'shell','settings','put','system','user_rotation','0');run(*A,'logcat','-c')
run(*A,'shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','diagnostic','unified-contract','--es','engine','zerolist','--ei','count','100')
video=s.Popen(A+['shell','screenrecord','--time-limit','25','/sdcard/zerolist-unified-contract.mp4'],stdout=s.DEVNULL,stderr=s.DEVNULL)
t0=time.monotonic()
for t,name in [(5.5,'reorder'),(9.5,'replace'),(11.5,'scroll'),(21.5,'dynamic')]:
 time.sleep(max(0,t-(time.monotonic()-t0)));(D/f'android-{name}.png').write_bytes(run(*A,'exec-out','screencap','-p'))
video.wait(timeout=10);run(*A,'pull','/sdcard/zerolist-unified-contract.mp4',str(D/'android-contract.mp4'))
(D/'android.log').write_bytes(run(*A,'logcat','-d','-v','brief','ReactNativeJS:I','AndroidRuntime:E','*:S'));run(*A,'shell','am','force-stop','zerolist.example')
env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_DIAGNOSTIC='unified-contract',SIMCTL_CHILD_ZL_ENGINE='zerolist',SIMCTL_CHILD_ZL_COUNT='100')
f=(D/'ios.log').open('w');proc=s.Popen(['xcrun','simctl','launch','--terminate-running-process','--console',U,'zerolist.example'],env=env,stdout=f,stderr=s.STDOUT)
vid=s.Popen(['xcrun','simctl','io',U,'recordVideo',str(D/'ios-contract.mp4')],stdout=s.DEVNULL,stderr=s.DEVNULL);t0=time.monotonic()
for t,name in [(6,'reorder'),(10,'replace'),(12,'scroll'),(23,'dynamic')]:
 time.sleep(max(0,t-(time.monotonic()-t0)));run('xcrun','simctl','io',U,'screenshot',str(D/f'ios-{name}.png'))
vid.send_signal(signal.SIGINT);vid.wait(timeout=10)
run('xcrun','simctl','terminate',U,'zerolist.example');proc.wait(timeout=10);f.close();print('계약 화면 녹화·로그 수집 완료')
