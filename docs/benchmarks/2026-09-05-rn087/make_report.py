"""RN 0.87.1 결과를 구버전 자료와 구분하여 한글 보고서로 작성한다."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent
s=json.loads((D/'summary.json').read_text());p=json.loads((D/'points.json').read_text());matrix=json.loads((D/'matrix.json').read_text())
old=json.loads((D.parent/'2026-09-05-budget'/'summary.json').read_text())
labels={'flatlist':'FlatList','flashlist':'FlashList','legend':'LegendList','zerolist':'기존 ZeroList','zigpool':'ZigPool 고정','stable':'ZigPool 범위 유지'}
def name(n):
 a,b=n.rsplit('-',1);return f'{labels[a]} · {b}행'
def med(r,k):return r[k]['median']
def table(h,rs):return '| '+' | '.join(h)+' |\n|'+'|'.join(['---']*len(h))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rs)
lines=['# RN 0.87.1에서 다시 비교한 리스트 성능\n',f'최신 안정판 확인 당시 npm latest는 **0.87.1**이었다. 같은 React 19.2.3, FlashList 2.3.1, LegendList 2.0.19를 유지하고 RN 및 관련 네이티브 도구를 갱신했다. 기존 RN 0.85.0의 207회와 별도로 **{len(matrix)}회**를 측정했다.\n','Android·iOS 모두 arm64 Release, Fabric, Hermes다. 각 실행 전 앱의 네이티브 RN 버전이 0.87.1인지 검사했다. Android 에뮬레이터와 iOS 시뮬레이터를 사용했다. 실물 저사양 기기 결과는 아니다.\n','## 조건과 선택\n','이전 탐색에서 Android는 메모리 약 160MiB 근처의 FlatList 5행, FlashList 2행, ZeroList 5행, ZigPool 5행을 선택했고 LegendList 5행을 함께 유지했다. iOS는 공백을 억제한 FlashList 12행과 ZigPool 범위 유지 12행을 포함했다. **이번 버전에서 모든 준비량을 다시 최적화한 순위는 아니다.**\n','10만 건의 고정 높이 무거운 셀, 준비 스와이프 12회와 측정 스와이프 18회다. 일반 비용·JS 부하 공백·JS 부하 비용은 각각 별도 3회다. JS 부하는 160ms 점유 후 40ms 여유를 반복한다. 측정 중 다른 플랫폼의 앱은 종료하며 화면 녹화와 빌드는 하지 않았다.\n','[기존 상세 측정 방법](../2026-09-05-budget/methodology-ko.md)을 동일하게 사용했다. 메모리는 종료 시점 PSS(Android)/RSS(iOS)이며 최대 사용량이 아니다. CPU는 앱 프로세스 전체를 1코어 기준으로 표시한다. Android와 iOS 수치를 직접 비교하지 않는다. 같은 제스처를 입력했지만 관성·이벤트 처리에 따라 이동 거리가 다를 수 있으므로 CPU 차이를 항목 처리 속도의 배수로 환산하지 않는다. 원자료의 travel_rows로 이동 범위를 확인할 수 있다.\n']
# 요약도 측정값에서 계산한다. 사전에 우위를 가정하지 않는다.
def normal(platform,n):return next(r for r in s if r['platform']==platform and r['name']==n and r['mode']=='perf' and r['block_ms']==0)
f=normal('android','flatlist-5');z=normal('android','zigpool-5')
delta=(med(z,'cpu_one_core_percent')/med(f,'cpu_one_core_percent')-1)*100
sp=next(r for r in p if r['platform']=='ios' and r['name']=='stable-12')
fp=next(r for r in p if r['platform']=='ios' and r['name']=='flashlist-12')
audit=[r for r in matrix if r['platform']=='ios' and r['name']=='stable-12' and r['mode']=='audit']
zero=sum(r['mean_blank_area_percent']==0 for r in audit)
lines += ['## 결과 판단\n',f"Android 일반 스크롤에서 ZigPool의 CPU는 FlatList 대비 **{delta:+.1f}%**였고, 종료 메모리는 각각 **{med(z,'memory_after_mib'):.1f}/{med(f,'memory_after_mib'):.1f}MiB**였다. p95 중앙값은 **{med(z,'p95_ms'):.0f}/{med(f,'p95_ms'):.0f}ms**다. 프레임 시간의 반복 범위를 함께 확인하며 앱 전체 속도의 배수로 환산하지 않는다.\n",f"iOS JS 부하에서 범위 유지 12행의 공백 없는 실행은 **{zero}/{len(audit)}회**였다. 종료 RSS는 **{sp['memory_mib']:.1f}MiB**, FlashList 12행은 **{fp['memory_mib']:.1f}MiB**였다. 최대 공백 면적은 각각 **{sp['worst_blank_area_percent']:.1f}%/{fp['worst_blank_area_percent']:.1f}%**였다. 평균 공백 중앙값이 같아도 순간 공백 품질이 같은 것은 아니다.\n",'[실제 개발 가치와 제품화 조건](decision-ko.md)\n']
lines += ['![RN 0.87.1 일반 비용](normal-cost-ko.png)\n', '![RN 0.87.1 Android 비용과 공백](android-budget-ko.png)\n', '![RN 0.87.1 iOS 비용과 공백](ios-budget-ko.png)\n']
for platform in ['android','ios']:
 lines += [f'## {platform}: 일반 스크롤\n']
 rows=[]
 for r in s:
  if r['platform']!=platform or r['mode']!='perf' or r['block_ms']!=0:continue
  k='p95_ms' if platform=='android' else 'callback_p95_ms';q=r[k]
  rows.append([name(r['name']),f"{med(r,'memory_after_mib'):.1f}",f"{med(r,'cpu_one_core_percent'):.1f}",f"{q['median']:.2f}",f"{q['min']:.2f}–{q['max']:.2f}",r['n']])
 lines += [table(['설정','종료 메모리 MiB','CPU %','p95 ms','p95 범위','반복'],rows),'\n']
 lines += [f'## {platform}: JS가 바쁠 때\n']
 rows=[]
 for r in p:
  if r['platform']!=platform:continue
  rows.append([name(r['name']),f"{r['memory_mib']:.1f}",f"{r['blank_area_percent']:.3f}",f"{r['worst_blank_area_percent']:.2f}",f"{r['cpu_percent']:.1f}",f"{r['frame_p95_ms']:.2f}",f"{r['audit_n']}/{r['perf_n']}"])
 lines += [table(['설정','메모리 MiB','평균 공백 %','최대 공백 %','CPU %','p95 ms','공백/비용 반복'],rows),'\n']
lines += ['iOS의 p95는 **CADisplayLink 콜백 간격**이며 실제 표시 프레임 지연이 아니다. 평균 공백은 이동 중 관측 프레임의 빈 면적 평균이다. 표의 평균 공백은 실행 간 중앙값, 최대 공백은 모든 반복의 최댓값이다. 중앙값 0%만으로 모든 실행이 공백 없었다고 말하지 않는다.\n','## RN 버전별 일반 스크롤 비교\n','같은 설정만 비교했다. 서로 다른 시점의 실행이므로 아래 변화 전체를 RN 업그레이드의 인과 효과로 단정하지 않는다.\n']
rows=[]
for r in s:
 if r['mode']!='perf' or r['block_ms']!=0:continue
 a=next((v for v in old if all(v[k]==r[k] for k in ['platform','name','mode','block_ms'])),None)
 if not a:continue
 k='p95_ms' if r['platform']=='android' else 'callback_p95_ms'
 rows.append([r['platform']+' · '+name(r['name']),f"{med(a,'cpu_one_core_percent'):.1f} → {med(r,'cpu_one_core_percent'):.1f}",f"{med(a,'memory_after_mib'):.1f} → {med(r,'memory_after_mib'):.1f}",f"{med(a,k):.2f} → {med(r,k):.2f}"])
lines += [table(['같은 설정','CPU %: 0.85 → 0.87','메모리 MiB: 0.85 → 0.87','p95 ms: 0.85 → 0.87'],rows),'\n','[개발 가치와 제품화 조건](decision-ko.md)\n','## 검증 및 재현\n','- Android·iOS Release 빌드 통과, JS 테스트 73개 통과, 린트·라이브러리 타입 검사·라이브러리 빌드 통과. 빌드 CI 추가 없음.\n- Android: 공식 템플릿에 맞춰 SDK 37, Gradle 9.4.1, Kotlin 2.2.0 및 AGP 9 호환 플래그 적용. targetSdk 36 유지.\n- iOS: 잔존한 0.85.0 사전 빌드 코어를 `pod update React-Core-prebuilt --no-repo-update`로 갱신했다. [실제 Pod 잠금 스냅샷](pods-lock.txt)에서 React-Core-prebuilt 0.87.1 확인 가능.\n- [측정 행렬](matrix.json), [집계](summary.json), [CSV](comparison-ko.csv), [바이너리 및 검증](provenance.json), [실행 스크립트](run_matrix.py).\n- iOS는 RN 0.87의 정보 로그가 simctl 콘솔에 나타나지 않아 Solo 계측 태그를 NSLog에도 기록했다. 최초 로그 확인 실패 실행은 정량 결과에 넣지 않았다. 마지막 iOS 비용 그룹은 simctl FIFO 충돌로 미실행한 시도가 있어, 이미 완료한 결과를 보존하고 같은 조건으로 RESUME=1을 사용해 이어갔다. 실패 로그도 원자료 압축에 보존했다.\n- 재측정: 새 출력 경로를 지정해 `record.py` 사용. `run_matrix.py`의 출력 경로가 이미 존재하면 덮어쓰지 않고 중단한다.\n']
lines += ['## 별도 비교 영상\n','정량 측정 후 RN 0.87.1 앱으로 별도 녹화했다. 각 패널은 다른 실행이며 1배속·60fps 합성이다. 짧은 클립의 끝부분은 마지막 화면을 유지한다. Android는 FlatList 5행·FlashList 2행·ZigPool 고정 5행, iOS는 FlatList 5행·FlashList 12행·ZigPool 범위 유지 12행이다.\n','[Android 영상](android-compare-block.mp4) · [iOS 영상](ios-compare-block.mp4) · [녹화 조건](capture-manifest.json) · [영상 검사](video-validation.json)\n']
lines += ['## 원자료 압축 파일\n'] + [f'- [{q.name}]({q.name})' for q in sorted(D.glob('*-raw.zip'))]
(D/'README.md').write_text('\n'.join(lines))
assert len(matrix)==99,len(matrix)
assert all(r.get('wrong_frames',0)==0 and r.get('overlap_frames',0)==0 for r in matrix),'내용 불일치 또는 겹침 발견: 결과를 검토해야 함'
