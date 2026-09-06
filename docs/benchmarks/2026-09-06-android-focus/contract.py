from pathlib import Path
import subprocess as s,time,os,signal
D=Path(os.environ.get('CONTRACT_OUT','/private/tmp/zerolist-android-focus-contract'));D.mkdir(exist_ok=False)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554'];U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
def run(*a,**kw):return s.run(a,check=True,stdout=s.PIPE,stderr=s.STDOUT,**kw).stdout
run(*A,'shell','am','force-stop','zerolist.example');run(*A,'shell','settings','put','system','user_rotation','0');run(*A,'logcat','-c')
run(*A,'shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','diagnostic','unified-contract','--es','engine','zerolist','--ei','count','100')
video=s.Popen(A+['shell','screenrecord','--time-limit','25','/sdcard/zerolist-android-focus-contract.mp4'],stdout=s.DEVNULL,stderr=s.DEVNULL)
t0=time.monotonic()
for t,name in [(5.5,'reorder'),(9.5,'replace'),(11.5,'scroll'),(21.5,'dynamic')]:
 time.sleep(max(0,t-(time.monotonic()-t0)));(D/f'android-{name}.png').write_bytes(run(*A,'exec-out','screencap','-p'))
video.wait(timeout=10);run(*A,'pull','/sdcard/zerolist-android-focus-contract.mp4',str(D/'android-contract.mp4'))
(D/'android.log').write_bytes(run(*A,'logcat','-d','-v','brief','ReactNativeJS:I','AndroidRuntime:E','*:S'));run(*A,'shell','am','force-stop','zerolist.example')
run(*A,'logcat','-c')
run(*A,'shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','diagnostic','android-pool-contract','--es','engine','zerolist','--ei','count','100')
video=s.Popen(A+['shell','screenrecord','--time-limit','23','/sdcard/zerolist-android-focus-far.mp4'],stdout=s.DEVNULL,stderr=s.DEVNULL)
t0=time.monotonic()
for t,name in [(3.8,'far'),(4.3,'tap'),(7.8,'insert'),(10.8,'shrink'),(13.8,'start'),(16.8,'height'),(20.8,'end')]:
 time.sleep(max(0,t-(time.monotonic()-t0)))
 if name=='tap':run(*A,'shell','input','tap','200','380')
 else:(D/f'android-{name}.png').write_bytes(run(*A,'exec-out','screencap','-p'))
video.wait(timeout=10);run(*A,'pull','/sdcard/zerolist-android-focus-far.mp4',str(D/'android-far.mp4'))
(D/'android-far.log').write_bytes(run(*A,'logcat','-d','-v','brief','ReactNativeJS:I','AndroidRuntime:E','*:S'));run(*A,'shell','am','force-stop','zerolist.example')
print('Android 상태·큰 인덱스·터치 계약 수집 완료')
