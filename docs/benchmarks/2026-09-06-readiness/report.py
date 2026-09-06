"""단계 추적·탐색·재검증을 섞지 않고 한글 표로 보고한다."""
from pathlib import Path
import json,statistics,math,csv
D=Path(__file__).resolve().parent
m=json.loads((D/'matrix.json').read_text())
labels={'zigpool-5':'기존 고정 5행','legend-5':'레전드리스트 5행','stable-5':'기존 선행 준비 5행','stable-12':'기존 선행 준비 12행','pending-stable-5':'대기 보정 5행','pending-stable-12':'대기 보정 12행','priority-5':'우선순위 5행','priority-stable-5':'우선순위+선행 5행','priority-stable-12':'우선순위+선행 12행','priority-pending-stable-12':'우선순위+보정 12행'}
def med(rs,k):return statistics.median(r[k] for r in rs)
def tab(head,rows):return '| '+' | '.join(head)+' |\n|'+'|'.join(['---']*len(head))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def group(os,n,mode,block):return [r for r in m if 'confirm-' in r['group'] and (r['platform'],r['name'],r['mode'],r['block_ms'])==(os,n,mode,block)]
a=[r for r in m if r['mode']=='audit'];assert all(r['wrong_frames']==r['overlap_frames']==0 and not r['blank_tail_open'] for r in a)
points=[]
for os in ['ios','android']:
 for n in dict.fromkeys(r['name'] for r in m if 'confirm-' in r['group'] and r['platform']==os):
  au=group(os,n,'audit',160);normal=group(os,n,'perf',0);cost=group(os,n,'perf',160)
  assert len(au)==len(normal)==len(cost)==3,(os,n)
  points.append(dict(cost_comparison_eligible=os!='android',platform=os,name=n,label=labels[n],normal_cpu=med(normal,'cpu_one_core_percent'),normal_memory=med(normal,'memory_after_mib'),normal_p95=med(normal,'p95_ms' if os=='android' else 'callback_p95_ms'),normal_late=med(normal,'late_percent' if os=='android' else 'late_callback_percent'),stress_cpu=med(cost,'cpu_one_core_percent'),stress_memory=med(cost,'memory_after_mib'),mean_blank=med(au,'mean_blank_area_percent'),worst_blank=max(r['max_blank_area_percent'] for r in au),max_duration=max(r['blank_episode_max_ms'] for r in au),zero_runs=sum(r['blank_episode_count']==0 for r in au),entry_ready=med(au,'entry_ready_percent'),p95=med(cost,'p95_ms' if os=='android' else 'callback_p95_ms'),late=med(cost,'late_percent' if os=='android' else 'late_callback_percent'),audit_samples=[{'run':r['run'],'mean':r['mean_blank_area_percent'],'max':r['max_blank_area_percent'],'duration':r['blank_episode_max_ms']} for r in au]))
(D/'confirmation-summary.json').write_text(json.dumps(points,ensure_ascii=False,indent=2)+'\n')
with (D/'comparison-ko.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n')
 w.writerow(['비용 통제 비교 포함','플랫폼','설정','일반 CPU %','일반 종료 메모리 MiB','부하 CPU %','부하 종료 메모리 MiB','평균 공백 %','최대 공백 %','최대 지속 ms','무공백 실행 수','진입 시 준비 %','부하 p95 ms','부하 지연 비율 %'])
 for p in points:w.writerow([p[k] for k in ['cost_comparison_eligible','platform','label','normal_cpu','normal_memory','stress_cpu','stress_memory','mean_blank','worst_blank','max_duration','zero_runs','entry_ready','p95','late']])
lines=['# 내용 준비 대기: 원인 추적과 개선 PoC\n','[원인·개선 효과·채택 판단](interpretation-ko.md)\n',f'RN 0.87.1에서 총 {len(m)}회 실행했다. 진단·탐색·재검증을 구분한다. 앱 기본값은 유지했고 GPU 경로는 바꾸지 않았다. [실험 방법과 옵션](methodology-ko.md)\n','## 단계별 대기\n','JS를 160ms 점유하는 진단 실행에서 주요 대기는 요청의 JS 수신 이전이었다. 우선순위는 이미 실행 중인 JS 루프를 중단하지 않는다. 수신 이후 렌더 시작이 대체로 빠른 상황에서는 우선순위만으로 큰 개선을 기대하기 어렵다.\n']
t=json.loads((D/'trace-summary.json').read_text());rs=[]
for n,v in t.items():
 key=n.removeprefix('1-').removesuffix('-measured');d=v['durations'];back=v['backlog_samples']
 rs.append([labels[key],v['phases']['request'],v['phases']['placed'],d['request->receive']['p95'],d['receive->render']['p95'],d['render->native_commit']['p95'],d['native_commit->placed']['p95'],statistics.median(x['latest_ms'] for x in back),statistics.median(x['oldest_ms'] for x in back)])
