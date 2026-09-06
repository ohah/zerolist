"""실제 화면의 행 제목과 배치 위치를 비교한다. 성능 통계와 별도로 실행한다."""
import os,subprocess,time,pathlib,json,re
P=pathlib.Path(os.environ.get('OUT','/tmp/zerolist-sync-audit'));P.mkdir(exist_ok=True,parents=True)
A=[os.environ.get('ADB','/Users/yoonhb/Library/Android/sdk/platform-tools/adb'),'-s','emulator-5554']
def adb(*args):return subprocess.check_output(A+list(args),timeout=40)
results=[]
for delay in [0,120,400]:
 for legacy in [True,False]:
  name=('legacy' if legacy else 'fixed')+'-'+str(delay)
  adb('shell','am','force-stop','zerolist.example')
  adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine','zigpool','--ei','count','100000','--es','cell','heavy','--ez','audit','true','--ez','legacyRecycling',str(legacy).lower(),'--ei','bindingDelayMs',str(delay))
  time.sleep(3)
  pid=adb('shell','pidof','zerolist.example').decode().strip()
  adb('logcat','-c')
  for y1,y2,d in [(1800,600,300)]*3+[(1900,400,120)]*6+[(400,1900,120)]*6+[(1800,600,300)]*3:
   adb('shell','input','swipe','540',str(y1),'540',str(y2),str(d))
  time.sleep(2)
  log=adb('logcat','-d','--pid='+pid,'-v','brief','ZlAudit:I','ReactNativeJS:I','*:S').decode(errors='replace')
  (P/(name+'.log')).write_text(log)
  (P/(name+'.png')).write_bytes(adb('exec-out','screencap','-p'))
  frames=[{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)} for line in log.splitlines() if 'ZlAudit' in line and 'frame=' in line]
  if not frames:raise RuntimeError('No native audit frames: '+name)
  result={'case':name,'frames':len(frames),'wrong_frames':sum(f['wrong']>0 for f in frames),'max_wrong':max(f['wrong'] for f in frames),'blank_frames':sum(f['blank']>2 for f in frames),'overlap_frames':sum(f['overlap']>2 for f in frames),'last':frames[-1]}
  results.append(result);(P/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(result),flush=True)

# 이전 경로에서 문제를 재현해야 검사기가 실제 불일치를 잡는다는 근거가 된다.
assert any(r['wrong_frames'] > 0 for r in results if r['case'].startswith('legacy-'))
for r in results:
 if r['case'].startswith('fixed-'):
  assert r['wrong_frames'] == 0 and r['overlap_frames'] == 0, r
  assert r['last']['wrong'] == 0 and r['last']['blank'] <= 2, r
  if r['case'] == 'fixed-0': assert r['blank_frames'] == 0, r
print('정확성 검사 통과: 기본 조건 빈 공간 없음, 지연 주입에서도 잘못된 행 없음')
