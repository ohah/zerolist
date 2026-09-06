"""기존 동일 바이너리 결과만 재집계한다. 새 실행이나 다른 날짜 점수 혼합 없음."""
from pathlib import Path
import json,statistics,hashlib
D=Path(__file__).resolve().parent;P=D.parent/'2026-09-06-palette'
summary=json.loads((P/'summary.json').read_text());matrix=json.loads((P/'matrix.json').read_text())
out={'measurement_source':'864b6e6','new_device_runs':0,'source_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'summary.json',P/'matrix.json']},'comparisons':[]}
for platform in ['android','ios']:
 for engine in ['flatlist','flatlist-palette','template-palette']:
  r=next(r for r in summary if r['platform']==platform and r['engine']==engine)
  a=[r for r in matrix if r['platform']==platform and r['engine']==engine and r['mode']=='audit'];assert len(a)==3
  out['comparisons'].append(dict(platform=platform,engine=engine,repeats=3,startup_median_ms=r['startup_ms']['median'],memory_mib=r['perf0']['memory']['mean'],cpu_percent=r['perf0']['cpu']['mean'],stress_late_percent=r['perf160']['late']['mean'],stress_blank_percent=r['audit']['blank']['mean'],audit_travel_rows=statistics.mean(x['travel_rows'] for x in a),attached_max=statistics.mean(x['attached_max'] for x in a)))
(D/'evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('동일 바이너리 대조군 6개 재집계, 새 기기 실행 0회')
