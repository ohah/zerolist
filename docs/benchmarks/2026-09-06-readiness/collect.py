"""수집 디렉터리 목록을 받아 원자료를 보존하고 결과를 합친다."""
from pathlib import Path
import json,sys,zipfile,shutil,statistics
D=Path(__file__).resolve().parent
matrix=[];groups=[]
for arg in sys.argv[1:]:
 p=Path(arg);c=json.loads((p/'conditions.json').read_text());rs=json.loads((p/'results.json').read_text())
 expected=len(c['configs'])*c['repeats'];assert len(rs)==expected,(p,len(rs),expected)
 name=p.name.removeprefix('zerolist-budget-');groups.append(dict(name=name,conditions=c,runs=len(rs)))
 for r in rs:matrix.append(dict(r,platform=c['platform'],group=name))
 for suffix in ['conditions','results']:shutil.copy(p/f'{suffix}.json',D/f'{name}-{suffix}.json')
 with zipfile.ZipFile(D/f'{name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(p.iterdir()):
   if f.is_file():z.write(f,f.name)
(D/'matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2))
(D/'groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2))
print('valid runs',len(matrix),'groups',len(groups))
