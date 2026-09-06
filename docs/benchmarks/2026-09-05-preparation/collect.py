"""완료된 측정만 수집한다. 초기 파일럿/검증기 중단 실행은 합산하지 않는다."""
from pathlib import Path
import json,zipfile,shutil,statistics
D=Path(__file__).resolve().parent
S=Path('/private/tmp')
groups={
 'android-audit-a':('zerolist-prepare-android-final-audit',21),
 'android-audit-b':('zerolist-prepare-android-stable-audit',9),
 'ios-audit':('zerolist-prepare-ios-final-audit',27),
 'android-perf':('zerolist-prepare-android-perf',27),
 'ios-perf':('zerolist-prepare-ios-perf',27),
 'android-block':('zerolist-prepare-android-block',4),
 'ios-block':('zerolist-prepare-ios-block',4),
}
data={}
for name,(folder,expected) in groups.items():
 source=S/folder
 rows=json.loads((source/'results.json').read_text())
 if len(rows)!=expected:raise RuntimeError(f'{name}: {len(rows)}/{expected}')
 for r in rows:
  if 'wrong_frames' in r:assert r['wrong_frames']==0 and r['overlap_frames']==0, (name,r)
 shutil.copyfile(source/'results.json',D/(name+'-results.json'))
 shutil.copyfile(source/'conditions.json',D/(name+'-conditions.json'))
 with zipfile.ZipFile(D/(name+'-raw.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(source.iterdir()):
   if f.is_file():z.write(f,f.name)
 data[name]=rows
android={}
for name in ['android-audit-a','android-audit-b']:
 for r in data[name]:android[(r['variant'],r['delay_ms'])]=dict(r,source=name)
matrix={'android':{'audit':list(android.values()),'perf':data['android-perf'],'block':data['android-block']},'ios':{'audit':data['ios-audit'],'perf':data['ios-perf'],'block':data['ios-block']}}
(D/'matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2))
summary={}
for platform,values in matrix.items():
 summary[platform]={}
 for r in values['audit']:
  v=summary[platform].setdefault(r['variant'],{})
  v[str(r['delay_ms'])]={'ready_percent':r['entry_ready_percent'],'ready_p50_ms':r['ready_p50_ms'],'ready_p95_ms':r['ready_p95_ms'],'requests':r['requests'],'renders':r['renders_during'],'blank_moving_frames':r['blank_moving_frames']}
 for variant,v in summary[platform].items():
  rows=[r for r in values['perf'] if r['variant']==variant]
  keys=['memory_before_mib','memory_after_mib']+(['late_percent','p95_ms','renders_during'] if platform=='android' else ['late_callback_percent','callback_p95_ms'])
  v['perf']={k:{'median':statistics.median(r[k] for r in rows),'min':min(r[k] for r in rows),'max':max(r[k] for r in rows)} for k in keys}
 for r in values['block']:
  summary[platform][r['variant']]['block']={'ready_percent':r['entry_ready_percent'],'ready_p50_ms':r['ready_p50_ms'],'ready_p95_ms':r['ready_p95_ms'],'block_samples':r['block_samples'],'block_median_ms':r['block_median_ms']}
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('수집 완료:',sum(len(r) for r in data.values()),'실행, 기본 대조군 중복 3회는 행렬에서 대체')
