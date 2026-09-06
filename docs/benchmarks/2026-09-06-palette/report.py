"""8종의 새 실행만 수집한다. 시작과 스크롤·공백 지표를 혼합하지 않는다."""
from pathlib import Path
import json,statistics,re,zipfile,sys,itertools
D=Path(__file__).resolve().parent;root=Path(sys.argv[1])
ENGINES=['flatlist','flatlist-palette','zerolist','flashlist','legend','zigpool','template-compact','template-palette']
LABELS=['FlatList','FlatList 장식 통합','ZeroList','FlashList','LegendList','기존 ZigPool','메모리 개선 워클릿','장식 통합 워클릿']
labels=dict(zip(ENGINES,LABELS))
startup=json.loads((root/'startup/results.json').read_text());assert len(startup)==64
for r in startup:
 p=root/'startup'/f"{r['platform']}-{r['run']}-{r['engine']}.log"
 fs=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',line)} for line in p.read_text().splitlines() if 'ZlCommon' in line and 'frame=' in line]
 good=next(f for f in fs if f['wrong']==0 and f['blank']<=2 and f['overlap']<=2 and f['visible']>0)
 r['first_valid_attached']=good['attached'];r['first_valid_visible']=good['visible']
matrix=[];groups=[]
for platform in ['ios','android']:
 for group in ['audit160','perf0','perf160']:
  p=root/f'{platform}-{group}';c=json.loads((p/'conditions.json').read_text());rs=json.loads((p/'results.json').read_text());assert len(rs)==24
  groups.append(dict(name=p.name,conditions=c))
  matrix += [dict(r,platform=platform,group=group) for r in rs]
summary=[]
def stats(v):return {'mean':statistics.mean(v),'median':statistics.median(v),'min':min(v),'max':max(v)}
for platform in ['ios','android']:
 for engine in ENGINES:
  starts=[r for r in startup if r['platform']==platform and r['engine']==engine and not r['warmup']];assert len(starts)==3
  row=dict(platform=platform,engine=engine,label=labels[engine],startup_ms=stats([r['milliseconds']['content_ready'] for r in starts]),initial_attached=stats([r['first_valid_attached'] for r in starts]),initial_visible=stats([r['first_valid_visible'] for r in starts]))
  if engine.startswith('template-'):row['ui_data_ready_ms']=stats([r['milliseconds']['data_ready'] for r in starts])
  for group in ['perf0','perf160']:
   rs=[r for r in matrix if r['platform']==platform and r['engine']==engine and r['group']==group];assert len(rs)==3
   late='late_percent' if platform=='android' else 'late_callback_percent';p95='p95_ms' if platform=='android' else 'callback_p95_ms'
   row[group]={key:stats([r[source] for r in rs]) for key,source in [('memory','memory_after_mib'),('cpu','cpu_one_core_percent'),('late',late),('p95',p95)]}
  a=[r for r in matrix if r['platform']==platform and r['engine']==engine and r['group']=='audit160'];assert len(a)==3
  row['audit']={'blank':stats([r['mean_blank_area_percent'] for r in a]),'max_blank_percent':max(r['max_blank_area_percent'] for r in a),'zero_blank_runs':sum(r['blank_episode_count']==0 for r in a),'wrong_frames':sum(r['wrong_frames'] for r in a),'overlap_frames':sum(r['overlap_frames'] for r in a),'frames':sum(r['frames'] for r in a),'attached_max':max(r['attached_max'] for r in a),'entry_ready_percent':stats([r['entry_ready_percent'] for r in a])}
  row['audit']['travel_rows']=stats([r['travel_rows'] for r in a])
  summary.append(row)
for name,value in [('summary',summary),('startup-results',startup),('matrix',matrix),('groups',groups)]:
 (D/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2))
