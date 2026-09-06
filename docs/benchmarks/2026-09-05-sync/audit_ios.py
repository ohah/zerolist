"""iOS 실제 텍스트/위치 검사. Android와 프레임 개수·비율을 직접 비교하지 않는다."""
import os,subprocess,time,pathlib,json,re
P=pathlib.Path(os.environ.get('OUT','/tmp/zerolist-sync-ios-audit'));P.mkdir(exist_ok=True,parents=True)
UDID=os.environ.get('UDID','ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D')
def run(*args):return subprocess.run(list(args),capture_output=True,check=True,timeout=45)
results=[]
for delay in [0,120,400]:
 for legacy in [True,False]:
  name=('legacy' if legacy else 'fixed')+'-'+str(delay)
  env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_ENGINE='zigpool',SIMCTL_CHILD_ZL_AUDIT='1',SIMCTL_CHILD_ZL_LEGACY='1' if legacy else '0',SIMCTL_CHILD_ZL_DELAY=str(delay))
  logPath=P/(name+'.log')
  with logPath.open('w') as log:
   proc=subprocess.Popen(['xcrun','simctl','launch','--terminate-running-process','--console',UDID,'zerolist.example'],env=env,stdout=log,stderr=subprocess.STDOUT)
   try:
    time.sleep(3);start=logPath.stat().st_size
    for y1,y2,d in [(750,220,.3)]*3+[(780,150,.12)]*6+[(150,780,.12)]*6+[(750,220,.3)]*3:
     run('idb','ui','swipe','200',str(y1),'200',str(y2),'--duration',str(d),'--udid',UDID)
    time.sleep(2)
    run('xcrun','simctl','io',UDID,'screenshot',str(P/(name+'.png')))
   finally:
    run('xcrun','simctl','terminate',UDID,'zerolist.example');proc.wait(timeout=15)
  text=logPath.read_bytes()[start:].decode(errors='replace')
  frames=[{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)} for line in text.splitlines() if 'ZlAudit' in line and 'frame=' in line]
  if not frames:raise RuntimeError('No audit frames: '+name)
  r={'case':name,'frames':len(frames),'wrong_frames':sum(f['wrong']>0 for f in frames),'max_wrong':max(f['wrong'] for f in frames),'blank_frames':sum(f['blank']>2 for f in frames),'overlap_frames':sum(f['overlap']>2 for f in frames),'last':frames[-1]}
  results.append(r);(P/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(r),flush=True)

# 이전 경로에서 문제를 재현해야 검사기가 실제 불일치를 잡는다는 근거가 된다.
assert any(r['wrong_frames'] > 0 for r in results if r['case'].startswith('legacy-'))
for r in results:
 if r['case'].startswith('fixed-'):
  assert r['wrong_frames'] == 0 and r['overlap_frames'] == 0, r
  assert r['last']['wrong'] == 0 and r['last']['blank'] <= 2, r
  if r['case'] == 'fixed-0': assert r['blank_frames'] == 0, r
print('정확성 검사 통과: 기본 조건 빈 공간 없음, 지연 주입에서도 잘못된 행 없음')
