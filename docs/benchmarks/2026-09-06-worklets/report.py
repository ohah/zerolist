"""원자료에서 한글 표와 요약 JSON을 생성한다. 비용은 탐색값이다."""
from pathlib import Path
import json,statistics
D=Path(__file__).resolve().parent
matrix=json.loads((D/'matrix.json').read_text());traces=json.loads((D/'traces.json').read_text())
labels={'zigpool':'기존 ZigPool','template-js':'JS 수신 템플릿','template-worklet':'UI 수신 템플릿'}
summary=[]
for platform in ['ios','android']:
 for engine in labels:
  audit=[r for r in matrix if r['group']==f'{platform}-audit160' and r['engine']==engine]
  normal=[r for r in matrix if r['group']==f'{platform}-perf0' and r['engine']==engine]
  stress=[r for r in matrix if r['group']==f'{platform}-perf160' and r['engine']==engine]
  assert len(audit)==len(normal)==len(stress)==3
  avg=lambda rs,key:statistics.mean(r[key] for r in rs)
  late='late_callback_percent' if platform=='ios' else 'late_percent'
  row={'platform':platform,'engine':engine,'label':labels[engine], 'audit_repeats':3,
   'blank_mean_percent':avg(audit,'mean_blank_area_percent'),'blank_each_percent':[r['mean_blank_area_percent'] for r in audit],
   'blank_max_percent':max(r['max_blank_area_percent'] for r in audit),'blank_episode_max_ms':max(r['blank_episode_max_ms'] for r in audit),
   'entry_ready_percent':avg(audit,'entry_ready_percent'),'zero_blank_runs':sum(r['blank_episode_count']==0 for r in audit),
   'wrong_frames':sum(r['wrong_frames'] for r in audit),'overlap_frames':sum(r['overlap_frames'] for r in audit),
   'normal_cpu_percent':avg(normal,'cpu_one_core_percent'),'normal_memory_mib':avg(normal,'memory_after_mib'),
   'normal_late_percent':avg(normal,late),'stress_cpu_percent':avg(stress,'cpu_one_core_percent'),
   'stress_memory_mib':avg(stress,'memory_after_mib'),'stress_late_percent':avg(stress,late),
   'controlled_cost_comparison':False}
  summary.append(row)
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
lines=['# JS 수신을 우회하는 UI 워클릿 템플릿 PoC','',f'RN 0.87.1에서 {len(matrix)}회 실행했다. **고정 높이 셀의 내용 갱신이 RN JS의 처리를 기다리지 않는 경로**를 구현했다. GPU API는 바꾸지 않았다. [구현·제약·측정 방법](methodology-ko.md)','',
'## JS를 160ms씩 막았을 때 실제 화면','',
'각 엔진 3회, 10만 건 heavy, 동일 14개 슬롯이다. 평균 공백은 이동 중 화면에서 비어 있던 면적의 실행별 평균을 다시 평균한 값이다. 제목·위치 불일치와 겹침은 별도로 검사했다.','',
'| 플랫폼 | 엔진 | 평균 공백 % | 최대 공백 % | 최대 지속 ms | 진입 시 준비 % | 무공백 / 3 | 내용 오류 / 겹침 프레임 |',
'|---|---|---:|---:|---:|---:|---:|---:|']
for r in summary:lines.append(f"| {r['platform']} | {r['label']} | {r['blank_mean_percent']:.3f} | {r['blank_max_percent']:.1f} | {r['blank_episode_max_ms']:.1f} | {r['entry_ready_percent']:.1f} | {r['zero_blank_runs']} | {r['wrong_frames']} / {r['overlap_frames']} |")
lines+=['','Android UI 수신의 준비 비율 99.2%에는 행 경계의 1px 공백이 있는 표본 1개가 포함된다. 공백 지표는 2px 오차를 허용하므로 무공백 판정과 모순되지 않는다.']
lines+=['','## 비용: 화면 검사 없이 별도 실행','',
'**호스트의 외부 작업을 완전히 통제하지 못한 탐색값이다.** 실제 저사양 태블릿의 속도·전력·발열 순위로 일반화하지 않는다. CPU는 코어 하나 기준 앱 전체 사용률이다. Android는 종료 PSS, iOS는 종료 RSS다. 시작 최고 메모리는 측정하지 않았다.','',
'| 플랫폼 | 엔진 | 평상시 CPU % | 평상시 메모리 MiB | 평상시 지연 % | JS 부하 CPU % | JS 부하 메모리 MiB | JS 부하 지연 % |',
'|---|---|---:|---:|---:|---:|---:|---:|']
for r in summary:lines.append(f"| {r['platform']} | {r['label']} | {r['normal_cpu_percent']:.1f} | {r['normal_memory_mib']:.1f} | {r['normal_late_percent']:.2f} | {r['stress_cpu_percent']:.1f} | {r['stress_memory_mib']:.1f} | {r['stress_late_percent']:.2f} |")
lines+=['','지연은 Android에서는 gfxinfo 지연 프레임, iOS에서는 CADisplayLink 지연 콜백이다. 두 플랫폼의 지연 비율은 직접 비교하지 않는다. 과거 바이너리의 결과도 이 표에 섞지 않았다.','',
'## 수신 대기의 변화','',
'별도 진단 각 1회에서 같은 버전의 첫 요청·수신·반영·배치를 연결했다. 반복 커밋은 첫 반영 이후의 수신 대기로 중복 계산하지 않았다. UI 로그는 출력이 늦어질 수 있어 로그 접두 시각 대신 워클릿 안에서 기록한 wall 값을 사용했다. 벽시계 반올림 오차 약 1ms가 있으며 단계별 p95를 더하지 않는다.','',
'| 플랫폼 | 엔진 | 요청 / 수신 / 반영 수 | 요청→수신 p95 ms | 수신→반영 p95 ms | 반영→배치 p95 ms |',
'|---|---|---:|---:|---:|---:|']
for r in traces:lines.append(f"| {r['platform']} | {labels[r['engine']]} | {r['requested']} / {r['received']} / {r['committed']} | {r['request_to_receive']['p95_ms']} | {r['receive_to_commit']['p95_ms']} | {r['commit_to_placed']['p95_ms']} |")
lines+=['','요청은 합쳐질 수 있어 단계별 표본 수가 다르다. 원시 분포의 최소값·음수 표본 수는 traces.json에 남겼다.']
lines+=['','## 보조 검사: 단순 셀과 데이터 크기','',
'단순 셀 검사는 각 템플릿·플랫폼 1회이며, 고정 높이 heavy 주 비교와 분리했다.','',
'| 플랫폼 | 엔진 | 평균 공백 % | 내용 오류 프레임 | 겹침 프레임 |','|---|---|---:|---:|---:|']
for r in matrix:
 if r['group'].endswith('-simple'):
  lines.append(f"| {r['platform']} | {labels[r['engine']]} | {r['mean_blank_area_percent']:.3f} | {r['wrong_frames']} | {r['overlap_frames']} |")
