"""공통 벽시계 단계 추적. 진단 실행만 사용하며 로그 누락 버전은 별도 집계한다."""
from pathlib import Path
import json,re,math,sys,statistics
D=Path(sys.argv[1]);out={}
for path in sorted(D.glob('*-measured.log')):
 versions={}
 for line in path.read_text().splitlines():
  m=re.search(r'ZlBinding\]? phase=(\w+) version=(-?\d+) wall=([\d.]+)',line)
  if m and int(m[2])>=0:versions.setdefault(int(m[2]),{})[m[1]]=float(m[3])
 backlog=[]
 pending={}
 for version,v in sorted(versions.items()):
  if 'request' in v:pending[version]=v['request']
  if 'placed' in v and version in pending:
   backlog.append({'latest_ms':v['placed']-pending[version],'oldest_ms':v['placed']-min(pending.values()),'requests':len(pending)})
   pending={}
 report={'backlog_samples':backlog,'phases':{p:sum(p in v for v in versions.values()) for p in ['request','receive','render','react_layout','native_commit','placed']},'durations':{}}
 for a,b in [('request','receive'),('receive','render'),('render','native_commit'),('native_commit','placed'),('request','placed')]:
  values=[v[b]-v[a] for v in versions.values() if a in v and b in v]
  if values:report['durations'][a+'->'+b]={'n':len(values),'p50':statistics.median(values),'p95':sorted(values)[math.ceil(.95*len(values))-1],'max':max(values),'min':min(values)}
 out[path.stem]=report
print(json.dumps(out,ensure_ascii=False,indent=2))
