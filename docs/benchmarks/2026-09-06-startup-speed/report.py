"""새 바이너리의 시작·스크롤 결과를 수집하고 한글로 요약한다."""
from pathlib import Path
import json,statistics,zipfile,sys
D=Path(__file__).resolve().parent;root=Path(sys.argv[1])
startup=json.loads((root/'startup/results.json').read_text());assert len(startup)==44
summary=[];perf=[];audits=[]
for platform in ['ios','android']:
 for engine in ['template-worklet','template-compact']:
  rs=[r for r in startup if r['platform']==platform and r['engine']==engine and not r['warmup']];assert len(rs)==10
  row={'platform':platform,'engine':engine,'startup':{}}
  for key in ['render_begin','data_ready','content_ready','both']:
   vs=[r['data_and_content_ms'] if key=='both' else r['milliseconds'][key] for r in rs]
   row['startup'][key]={'median':statistics.median(vs),'min':min(vs),'max':max(vs)}
  if engine=='template-compact':
   base={r['run']:r for r in startup if r['platform']==platform and r['engine']=='template-worklet' and not r['warmup']}
   row['paired_faster_runs']=sum(r['data_and_content_ms']<base[r['run']]['data_and_content_ms'] for r in rs)
  row['perf']={}
  for block in [0,160]:
   all_rs=json.loads((root/f'{platform}-perf{block}/results.json').read_text())
   rs=[r for r in all_rs if r['engine']==engine];assert len(rs)==5
   late='late_percent' if platform=='android' else 'late_callback_percent'
   p95='p95_ms' if platform=='android' else 'callback_p95_ms'
   row['perf'][str(block)]={}
   for key,source in [('late',late),('p95',p95),('cpu','cpu_one_core_percent'),('memory','memory_after_mib')]:
    vs=[r[source] for r in rs];row['perf'][str(block)][key]={'mean':statistics.mean(vs),'min':min(vs),'max':max(vs)}
   perf += [dict(r,platform=platform) for r in rs]
  a=[r for r in json.loads((root/f'{platform}-audit160/results.json').read_text()) if r['engine']==engine];assert len(a)==1
  row['audit']=a[0];audits += [dict(r,platform=platform) for r in a]
  summary.append(row)
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(D/'startup-results.json').write_text(json.dumps(startup,ensure_ascii=False,indent=2))
(D/'scroll-results.json').write_text(json.dumps(perf+audits,ensure_ascii=False,indent=2))
for p in root.iterdir():
 if not p.is_dir():continue
 with zipfile.ZipFile(D/f'{p.name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in p.iterdir():
   if f.is_file():z.write(f,f.name)
labels={'template-worklet':'기존 UI 워클릿','template-compact':'메모리 개선 워클릿'}
lines=['# 시작 속도와 스크롤 지연 재검증','',
'10만 건 무거운 셀, RN 0.87.1 Release. 시작 40회·스크롤 비용 40회·화면 검사 4회와 별도 Android 지연 보조 6회다. 시작 준비 4회는 통계에서 제외했다. [측정 경계와 재현 방법](methodology-ko.md)','',
'**시작 준비는 개선됐지만 Android 스크롤 지연 비율은 증가했다.** 앞선 스크롤 성능 유지 설명을 수정한다. 호스트 외부 부하가 겹쳤으며 구현 비용과의 인과관계는 아직 분리하지 못했다.','',
'## 시작 시간','',
'네이티브 시작 진입부터의 시간이다. OS 프로세스 생성 이전부터의 앱 전체 시작 시간이나 실제 패널 표시 시각은 아니다. 아래는 각 10회 중앙값(ms)이다.','',
'| 플랫폼 | 엔진 | React 진입 | UI 데이터 접근 가능 | 첫 제목·배치 확인 | 둘 다 준비 |','|---|---|---:|---:|---:|---:|']
for r in summary:
 s=r['startup'];lines.append(f"| {r['platform']} | {labels[r['engine']]} | {s['render_begin']['median']:.1f} | {s['data_ready']['median']:.1f} | {s['content_ready']['median']:.1f} | {s['both']['median']:.1f} |")
lines+=['','| 플랫폼 | 기존 둘 다 준비 범위 ms | 개선 둘 다 준비 범위 ms | 중앙값 감소 | 같은 회차에서 개선 / 10 |','|---|---:|---:|---:|---:|']
for p in ['ios','android']:
 old,new=[r for r in summary if r['platform']==p];o=old['startup']['both'];n=new['startup']['both'];saved=o['median']-n['median']
 lines.append(f"| {p} | {o['min']:.1f}~{o['max']:.1f} | {n['min']:.1f}~{n['max']:.1f} | {saved:.1f}ms ({saved/o['median']*100:.1f}%) | {new['paired_faster_runs']} |")
lines+=['','## 스크롤 비용 재측정','',
'각 5회 평균. 괄호는 실행별 최솟값~최댓값이다. Android 지연 프레임과 iOS 지연 콜백은 서로 다른 지표다.','',
'| 플랫폼 | JS 점유 ms | 엔진 | 지연 % (범위) | 간격/시간 p95 ms | CPU % | 종료 메모리 MiB |','|---|---:|---|---:|---:|---:|---:|']
for r in summary:
 for b,s in r['perf'].items():
  l=s['late'];lines.append(f"| {r['platform']} | {b} | {labels[r['engine']]} | {l['mean']:.2f} ({l['min']:.2f}~{l['max']:.2f}) | {s['p95']['mean']:.2f} | {s['cpu']['mean']:.1f} | {s['memory']['mean']:.1f} |")
lines+=['','## 해석','',
'시작 준비와 스크롤 처리량을 구분한다. React 진입 이후에는 데이터 전달, 워클릿 초기화, React 커밋과 네이티브 뷰 준비가 포함된다. 기존 경로는 객체 배열을 shared value 초기값으로 넣고 effect에서도 대입한다. 개선 경로는 빈 공유값으로 시작해 필드 배열을 한 번 전달한다. 결과는 이 변경 묶음의 비교이며 JSON 표현 한 가지만의 효과를 분리한 실험은 아니다.','',
'스크롤 p95와 지연 비율은 작은 차이와 실행별 범위를 함께 봐야 한다. 지연 프레임 비율이 절반이 됐다고 스크롤 처리 속도가 두 배라는 뜻은 아니다. 초기 UI 복원 작업 자체는 남지만, 기존 경로의 총 준비 비용보다 작은지 시작 지표로 직접 비교했다.','',
'## 정확성과 한계','',f"추가 스크롤 화면 검사 {len(audits)}회에서 공백 발생 {sum(r['blank_episode_count'] for r in audits)}회, 내용 오류 {sum(r['wrong_frames'] for r in audits)}프레임, 겹침 {sum(r['overlap_frames'] for r in audits)}프레임이었다.",
f"시작 검사(준비 포함) {len(startup)}회·{sum(r['audit_frames'] for r in startup)}프레임에서 내용 오류 {sum(r['wrong_frames'] for r in startup)}프레임, 겹침 {sum(r['overlap_frames'] for r in startup)}프레임이었다.",'',
'시작 진단은 첫 화면의 제목·좌표와 UI 데이터 접근을 관측한다. 초기 본문·합계·색상 전체, 실제 GPU 표시 완료, 장시간 누수, 동적 높이와 임의 React 자식, 실물 구형 기기는 검증하지 않았다. 초기 UI 복원 비용이 사라진 것은 아니다. 외부 호스트 부하 미통제 조건의 반복 측정이다.','',
'검증: Android/iOS arm64 Release 빌드, 린트·라이브러리 타입 검사, 76개 테스트 통과.','',
'![한글 시작 속도 비교](startup-summary-ko.png)','']
follow=json.loads((root/'android-stress-followup/results.json').read_text());assert len(follow)==6
(D/'followup-results.json').write_text(json.dumps(follow,ensure_ascii=False,indent=2))
lines+=['## Android 점유 조건 보조 비교 6회','',
'주 비교의 개선 후보 3회차에서 지연 8%, p95 40ms가 관측됐다. 같은 구간 외부 Zig 빌드·테스트와 호스트 부하 증가(1분 부하 약 17.4→20.9)가 기록됐지만 인과관계는 확정하지 않는다. 이 실행을 포함한 주 비교 평균 2.68%를 그대로 보존했다. 추가 6회는 주 비교 평균에 합치지 않는다.','',
'| 엔진 | 지연 비율 각 3회 % | 평균 % | p95 평균 ms |','|---|---|---:|---:|']
for engine in ['template-worklet','template-compact']:
 a=[r for r in follow if r['engine']==engine];assert len(a)==3
 lines.append(f"| {labels[engine]} | {', '.join(str(r['late_percent']) for r in a)} | {statistics.mean(r['late_percent'] for r in a):.2f} | {statistics.mean(r['p95_ms'] for r in a):.2f} |")
lines+=['','시작 준비 개선은 양쪽 10/10회 확인했다. Android 지연 비율은 주 비교·보조 비교에서 증가했으므로 앞선 스크롤 성능 유지 설명을 수정한다. 외부 부하 영향과 구현 비용을 분리하는 검증은 남아 있다. 총 정식·보조 90회, 별도 시작 준비 4회다.','']
(D/'README.md').write_text('\n'.join(lines))
print('시작40 + 스크롤40 + 정확성4 + 보조6, 별도 시작 준비4 수집 완료')
