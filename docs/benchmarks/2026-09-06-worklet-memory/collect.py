"""정식 비교와 보조 관측을 수집하고 예비 실행은 따로 보존한다."""
from pathlib import Path
import json,zipfile,shutil,re,sys
D=Path(__file__).resolve().parent
matrix=[];groups=[]
for arg in sys.argv[1:]:
 p=Path(arg)
 if p.name=='startup':
  rs=json.loads((p/'results.json').read_text());assert len(rs)==12
  shutil.copy(p/'results.json',D/'startup-results.json');continue
 c=json.loads((p/'conditions.json').read_text());rs=json.loads((p/'results.json').read_text());assert len(rs)==len(c['configs'])*c['repeats']
 groups.append({'name':p.name,'conditions':c,'runs':len(rs)})
 for r in rs:
  initial=(p/f'{r["run"]}-{r["name"]}-startup.log').read_text()
  timings={}
  for phase,ms in re.findall(r'\[ZlData\] phase=(encode|decode).*? ms=([\d.]+)',initial):timings.setdefault(phase,[]).append(float(ms))
  if r['engine']=='template-compact':assert len(timings.get('encode',[]))==len(timings.get('decode',[]))==1,(p,r['name'],timings)
  matrix.append(dict(r,platform=c['platform'],group=p.name,cell=c['cell'],count=c['count'],data_timing_ms=timings,controlled_cost_comparison=False))
 for suffix in ['conditions','results']:shutil.copy(p/f'{suffix}.json',D/f'{p.name}-{suffix}.json')
 with zipfile.ZipFile(D/f'{p.name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(p.iterdir()):
   if f.is_file():z.write(f,f.name)
assert len(matrix)==58 and len(groups)==8
assert (D/'startup-results.json').exists()
(D/'matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2));(D/'groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2))
# shared value에 큰 JSON 문자열을 남긴 초기 방식: 최종 비교와 분리.
p=Path('/private/tmp/zerolist-memory-smoke-ios')
with zipfile.ZipFile(D/'retained-json-exploration.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in p.iterdir():
  if f.is_file():z.write(f,f.name)
print('정식',len(matrix),'회 + 시작 관측 12회')
