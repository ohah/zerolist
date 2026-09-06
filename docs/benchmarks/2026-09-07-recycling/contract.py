"""실제 ZeroList의 항목 상태·재정렬·삭제·동적 크기를 재활용 켬/끔으로 검사한다."""
from pathlib import Path
import os,subprocess,time,json,re
D=Path(os.environ['OUT']);D.mkdir(exist_ok=False)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s',os.environ['ANDROID_SERIAL']]
def adb(*a):return subprocess.check_output(A+list(a),stderr=subprocess.STDOUT,timeout=30)
def foreground():
 lines=[l for l in adb('shell','dumpsys','window','displays').decode().splitlines() if 'mCurrentFocus=' in l]
 assert any('zerolist.example/zerolist.example.SoloActivity' in l or 'zerolist.example/.SoloActivity' in l for l in lines),'테스트 앱이 전면에 없음'
result=[]
for enabled in [False,True]:
 name='on' if enabled else 'off';adb('shell','am','force-stop','zerolist.example')
 adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--ez','viewRecycling',str(enabled).lower(),'--es','diagnostic','unified-contract','--es','engine','zerolist')
 start=time.monotonic();pid=adb('shell','pidof','zerolist.example').decode().strip()
 for at,step in [(5.5,'reorder'),(9.5,'replace'),(11.5,'far'),(17.5,'restore'),(21.5,'dynamic')]:
  time.sleep(max(0,at-(time.monotonic()-start)));foreground()
  (D/f'{name}-{step}.png').write_bytes(adb('exec-out','screencap','-p'))
 raw=adb('logcat','-d','--pid='+pid,'-v','brief','ReactNativeJS:I','ZlRecycle:I','AndroidRuntime:E','*:S').decode();(D/f'{name}.log').write_text(raw)
 assert f'configured={str(enabled).lower()} effective={str(enabled).lower()}' in raw
 rows=[json.loads(l.split('[ZlContractRow] ',1)[1]) for l in raw.splitlines() if '[ZlContractRow] ' in l]
 checks={}
 for step,index in [('재정렬',1),('앞 삽입',2),('내용 교체',2)]:
  found=[r for r in rows if r['step']==step and r['id']==0]
  checks[step]=any(r['index']==index and r['value']==1 for r in found)
 checks['내용 변경']=any(r['step']=='내용 교체' and r['id']==0 and r['label']=='변경된 항목 0' for r in rows)
 for step in ['먼 항목 이동','복원','동적 크기 변경']:
  found=[r for r in rows if r['step']==step];checks[step]=bool(found) and all(r['value']==0 for r in found)
 assert all(checks.values()),checks
 result.append({'recycling':enabled,'checks':checks,'note':'measureInWindow 좌표는 실제 화면 위치 증거로 사용하지 않음. PNG 별도 육안 검사.'})
 adb('shell','am','force-stop','zerolist.example')
(D/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
