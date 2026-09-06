"""단계별 벽시계 지연과 Android 프레임 계측을 원시 로그에서 계산한다."""
from pathlib import Path
import json,re,statistics,os
P=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('RAW_ROOT','/private/tmp'))
def stats(v):
 assert v and min(v)>=0, '누락 또는 역전된 시간 구간'
 v=sorted(v);return {'n':len(v),'p50':statistics.median(v),'p95':v[int(.95*(len(v)-1))],'max':max(v)}
def binding(path):
 rows={};phases=['request','receive','render','react_layout','native_commit','placed']
 for line in path.read_text().splitlines():
  m=re.search(r'phase=(\w+) version=(-?\d+) wall=(\d+)',line)
  if m:rows.setdefault(int(m[2]),{})[m[1]]=int(m[3])
 complete=[r for r in rows.values() if all(k in r for k in phases)]
 if not complete:return None
 return {a+'->'+b:stats([r[b]-r[a] for r in complete]) for a,b in list(zip(phases,phases[1:]))+[('request','placed')]}
def frames(path):
 rows=[];touch=[]
 for line in path.read_text().splitlines():
  d={k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
  if 'frame intended=' in line:rows.append(d)
  if 'touch action=' in line:touch.append(d['nano'])
 if not touch:return None
 rows=[f for f in rows if touch[0]-16666667<=f['intended']<=touch[-1]+1200000000]
 late=[f for f in rows if f['total']>f['deadline']]
 keys=['total','gpu','unknown','input','layout','draw','sync','command','swap','deadline']
 return {'frames':len(rows),'late_frames':len(late),'median_ms':{k:statistics.median(f[k] for f in rows)/1e6 for k in keys},'late_median_ms':{k:statistics.median(f[k] for f in late)/1e6 for k in keys} if late else {},'short_deadline_frames':sum(f['deadline']<20000000 for f in rows)}
result={'binding':{},'frames':{}}
for folder in ['zerolist-cause','zerolist-probe-modes','zerolist-probe-categories','zerolist-gfx-confirm','zerolist-cause-vulkan','zerolist-renderer-confirm']:
 for path in (ROOT/folder).rglob('*.log'):
  key=str(path.relative_to(ROOT));b=binding(path);f=frames(path)
  if b:result['binding'][key]=b
  if f:result['frames'][key]=f
 for path in (ROOT/folder).rglob('*-log.txt'):
  key=str(path.relative_to(ROOT));f=frames(path)
  if f:result['frames'][key]=f
(P/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print('분석 로그',len(result['frames']),'개, 내용 반영 로그',len(result['binding']),'개')