for p in root.iterdir():
 if p.is_dir():
  with zipfile.ZipFile(D/f'{p.name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
   for f in p.iterdir():
    if f.is_file():z.write(f,f.name)
lines=['# 8종 리스트 전체 비교','',
'**FlatList·장식 통합 FlatList·ZeroList·FlashList·LegendList·기존 ZigPool·메모리 개선 워클릿·장식 통합 워클릿을 모두 같은 바이너리에서 새로 측정했다.** 정식 192회와 별도 시작 준비 16회이며 과거 수치를 섞지 않았다. [조건·API 차이·측정 경계](methodology-ko.md)','',
'RN 0.87.1 / FlashList 2.3.1 / LegendList 2.0.19. 10만 건 고정 높이 무거운 셀, 한쪽 5행 준비 목표. 실제 뷰 수와 지원 기능은 엔진마다 다르다. 에뮬레이터·시뮬레이터에서 외부 호스트 부하를 통제하지 못한 탐색 비교다.','']
observations=[]
lines += ['**지연 안정성은 해결하지 못했다.** Android JS 점유 지연은 직전 워클릿 0.85% → 후보 1.57%였다. 별도 추가 6회에서는 후보 한 실행이 21.23%까지 높아졌다. 정식 평균과 섞지 않았으며 [추가 검사](followup-ko.md)와 [개선 폭·대조군 해석](findings-ko.md)에 원자료와 한계를 남겼다.','']
for r in matrix:
 if r['platform']=='android' and r['group']=='perf160' and r['late_percent']>=5:
  hs=json.loads((root/'android-perf160'/f"{r['run']}-{r['name']}-host.json").read_text())
  observations.append({'engine':r['engine'],'run':r['run'],'late_percent':r['late_percent'],'p95_ms':r['p95_ms'],'host_load':[h['load'][0] for h in hs],'external_build_processes':[sum(p['name'] in ['zig','build','test'] for p in h['processes']) for h in hs]})
(D/'high-latency-observations.json').write_text(json.dumps(observations,indent=2))
if observations:
 peak=max(observations,key=lambda r:r['late_percent'])
 lines += [f"**Android 지연 순위는 확정하지 않는다.** {labels[peak['engine']]} 한 실행에서 지연 {peak['late_percent']:.2f}%·p95 {peak['p95_ms']}ms와 함께 호스트 1분 부하 약 {peak['host_load'][0]:.1f}→{peak['host_load'][1]:.1f}가 기록됐다. 인과관계를 단정하거나 느린 실행을 제외하지 않았으며 [큰 지연과 외부 빌드 관측 기록](high-latency-observations.json)에 따로 보존했다.", '']
for platform in ['ios','android']:
 rs=[r for r in summary if r['platform']==platform];title='iOS' if platform=='ios' else 'Android'
 lines += [f'## {title} 시작과 평상시 비용','',
 '시작은 네이티브 진입부터 첫 제목·배치 확인까지의 3회 중앙값, 비용은 3회 평균이다. 괄호는 실행별 범위다. 실제 패널 표시 시각이나 앱 전체 시작 시간은 아니다.','',
 '| 엔진 | 시작 ms (범위) | 첫 확인 시 붙은 행 수 중앙값 | 메모리 MiB | CPU % | 지연 % | p95 ms |','|---|---:|---:|---:|---:|---:|---:|']
 for r in rs:
  s=r['startup_ms'];p=r['perf0'];lines.append(f"| {r['label']} | {s['median']:.1f} ({s['min']:.1f}~{s['max']:.1f}) | {r['initial_attached']['median']:.0f} | {p['memory']['mean']:.1f} | {p['cpu']['mean']:.1f} | {p['late']['mean']:.2f} | {p['p95']['mean']:.2f} |")
 lines += ['',f'## {title} JS 160ms 점유 조건','',
 '공백 검사와 비용 검사는 별도 실행이다. 평균 공백은 움직이는 구간의 화면 공백 면적 비율이며 지연 프레임 비율과 다르다.','',
 '| 엔진 | 평균 공백 % (범위) | 무공백 / 3 | 내용 오류 / 겹침 프레임 | 붙은 행 최대 | 메모리 MiB | CPU % | 지연 % (범위) | p95 ms |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in rs:
  a=r['audit'];b=a['blank'];p=r['perf160'];l=p['late'];lines.append(f"| {r['label']} | {b['mean']:.3f} ({b['min']:.3f}~{b['max']:.3f}) | {a['zero_blank_runs']} | {a['wrong_frames']} / {a['overlap_frames']} | {a['attached_max']:.0f} | {p['memory']['mean']:.1f} | {p['cpu']['mean']:.1f} | {l['mean']:.2f} ({l['min']:.2f}~{l['max']:.2f}) | {p['p95']['mean']:.2f} |")
 lines += ['',f'![{title} 한글 비교]({platform}-summary-ko.png)','']
lines += ['## 지표별 정렬','',
'아래는 이 조건에서 낮은 수치 순으로 정렬한 결과다. 종합 제품 순위나 통계적으로 확정된 우위를 의미하지 않는다. 지원 범위와 실행별 편차를 함께 봐야 한다.','']
for platform in ['ios','android']:
 rs=[r for r in summary if r['platform']==platform]
 for label,key in [('첫 제목·배치 확인',lambda r:r['startup_ms']['median']),('평상시 메모리',lambda r:r['perf0']['memory']['mean']),('JS 점유 평균 공백',lambda r:r['audit']['blank']['mean'])]:
  ordered=sorted(rs,key=key)
  ranked=[' = '.join(r['label'] for r in group)+f' ({value:.2f})' for value,group in itertools.groupby(ordered,key=lambda r:round(key(r),2))]
  lines.append(f"- {platform} {label}: "+' → '.join(ranked))
lines += ['','## 워클릿 보조 지표','',
'UI 전체 데이터 접근 시점은 워클릿에만 있는 별도 지표다. 일반 리스트의 값은 해당 없음이며 0으로 간주하지 않는다. 이 시간으로 전체 리스트 시작 순위를 매기지 않았다.','',
'| 플랫폼 | 워클릿 | UI 데이터 접근 가능 중앙값 ms |','|---|---|---:|']
for r in summary:
 if 'ui_data_ready_ms' in r:lines.append(f"| {r['platform']} | {r['label']} | {r['ui_data_ready_ms']['median']:.1f} |")
lines+=['','## 정확성과 검증 한계','',
f"스크롤 화면 검사 48회·{sum(r['audit']['frames'] for r in summary):,}프레임에서 내용 오류 {sum(r['audit']['wrong_frames'] for r in summary)}프레임, 겹침 {sum(r['audit']['overlap_frames'] for r in summary)}프레임을 관측했다.",
f"시작 검사(준비 포함) 64회에서 내용 오류 {sum(r['wrong_frames'] for r in startup)}프레임, 겹침 {sum(r['overlap_frames'] for r in startup)}프레임이었다.",'',
'FlatList·ZeroList·FlashList·LegendList는 공통 React 셀을 사용한다. 장식 통합 FlatList는 그 셀의 장식만 네이티브 뷰로 바꾼 대조군이다. 워클릿은 고정 템플릿과 전용 텍스트를 사용해 React 재렌더와 데이터 전달 경로가 다르다. 고정 높이 힌트가 주어진 이번 결과를 동적 높이·이미지 다운로드·데이터 변경·실물 구형 기기의 종합 성능으로 일반화하지 않는다.','',
'이번 변경은 장식용 64개 뷰와 워클릿을 한 뷰로 합쳤다. GPU API 변경이나 범용 리스트 알고리즘의 개선으로 해석하지 않는다. 외부 호스트 부하와 3회 편차가 있어 Android 지연 회귀가 일반적으로 해결됐다고 단정하지 않는다.','',
'장식 통합 소스 `864b6e6`으로 Android/iOS Release를 새로 빌드했다. 76개 테스트, 라이브러리 타입 검사, 린트, 웹 빌드를 통과했다. 초기 64칸 비교와 스크롤 후 384칸의 기대 색 검사도 통과했다. 자세한 검사 범위는 조건 문서에 명시했다.','']
lines += ['## 변경 해석과 실제 화면','',
'[개선 폭·대조군·남은 과제](findings-ko.md). 한글 비교 영상은 [드래프트 PR 본문](https://github.com/ohah/zerolist/pull/1)에 포함했다. 아래는 정량 측정과 분리한 실제 초기 화면이다. 원본 16장은 `screens/`에 보존했다.','',
'![iOS 장식 통합 실제 화면](ios-screens-ko.png)','',
'![Android 장식 통합 실제 화면](android-screens-ko.png)','']
(D/'README.md').write_text('\n'.join(lines));print('192회 + 시작 준비16회 수집 완료')
