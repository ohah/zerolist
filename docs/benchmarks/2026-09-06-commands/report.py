"""같은 새 바이너리의 3개 갱신 경로만 집계한다. 느린 실행도 보존한다."""
from pathlib import Path
import json,statistics,re,zipfile,sys
D=Path(__file__).resolve().parent;root=Path(sys.argv[1])
engines=['template-palette','template-palette-command','template-command']
labels=dict(zip(engines,['기존 장식 통합','장식만 명령','글자·장식 명령']))
starts=json.loads((root/'startup/results.json').read_text());assert len(starts)==36
matrix=[];conditions=[]
for platform in ['android','ios']:
 for group,n in [('audit160',9),('perf0',15),('perf160',30)]:
  p=root/f'{platform}-{group}';rs=json.loads((p/'results.json').read_text());assert len(rs)==n
  conditions.append(dict(platform=platform,group=group,conditions=json.loads((p/'conditions.json').read_text())))
  for r in rs:
   hs=json.loads((p/f"{r['run']}-{r['name']}-host.json").read_text())
   r.update(platform=platform,group=group,host_load=[h['load'][0] for h in hs],external_build_processes=[sum(x['name'] in ['zig','build','test'] for x in h['processes']) for h in hs])
   matrix.append(r)
def stats(v):return dict(n=len(v),mean=statistics.mean(v),median=statistics.median(v),min=min(v),max=max(v))
summary=[]
for platform in ['ios','android']:
 for e in engines:
  ss=[s for s in starts if s['platform']==platform and s['engine']==e and not s['warmup']];assert len(ss)==5
  row=dict(platform=platform,engine=e,label=labels[e],startup_ms=stats([s['milliseconds']['content_ready'] for s in ss]),data_ready_ms=stats([s['milliseconds']['data_ready'] for s in ss]))
  for group,n in [('perf0',5),('perf160',10)]:
   rs=[r for r in matrix if r['platform']==platform and r['engine']==e and r['group']==group];assert len(rs)==n
   keys={'memory':'memory_after_mib','cpu':'cpu_one_core_percent','late':'late_percent' if platform=='android' else 'late_callback_percent','p95':'p95_ms' if platform=='android' else 'callback_p95_ms'}
   row[group]={key:stats([r[src] for r in rs]) for key,src in keys.items()}
   row[group]['late_runs']=[dict(run=r['run'],value=r[keys['late']],p95_ms=r[keys['p95']],host_load=r['host_load'],external_build_processes=r['external_build_processes']) for r in rs]
  a=[r for r in matrix if r['platform']==platform and r['engine']==e and r['group']=='audit160'];assert len(a)==3
  row['audit']=dict(blank=stats([r['mean_blank_area_percent'] for r in a]),zero_blank_runs=sum(r['blank_episode_count']==0 for r in a),wrong_frames=sum(r['wrong_frames'] for r in a),overlap_frames=sum(r['overlap_frames'] for r in a),frames=sum(r['frames'] for r in a),travel_rows=stats([r['travel_rows'] for r in a]))
  summary.append(row)
for name,v in [('summary',summary),('matrix',matrix),('startup-results',starts),('conditions',conditions)]:
 (D/f'{name}.json').write_text(json.dumps(v,ensure_ascii=False,indent=2))
