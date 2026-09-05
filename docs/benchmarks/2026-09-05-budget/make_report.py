"""최종 집계에서 한글 보고서를 만든다."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent
summary=json.loads((D/'summary.json').read_text());matrix=json.loads((D/'matrix.json').read_text());points=json.loads((D/'points.json').read_text())
labels={'flatlist':'FlatList','flashlist':'FlashList','legend':'LegendList','zerolist':'기존 ZeroList','zigpool':'ZigPool 고정','stable':'ZigPool 범위 유지'}
def label(n):
 f,r=n.rsplit('-',1);return f'{labels[f]} · {r}행'
def get(os,name,mode,block):return next(r for r in summary if r['platform']==os and r['name']==name and r['mode']==mode and r['block_ms']==block)
def v(r,k):return r[k]['median']
def span(r,k,dec=1):return f"{r[k]['min']:.{dec}f}–{r[k]['max']:.{dec}f}"
a=get('android','flatlist-5','perf',0);z=get('android','zigpool-5','perf',0);old=get('android','zerolist-5','perf',0)
flash=get('ios','flashlist-12','perf',160);stable=get('ios','stable-12','perf',160)
cpu_saving=(1-v(z,'cpu_one_core_percent')/v(a,'cpu_one_core_percent'))*100
mem_saving=v(flash,'memory_after_mib')-v(stable,'memory_after_mib')
lines=['# 같은 메모리와 공백 수준에서 비교한 다섯 리스트 — RN 0.85.0','',
'**이번 고정 높이·10만 건 조건에서는 ZigPool이 비슷한 메모리의 FlatList보다 느려졌다는 근거가 없었고, CPU 비용이 낮았다.** iOS에서는 범위 유지 예측이 같은 공백 수준을 더 적은 메모리로 달성하는 후보였다. 실험을 계속할 근거는 있지만, 실물 저사양 기기와 동적 높이를 검증한 제품 도입 결론은 아니다.','',
f'유효 실행은 총 **{len(matrix)}회**다. 전체 17개 설정을 양 플랫폼에서 정상 공백·JS 부하 공백·JS 부하 성능으로 탐색했고, Android 7개·iOS 8개 후보의 부하 공백/성능은 총 3회, 정상 성능은 별도 3회로 비교했다. 초기 보관량과 검사 반올림을 조정하기 전 실행은 합산하지 않았다.','',
'[상세 측정 방법과 한계](methodology-ko.md) · [설정 선택 근거](selection.json) · [한글 CSV](comparison-ko.csv)','',
'## 정상 조건: 얼마나 느린가','',
f'Android 약 160MiB 구간에서 FlatList p95 중앙값은 **{v(a,"p95_ms"):.0f}ms**, ZigPool은 **{v(z,"p95_ms"):.0f}ms**, 기존 ZeroList는 **{v(old,"p95_ms"):.0f}ms**였다. p95는 느린 상위 5% 경계다. 전체 실행 속도의 배수로 바꾸지 않는다.','',
f'ZigPool과 FlatList의 CPU 중앙값은 각각 **{v(z,"cpu_one_core_percent"):.1f}% / {v(a,"cpu_one_core_percent"):.1f}%**로, 이번 같은 입력에서 ZigPool이 약 **{cpu_saving:.1f}%** 낮았다. 프레임 시간 분포는 겹치므로 프레임이 그 비율만큼 빨라졌다는 의미는 아니다. GPU API를 바꾼 실험도 아니다.','',
'![정상 조건 성능](normal-cost-ko.png)','']
for os,title in [('android','Android'),('ios','iOS')]:
 lines += [f'### {title} 정상 성능: 각 3회','', '| 설정 | 종료 메모리 MiB | CPU % | p95 ms | p95 범위 | 지연 비율 % |','|---|---:|---:|---:|---:|---:|']
 for r in summary:
  if r['platform']!=os or r['mode']!='perf' or r['block_ms']!=0:continue
  pk='p95_ms' if os=='android' else 'callback_p95_ms';lk='late_percent' if os=='android' else 'late_callback_percent'
  lines.append(f'| {label(r["name"])} | {v(r,"memory_after_mib"):.1f} | {v(r,"cpu_one_core_percent"):.1f} | {v(r,pk):.2f} | {span(r,pk,2)} | {v(r,lk):.2f} |')
 lines += ['']
lines += ['iOS의 p95·지연 비율은 CADisplayLink 콜백 간격이며 실제 표시 프레임의 끊김이 아니다. Android PSS와 iOS RSS도 직접 비교하지 않는다. CPU는 프로세스 전체를 1코어 기준으로 나타낸 비율이다.','',
'## JS가 바쁠 때: 같은 메모리 구간과 같은 공백 수준','',
'JS를 160ms 점유하고 40ms 여유를 반복한다. 모든 목록에 같은 부하를 주며 전용 반영 지연 타이머는 사용하지 않는다. 공백 검사의 메모리가 아니라, 검사 로그를 끈 별도 성능 실행의 메모리를 사용했다.','']
for os,title in [('android','Android'),('ios','iOS')]:
 lines += [f'### {title} 전체 준비량 탐색','',f'![{title} 메모리와 공백]({os}-budget-ko.png)','',
 '| 설정 | 메모리 MiB | 평균 공백 면적 % | 공백 이동 프레임 % | 최대 공백 면적 % | CPU % | 공백/성능 반복 |','|---|---:|---:|---:|---:|---:|---:|']
 for p in points:
  if p['platform']!=os:continue
  lines.append(f'| {label(p["name"])} | {p["memory_mib"]:.1f} | {p["blank_area_percent"]:.3f} | {p["blank_frames_percent"]:.2f} | {p["worst_blank_area_percent"]:.2f} | {p["cpu_percent"]:.1f} | {p["audit_n"]}/{p["perf_n"]} |')
 lines += ['']
lines += ['평균 공백은 이동 중 관측 프레임에서 비어 있는 세로 면적의 평균이다. 2px/포인트 반올림 오차를 허용했다. 최대 공백은 반복 실행 전체의 최댓값이다. 평균 0% 중앙값만으로 모든 실행에 공백이 없었다고 말하지 않는다.','',
'### 반복한 주요 비교의 범위','',
'| 플랫폼·설정 | 메모리 범위 MiB | 평균 공백 면적 범위 % | CPU 범위 % |','|---|---:|---:|---:|']
for os,names in [('android',['flatlist-5','flashlist-2','flashlist-5','zigpool-5']),('ios',['flatlist-5','flashlist-5','flashlist-12','zigpool-5','stable-5','stable-12'])]:
 for name in names:
  p=get(os,name,'perf',160);a1=get(os,name,'audit',160)
  lines.append(f'| {os} · {label(name)} | {span(p,"memory_after_mib")} | {span(a1,"mean_blank_area_percent",3)} | {span(p,"cpu_one_core_percent")} |')
small_a=get('ios','stable-5','audit',160);base_a=get('ios','zigpool-5','audit',160)
small_p=get('ios','stable-5','perf',160);base_p=get('ios','zigpool-5','perf',160)
lines += ['', '### 풀 크기를 늘리지 않은 예측', '',
 f'iOS에서 기본 5행과 범위 유지 예측 5행은 모두 풀 14개다. 종료 RSS 중앙값은 각각 **{v(base_p,"memory_after_mib"):.1f}/{v(small_p,"memory_after_mib"):.1f}MiB**, 평균 공백 면적 중앙값은 **{v(base_a,"mean_blank_area_percent"):.3f}/{v(small_a,"mean_blank_area_percent"):.3f}%**였다. 작은 예측의 공백 범위는 {span(small_a,"mean_blank_area_percent",3)}%다. 풀을 늘린 효과와 범위 배분·유지 효과를 구분해야 하며, 이 작은 풀에서도 공백을 모두 없앤 것은 아니다.', '']
lines += ['',f'iOS 공백 억제 후보인 FlashList 12행과 범위 유지 예측 12행의 종료 RSS 중앙값 차이는 **{mem_saving:.1f}MiB**였다. 공칭 여유가 같아도 내부 보관량·갱신·메모리 관리가 다르므로 메모리가 같지는 않다. 최대 메모리나 GC 후 최소 사용량을 측정한 것은 아니다.','',
'## 판단','',
'- **ZigPool 접근은 계속 검증할 가치가 있다.** Android의 비슷한 메모리 구간에서 CPU 비용이 낮았고, iOS 범위 유지 예측은 메모리와 공백을 함께 개선할 후보였다.','- **Android에서는 고정 5행이 우선 후보다.** 같은 작은 풀의 범위 유지 예측은 부하 p95가 더 높아 기본 적용 근거가 없었다.',
'- **작은 풀만 고집하면 공백은 남는다.** ZigPool도 준비 공간의 제약을 받는다. 범위를 유지하는 예측과 충분한 여유의 결합을 평가해야 한다.','- **기존 ZeroList는 이번 정상 조건의 CPU와 p95 비용이 더 컸다.** GPU 선택 하나로 설명되는 차이가 아니라 셀 갱신·생성·재사용 경로 전체의 비교다.','- **보편적인 라이브러리 순위로 확장하지 않는다.** FlashList의 작은 여유 설정은 낮은 메모리 후보이고, 각 목록의 기능·동적 높이·초기 표시·실물 기기의 비용은 아직 이 표에 없다.','- **제품 기본값은 유지한다.** bufferRows와 공통 검사는 Solo 예제의 측정 옵션이다. 구형 태블릿에서 메모리 압박·GC·발열과 실제 표시 프레임을 확인하기 전 일반 도입을 확정하지 않는다.','',
'## 별도 비교 영상','',
'정량 실행이 모두 끝난 뒤 같은 데이터와 JS 부하로 별도 녹화했다. Android는 FlatList 5행·FlashList 2행·ZigPool 고정 5행, iOS는 FlatList 5행·FlashList 5행·범위 유지 예측 12행이다. 서로 다른 실행이며 같은 시각의 같은 행을 비교하는 영상은 아니다. 원본은 1배속이고, 합성본은 60fps로 배치하며 짧은 클립이 끝나면 마지막 화면을 유지한다.','',
'- [Android 비교](android-compare-block.mp4)','- [iOS 비교](ios-compare-block.mp4)','',
'## 검증·재현·원자료','',
'73개 테스트, 린트, 라이브러리 타입 검사와 Android arm64 Release·iOS arm64 시뮬레이터 Release 빌드를 통과했다. 빌드 CI는 추가하지 않았다.','',
'- [전체 원자료 행렬](matrix.json), [집계](summary.json), [비교 점](points.json), [실행 그룹](groups.json)','- [바이너리·코드 해시](provenance.json), [코드 변경](runtime.patch)','- [측정](record.py), [후보 반복](repeat.py), [수집](collect.py), [분석](analyze.py), [한글 이미지](make_images.py)','- [녹화](capture.py), [영상 검증](video-validation.json), [녹화 입력·시각](capture-manifest.json)','',
'```sh','PLATFORM=android MODE=audit BLOCK_MS=160 OUT=/private/tmp/budget-new-audit python3 -I docs/benchmarks/2026-09-05-budget/record.py','PLATFORM=ios MODE=perf BLOCK_MS=0 REPEATS=3 CONFIGS=flatlist-5,zigpool-5 OUT=/private/tmp/budget-new-perf python3 -I docs/benchmarks/2026-09-05-budget/record.py','```','',
'이 자료는 RN 0.85.0 바이너리의 결과다. 재현하려면 provenance의 기반 커밋과 runtime.patch를 적용한 별도 체크아웃에서 RN 0.85.0 앱을 빌드한다. 최신 RN 앱으로 이 스크립트만 실행한 결과를 합산하면 안 된다. 항상 새 출력 경로를 사용한다. Android는 세로 1080×2400이 필요하며 설정을 자동 변경하지 않는다. [측정 방법](methodology-ko.md)에 조건과 지표의 한계를 상세히 적었다.','']
for p in sorted(D.glob('*-raw.zip')):lines.append(f'- [{p.name}]({p.name})')
(D/'README.md').write_text('\n'.join(lines)+'\n')