lines+=[tab(['진단 설정','요청 수','반영 수','수신 대기 p95 ms','렌더 시작 대기 p95 ms','렌더 시작→네이티브 p95 ms','배치 대기 p95 ms','최신 요청 대기 중앙값 ms','가장 오래된 요청 대기 중앙값 ms'],rs),'\n','각 설정 1회 진단이다. 요청은 합쳐질 수 있어 단계별 표본 수가 다르며 p95끼리 더하지 않는다. 벽시계 반올림 오차 약 1ms가 있다.\n','## 탐색 결과: 2회씩\n']
rs=[]
for n in dict.fromkeys(r['name'] for r in m if r['group']=='zerolist-readiness-ios-screen'):
 a=[r for r in m if r['group']=='zerolist-readiness-ios-screen' and r['name']==n]
 rs.append([labels[n],', '.join(f"{r['mean_blank_area_percent']:.3f}" for r in a),sum(r['blank_episode_count']==0 for r in a),f"{max(r['max_blank_area_percent'] for r in a):.1f}"])
lines+=[tab(['설정','실행별 평균 공백 %','무공백 횟수 / 2','최대 공백 %'],rs),'\n','우선순위 단독은 탐색에서 우위를 보이지 않았다. 대기 보정은 별도 순서의 재검증에서 기존 선행 준비와 직접 비교한다. 탐색과 재검증을 합산하지 않는다.\n']
for os in ['ios','android']:
 ps=[p for p in points if p['platform']==os]
 if os=='android':lines += ['**Android 비용 측정 두 그룹은 외부 Zig 테스트와 시간대가 겹쳐 통제된 성능 우위 판단에서 제외한다. 아래 비용·프레임은 참고 원자료다. [호스트 관측](host-contention.json)**\n']
 lines += [f'## {os} 별도 재검증: 각 조건 3회\n',f'![비용과 공백]({os}-readiness-ko.png)\n',tab(['설정','일반 CPU %','일반 종료 메모리 MiB','부하 CPU %','부하 종료 메모리 MiB','평균 공백 %','최대 공백 %','최대 지속 ms','무공백 횟수','진입 시 준비 %','부하 p95 ms','부하 지연 비율 %'],[[p['label'],f"{p['normal_cpu']:.1f}",f"{p['normal_memory']:.1f}",f"{p['stress_cpu']:.1f}",f"{p['stress_memory']:.1f}",f"{p['mean_blank']:.3f}",f"{p['worst_blank']:.1f}",f"{p['max_duration']:.1f}",f"{p['zero_runs']}/3",f"{p['entry_ready']:.1f}",f"{p['p95']:.2f}",f"{p['late']:.2f}"] for p in ps]),'\n']
 lines += [tab(['설정','일반 p95 ms','일반 지연 비율 %'],[[p['label'],f"{p['normal_p95']:.2f}",f"{p['normal_late']:.2f}"] for p in ps]),'\n']
 lines += [tab(['설정','실행별 평균 공백 %','실행별 최대 공백 %','실행별 최대 지속 ms'],[[p['label'],', '.join(f"{r['mean']:.3f}" for r in p['audit_samples']),', '.join(f"{r['max']:.1f}" for r in p['audit_samples']),', '.join(f"{r['duration']:.1f}" for r in p['audit_samples'])] for p in ps]),'\n']
smoke=[r for r in m if r['group']=='zerolist-readiness-android-priority-smoke']
if smoke:lines+=['## Android 우선순위 조합 동작 검사\n',tab(['설정','평균 공백 %','내용 불일치','겹침'],[[labels[r['name']],f"{r['mean_blank_area_percent']:.3f}",r['wrong_frames'],r['overlap_frames']] for r in smoke]),'각 1회 동작 검사이며 우선순위 옵션의 성능 순위를 정하는 근거로 사용하지 않는다.\n']
lines+=['## 정확성과 남은 범위\n',f'공백 검사 {len(audit := [r for r in m if r["mode"]=="audit"])}회에서 내용 불일치·겹침은 모두 0이었다. 이는 모든 설정이 무공백이었다는 뜻이 아니다. 일반 비용과 JS 부하 비용은 검사를 끈 별도 실행이다. 메모리는 종료 표본이며 피크가 아니다. iOS p95·지연 비율은 화면 갱신 콜백 계측으로 실제 GPU 표시 지연과 같지 않다.\n','실물 저사양 기기·동적 높이·발열·배터리는 미검증이다. 우선순위와 대기 보정은 기본값으로 승격하지 않은 PoC 옵션이다.\n','## 원자료\n','![공백의 직접 원인](blank-cause-ko.png)\n','[행렬](matrix.json) · [한글 CSV](comparison-ko.csv) · [재검증 집계](confirmation-summary.json) · [단계 추적](trace-summary.json) · [바이너리 해시](provenance.json)\n']
lines += [f'- [{p.name}]({p.name})' for p in sorted(D.glob('*-raw.zip'))]
(D/'README.md').write_text('\n'.join(lines))