outliers=[dict(platform=r['platform'],engine=r['engine'],group=r['group'],run=r['run'],late_percent=r.get('late_percent',r.get('late_callback_percent')),host_load=r['host_load'],external_build_processes=r['external_build_processes']) for r in matrix if r['mode']=='perf' and r.get('late_percent',r.get('late_callback_percent',0))>=5]
(D/'high-latency-observations.json').write_text(json.dumps(outliers,indent=2))
for p in root.iterdir():
 if p.is_dir():
  with zipfile.ZipFile(D/f'{p.name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
   for f in p.iterdir():
    if f.is_file():z.write(f,f.name)
lines=['# 네이티브 명령 경로 138회 비교','',
'**기존 장식 통합·장식만 명령·글자와 장식 명령의 세 경로를 같은 새 바이너리에서 비교했다.** 전체 라이브러리 순위 비교가 아니며 앞선 8종 자료의 수치를 섞지 않았다. [조건과 검증 범위](methodology-ko.md) · [판단과 남은 과제](findings-ko.md)','',
'RN 0.87.1 arm64 Release, 10만 건 고정 높이 무거운 셀, 14개 슬롯. 시작·평상시 각 5회, JS 점유 비용 각 10회, 화면 검사 각 3회로 정식 138회다. 별도 시작 준비 6회도 원본에 보존했다.','']
for platform in ['ios','android']:
 rs=[r for r in summary if r['platform']==platform];title='iOS' if platform=='ios' else 'Android'
 lines += [f'## {title} 시작과 평상시 비용','',
 '첫 제목·배치 확인은 중앙값, 비용은 평균이다. 괄호는 실행별 범위다. 시작은 실제 패널 표시나 앱 전체 실행 시간이 아니다.','',
 '| 경로 | 시작 ms (범위) | UI 데이터 준비 ms | 메모리 MiB (범위) | CPU % (범위) | 지연 % |','|---|---:|---:|---:|---:|---:|']
 for r in rs:
  s=r['startup_ms'];p=r['perf0'];m=p['memory'];c=p['cpu']
  lines.append(f"| {r['label']} | {s['median']:.1f} ({s['min']:.1f}~{s['max']:.1f}) | {r['data_ready_ms']['median']:.1f} | {m['mean']:.1f} ({m['min']:.1f}~{m['max']:.1f}) | {c['mean']:.1f} ({c['min']:.1f}~{c['max']:.1f}) | {p['late']['mean']:.2f} |")
 lines += ['',f'## {title} JS 160ms 점유·40ms 여유','',
 '| 경로 | 지연 평균 % (범위) | p95 평균 ms | 메모리 MiB | CPU % | 공백 평균 % | 무공백 / 3 | 오류 / 겹침 프레임 |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for r in rs:
  p=r['perf160'];l=p['late'];a=r['audit']
  lines.append(f"| {r['label']} | {l['mean']:.2f} ({l['min']:.2f}~{l['max']:.2f}) | {p['p95']['mean']:.2f} | {p['memory']['mean']:.1f} | {p['cpu']['mean']:.1f} | {a['blank']['mean']:.3f} | {a['zero_blank_runs']} | {a['wrong_frames']} / {a['overlap_frames']} |")
 lines+=['','지연과 공백은 별도 실행·서로 다른 지표다. CPU는 앱 전체 평균 사용률이며 처리 속도 향상률이 아니다.','',f'![{title} 명령 경로 한글 비교]({platform}-summary-ko.png)','',
 '### JS 점유 지연의 실행별 수치','',
 '| 경로 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in rs:lines.append('| '+r['label']+' | '+' | '.join(f"{x['value']:.2f}" for x in r['perf160']['late_runs'])+' |')
 lines+=['']
lines+=['## 정확성과 한계','',
 f"화면 검사 18회·{sum(r['audit']['frames'] for r in summary):,}프레임에서 제목 오류 {sum(r['audit']['wrong_frames'] for r in summary)}프레임, 겹침 {sum(r['audit']['overlap_frames'] for r in summary)}프레임을 관측했다.",
 '초기 화면의 글자·색 비교와 14개 슬롯 밖 실제 화면의 제목·본문 접두부·합계·색 검사도 별도로 수행했다. 모든 프레임의 모든 내용과 장시간 동작을 검증한 것은 아니다.','',
 '외부 호스트 부하를 통제하지 못했다. 느린 실행을 제외하지 않았으며 큰 지연은 [관측 기록](high-latency-observations.json)에 따로 모았다. 같은 시점의 외부 빌드를 유일한 원인으로 단정하지 않는다. 실제 기기·동적 높이·임의 React 셀·데이터 변경은 미검증이다.','',
 '소스 `ba8b86f`의 Android/iOS Release, 76개 테스트, 라이브러리 타입 검사, 린트와 웹 빌드를 검증했다. 예제 전체 타입 검사에는 조건 문서에 적은 기존 오류가 남는다.','',
 '한글 비교 영상은 [드래프트 PR 본문](https://github.com/ohah/zerolist/pull/1)에 포함했다.','']
(D/'README.md').write_text('\n'.join(lines));print('138회 집계 완료')