lines+=['','heavy의 풀 크기를 유지하고 데이터만 1만 건으로 줄인 평상시 1회 대조다. 10만 건 열은 주 비교 3회 평균이다. 세부 메모리 원인을 각각 분리한 실험은 아니다.','',
'| 플랫폼 | 엔진 | 1만 건 메모리 MiB | 10만 건 메모리 MiB |','|---|---|---:|---:|']
for r in matrix:
 if r['group'].endswith('-10k'):
  main=next(v for v in summary if v['platform']==r['platform'] and v['engine']==r['engine'])
  lines.append(f"| {r['platform']} | {labels[r['engine']]} | {r['memory_after_mib']:.1f} | {main['normal_memory_mib']:.1f} |")
lines+=['','## 해석','',
'같은 텍스트 컴포넌트와 UI 계산을 사용하는 두 템플릿을 비교해야 요청 수신 우회의 효과를 구분할 수 있다. 기존 ZigPool 대비 차이는 React 재렌더 제거와 전용 텍스트 구현의 영향도 포함한다. 워클릿은 계산량을 없애지 않고 실행 위치를 바꾸며, 관측된 메모리에는 데이터 전달, 추가 런타임 상태, 워클릿과 전용 뷰의 비용이 함께 포함된다.','',
'이번 결과는 고정 템플릿 경로를 더 개발해볼 근거이지, 일반 React 컴포넌트를 그대로 지원하는 범용 리스트의 완성이나 기본값 전환의 근거가 아니다. 메모리 절감, 동적 높이, 데이터 변경의 일관성, 실제 구형 기기 검증이 남았다.','',
'## 자료','',
'- summary.json: 표의 집계값. matrix.json: 실행별 수치. groups.json: 조건. traces.json: 단계별 진단.',
'- 각 그룹의 raw.zip: 정량 구간, 호스트 부하, 실행 로그, 프레임 원자료.',
'- provenance.json: 소스와 앱 바이너리 해시. run_matrix.py: 비교 재실행.',
'- 별도 녹화: 아래 영상은 1배속이며 서로 다른 실행을 나란히 합성한 설명용 자료다. 정량 측정과 프레임별 동기 비교가 아니다.','']
lines+=['','![한글 결과표](worklet-summary-ko.png)','','![한글 처리 경로](worklet-path-ko.png)','']
if (D/'attachments.json').exists():
 attachments={a['name']:a['href'] for a in json.loads((D/'attachments.json').read_text())}
 for platform in ['android','ios']:
  name=f'{platform}-compare-block.mp4'
  lines += [f'### {platform} 비교 영상','',attachments[name],'']
(D/'README.md').write_text('\n'.join(lines))
print('한글 보고서 생성')
