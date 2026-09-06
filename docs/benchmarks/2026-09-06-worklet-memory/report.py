"""동일 바이너리 비교 결과로 한글 보고서를 생성한다."""
from pathlib import Path
import json,statistics
D=Path(__file__).resolve().parent
m=json.loads((D/'matrix.json').read_text());startup=json.loads((D/'startup-results.json').read_text())
labels={'zigpool':'기존 ZigPool','template-worklet':'기존 UI 워클릿','template-compact':'메모리 개선 워클릿'}
rows=[]
for platform in ['ios','android']:
 for engine,label in labels.items():
  a=[r for r in m if r['group']==f'{platform}-audit160' and r['engine']==engine]
  n=[r for r in m if r['group']==f'{platform}-perf0' and r['engine']==engine]
  b=[r for r in m if r['group']==f'{platform}-perf160' and r['engine']==engine]
  start=[r for r in startup if r['platform']==platform and r['engine']==engine]
  assert len(a)==len(n)==len(b)==3 and len(start)==2
  avg=lambda rs,k:statistics.mean(r[k] for r in rs)
  late='late_callback_percent' if platform=='ios' else 'late_percent'
  row={'platform':platform,'engine':engine,'label':label,'memory_mib':avg(n,'memory_after_mib'),'stress_memory_mib':avg(b,'memory_after_mib'),'cpu_percent':avg(n,'cpu_one_core_percent'),'stress_cpu_percent':avg(b,'cpu_one_core_percent'),'late_percent':avg(n,late),'stress_late_percent':avg(b,late),'blank_mean_percent':avg(a,'mean_blank_area_percent'),'blank_max_percent':max(r['max_blank_area_percent'] for r in a),'zero_blank_runs':sum(r['blank_episode_count']==0 for r in a),'wrong_frames':sum(r['wrong_frames'] for r in a),'overlap_frames':sum(r['overlap_frames'] for r in a),'startup_observed_peak_mib':max(r['observed_peak_mib'] for r in start),'startup_peaks_mib':[r['observed_peak_mib'] for r in start]}
  if engine=='template-compact':
   row['encode_median_ms']=statistics.median(r['data_timing_ms']['encode'][0] for r in a+n+b)
   row['decode_median_ms']=statistics.median(r['data_timing_ms']['decode'][0] for r in a+n+b)
  rows.append(row)
