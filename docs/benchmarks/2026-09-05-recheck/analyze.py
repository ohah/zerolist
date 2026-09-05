"""집계와 조건부 비교. 원자료에 없는 설정을 보간하거나 순위를 추정하지 않는다."""
from pathlib import Path
import json,statistics,csv
D=Path(__file__).resolve().parent
matrix=json.loads((D/'matrix.json').read_text())
groups={}
for r in matrix:groups.setdefault((r['platform'],r['name'],r['mode'],r['block_ms']),[]).append(r)
metrics=['blank_episode_count','blank_episode_max_ms','blank_episode_total_ms','memory_after_mib','cpu_one_core_percent','cpu_seconds','wall_seconds','mean_blank_area_percent','blank_moving_percent','max_blank_area_percent','wrong_frames','overlap_frames','late_percent','p95_ms','late_callback_percent','callback_p95_ms','travel_rows']
summary=[]
for (platform,name,mode,block),rs in groups.items():
 row={'platform':platform,'name':name,'engine':rs[0]['engine'],'rows':rs[0]['rows'],'mode':mode,'block_ms':block,'n':len(rs)}
 for metric in metrics:
  values=[r[metric] for r in rs if r.get(metric) is not None]
  if values:row[metric]={'median':statistics.median(values),'min':min(values),'max':max(values)}
 if all(r.get('work') for r in rs):
  row['renders_per_100_rows']={'median':statistics.median(r['work']['renders']/r['travel_rows']*100 for r in rs),'min':min(r['work']['renders']/r['travel_rows']*100 for r in rs),'max':max(r['work']['renders']/r['travel_rows']*100 for r in rs)} if all(r.get('travel_rows') for r in rs) else None
 summary.append(row)
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
# CPU와 메모리는 감사 로그 없는 perf, 공백과 작업량은 별도 audit의 결과다.
points=[]
for p in summary:
 if p['mode']!='perf' or p['block_ms']!=160:continue
 a=next((r for r in summary if r['platform']==p['platform'] and r['name']==p['name'] and r['mode']=='audit' and r['block_ms']==160),None)
 if a is None:continue
 points.append({'blank_episode_max_ms':a['blank_episode_max_ms']['max'],'platform':p['platform'],'name':p['name'],'engine':p['engine'],'rows':p['rows'],'perf_n':p['n'],'audit_n':a['n'],'memory_mib':p['memory_after_mib']['median'],'cpu_percent':p['cpu_one_core_percent']['median'],'blank_area_percent':a['mean_blank_area_percent']['median'],'blank_frames_percent':a['blank_moving_percent']['median'],'worst_blank_area_percent':a['max_blank_area_percent']['max'],'wrong_frames':a['wrong_frames']['max'],'overlap_frames':a['overlap_frames']['max'],'frame_p95_ms':p.get('p95_ms',p.get('callback_p95_ms'))['median'],'late_percent':p.get('late_percent',p.get('late_callback_percent'))['median'],'renders_per_100_rows':a['renders_per_100_rows']['median']})
(D/'points.json').write_text(json.dumps(points,ensure_ascii=False,indent=2))
with (D/'comparison-ko.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['플랫폼','설정','JS 점유 ms','메모리 MiB','CPU 1코어 대비 %','평균 공백 면적 %','공백 있는 이동 프레임 %','최대 공백 면적 %','프레임 또는 콜백 p95 ms','지연 프레임 또는 늦은 콜백 %','100행 이동당 셀 렌더','성능 반복','공백 반복','최대 공백 관측 지속 ms'])
 for p in points:w.writerow([p['platform'],p['name'],160]+[p[k] for k in ['memory_mib','cpu_percent','blank_area_percent','blank_frames_percent','worst_blank_area_percent','frame_p95_ms','late_percent','renders_per_100_rows','perf_n','audit_n','blank_episode_max_ms']])
for os in ['android','ios']:
 print(os)
 for p in points:
  if p['platform']==os:print(p['name'],round(p['memory_mib'],1),round(p['blank_area_percent'],2),round(p['cpu_percent'],1),p['frame_p95_ms'])
