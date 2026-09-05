"""완료한 그룹만 수집한다. 화면 정확성과 비용의 판정을 분리한다."""
from pathlib import Path
import sys,json,shutil,zipfile,re,math,statistics
D=Path(__file__).resolve().parent
matrix=[];groups=[];traces=[]
def percentile(xs):return sorted(xs)[max(0,math.ceil(.95*len(xs))-1)] if xs else None
for arg in sys.argv[1:]:
 p=Path(arg);c=json.loads((p/'conditions.json').read_text());rs=json.loads((p/'results.json').read_text())
 assert len(rs)==len(c['configs'])*c['repeats'],p
 groups.append({'name':p.name,'conditions':c,'runs':len(rs)})
 for r in rs:
  row=dict(r,platform=c['platform'],group=p.name,cell=c['cell'],count=c['count'],controlled_cost_comparison=False)
  matrix.append(row)
  if c['diagnostic']=='trace-binding':
   raw=(p/f'{r["run"]}-{r["name"]}-measured.log').read_text()
   phases={}
   for phase,v,t in re.findall(r'ZlBinding[^\n]*?phase=(\w+) version=(-?\d+) wall=(\d+)',raw):
    phases.setdefault(phase,{}).setdefault(int(v),int(t))
   receive='ui_receive' if r['engine']=='template-worklet' else 'js_receive' if r['engine']=='template-js' else 'receive'
   result={'platform':c['platform'],'engine':r['engine'],'group':p.name,'requested':len(phases.get('request',{})),'received':len(phases.get(receive,{})),'committed':len(phases.get('native_commit',{})),'placed':len(phases.get('placed',{}))}
   for label,a,b in [('request_to_receive','request',receive),('receive_to_commit',receive,'native_commit'),('commit_to_placed','native_commit','placed')]:
    values=[t-phases[a][v] for v,t in phases.get(b,{}).items() if v in phases.get(a,{})]
    result[label]={'n':len(values),'p95_ms':percentile(values),'median_ms':statistics.median(values) if values else None,'min_ms':min(values,default=None),'negative_samples':sum(v<0 for v in values)}
   traces.append(result)
 for suffix in ['conditions','results']:shutil.copy(p/f'{suffix}.json',D/f'{p.name}-{suffix}.json')
 with zipfile.ZipFile(D/f'{p.name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(p.iterdir()):
   if f.is_file():z.write(f,f.name)
for name,value in [('matrix',matrix),('groups',groups),('traces',traces)]:
 (D/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2))
print('수집',len(matrix),'회 /',len(groups),'그룹')