(D/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
lines=['# UI 워클릿의 메모리 감소 검증','',f'RN 0.87.1에서 정식 비교·단순 셀 {len(m)}회와 시작 메모리 관측 {len(startup)}회를 실행했다. [구현과 측정 방법](methodology-ko.md)','',
'객체 배열 전체의 공유 변환을 필드별 배열의 일회성 전달로 바꿨다. UI에서 데이터를 복원하고 슬롯의 항목만 조립한다. 실제 값과 전체 10만 건 접근을 유지하며, 스크롤 중 JS 데이터 재요청을 추가하지 않았다.','',
'## 평상시 메모리와 CPU','',
'동일한 새 바이너리, 10만 건 무거운 셀, 14개 슬롯, 각 3회 평균이다. Android는 PSS, iOS는 RSS로 서로 직접 비교하지 않는다. 호스트 외부 부하를 통제하지 못한 탐색값이다.','',
'| 플랫폼 | 엔진 | 종료 메모리 MiB | CPU % | 지연 % |','|---|---|---:|---:|---:|']
for r in rows:lines.append(f"| {r['platform']} | {r['label']} | {r['memory_mib']:.1f} | {r['cpu_percent']:.1f} | {r['late_percent']:.2f} |")
lines+=['']
for platform in ['ios','android']:
 old=next(r for r in rows if r['platform']==platform and r['engine']=='template-worklet');new=next(r for r in rows if r['platform']==platform and r['engine']=='template-compact');base=next(r for r in rows if r['platform']==platform and r['engine']=='zigpool')
 saved=old['memory_mib']-new['memory_mib'];extra=old['memory_mib']-base['memory_mib'];left=new['memory_mib']-base['memory_mib']
 lines.append(f"- {platform}: 워클릿 전체 사용량 {saved:.1f}MiB 감소({saved/old['memory_mib']*100:.1f}%). 기본 ZigPool 대비 추가 사용량은 {extra:.1f}→{left:.1f}MiB다.")
lines+=['','## JS 160ms 점유 상태','',
'화면 검사와 CPU·메모리 검사를 별도로 실행했다. 지연은 Android gfxinfo 지연 프레임, iOS CADisplayLink 지연 콜백이다. 단계가 다른 지표를 같은 표시 누락률로 해석하지 않는다.','',
'| 플랫폼 | 엔진 | 평균 공백 % | 무공백 / 3 | 내용 오류 / 겹침 | CPU % | 메모리 MiB | 지연 % |','|---|---|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f"| {r['platform']} | {r['label']} | {r['blank_mean_percent']:.3f} | {r['zero_blank_runs']} | {r['wrong_frames']} / {r['overlap_frames']} | {r['stress_cpu_percent']:.1f} | {r['stress_memory_mib']:.1f} | {r['stress_late_percent']:.2f} |")
lines+=['','## 시작 시 비용','',
'각 엔진·플랫폼 2회, 시작 8초 동안 외부에서 표본을 얻었다. 조회 시간과 100ms 간격 사이의 순간 피크는 놓칠 수 있어 **관측 최고치**라고 부른다. 스크롤 전 수치이므로 위 종료 메모리와 측정 구간이 다르다.','',
'| 플랫폼 | 엔진 | 관측 최고 메모리 MiB, 각 2회 |','|---|---|---:|']
for r in rows:lines.append(f"| {r['platform']} | {r['label']} | {', '.join(f'{v:.1f}' for v in r['startup_peaks_mib'])} |")
lines+=['','최종 후보의 초기 변환 시간은 주 비교 9회에서 얻은 중앙값이다. 앱 시작 전체 시간이 아니며, UI 복원은 UI 스레드를 점유한다.','',
'| 플랫폼 | JS 배열 구성·직렬화 ms | UI 복원·공유값 대입 ms |','|---|---:|---:|']
for r in rows:
 if r['engine']=='template-compact':lines.append(f"| {r['platform']} | {r['encode_median_ms']:.1f} | {r['decode_median_ms']:.1f} |")
lines+=['','## 단순 셀 보조 검사','',
'각 1회로 주 비교 평균에 섞지 않았다.','',
'| 플랫폼 | 엔진 | 평균 공백 % | 내용 오류 / 겹침 프레임 |','|---|---|---:|---:|']
for r in m:
 if r['group'].endswith('simple'):lines.append(f"| {r['platform']} | {labels[r['engine']]} | {r['mean_blank_area_percent']:.3f} | {r['wrong_frames']} / {r['overlap_frames']} |")
lines+=['','## 판단과 남은 범위','',
'전체 데이터의 UI 접근과 내용 갱신 경로를 유지하면서 메모리 전달 표현을 줄이는 방향이다. 기본 ZigPool 수준까지 줄였다는 의미는 아니다. 템플릿·전용 뷰·추가 런타임의 비용이 남는다.','',
'고정 높이 simple/heavy의 Solo PoC다. 동적 높이, 임의 React 컴포넌트, 데이터 변경의 전체 원자성, 장시간 누수, 실물 구형 기기의 메모리 압박과 시작 체감은 검증하지 않았다. 기본 엔진이나 GPU API, CI 구성은 바꾸지 않았다.','',
'검증: Android/iOS arm64 Release 로컬 빌드, 린트, 라이브러리 타입 검사, 웹 빌드, 76개 테스트. 초기 문자열 보관 방식의 예비 결과 1회는 별도 보존하고 정식 평균에서 제외했다.','',
'![한글 메모리 결과](memory-summary-ko.png)','',
'![한글 데이터 전달 경로](memory-path-ko.png)','']
if (D/'attachments.json').exists():
 a={r['name']:r['href'] for r in json.loads((D/'attachments.json').read_text())}
 lines+=['## 별도 녹화','', '기존 ZigPool / 기존 UI 워클릿 / 메모리 개선 워클릿. 각기 다른 실행을 1배속·60fps로 합성했다. 정량 비교와 프레임 동기 비교가 아니다.','']
 for platform in ['android','ios']:lines += [platform,'',a[f'{platform}-compare-block.mp4'],'']
audits=[r for r in m if r['mode']=='audit']
lines+=['',f"화면 검사 {len(audits)}회, {sum(r['frames'] for r in audits):,}프레임에서 내용 오류 {sum(r['wrong_frames'] for r in audits)}회, 겹침 {sum(r['overlap_frames'] for r in audits)}회였다. 개선 워클릿은 무거운 셀 6회와 단순 셀 2회 모두 공백 0이었다.", '']
(D/'README.md').write_text('\n'.join(lines))
print('보고서 생성',len(m)+len(startup),'회')
