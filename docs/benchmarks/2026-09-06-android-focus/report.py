"""최종 Android 원자료에서 표와 실행 범위를 생성한다."""
from pathlib import Path
import json,statistics,sys
D=Path(__file__).resolve().parent;R=Path(sys.argv[1] if len(sys.argv)>1 else '/private/tmp/zerolist-android-focus-final')
labels={'flatlist-5':'FlatList','zerolist-5':'개선 ZeroList','flashlist-5':'FlashList','legend-5':'LegendList','zigpool-5':'ZigPool 비교 어댑터','zerolist-before-5':'ZeroList 수정 전 경로'}
allrows=[];summary=[]
s='''# 1단계: Android 네이티브 배치만 변경한 비교

**React 슬롯 memo를 추가하기 전, 네이티브 배치만 변경한 단계의 기록이다.** API·준비 행 수·상태 보호는 유지한다. 이전 고부하 실행의 CPU 35.13%·지연 5.37%와 현재 결과의 차이를 이번 코드의 개선율로 계산하지 않는다. [변경 내용과 범위](implementation-ko.md) · [원인 해석과 개선 판단](findings-ko.md) · [실제 동작](contract-ko.md).

RN 0.87.1, Android 16 arm64 Release 에뮬레이터, 10만 건, 한쪽 5행 준비 목표, 강제 JS 점유 없음. 그래픽 설정은 skiagl 그대로다. 준비 스와이프 12회 후 18회 스와이프를 측정하고 빌드·녹화·시스템 추적은 별도로 했다. 각 비용 3회, 화면 검사 1회다.

최종 비교는 5개 리스트와 무거운 셀의 수정 전 ZeroList 경로를 포함해 비용 33회·화면 검사 11회, 총 44회다. 아래 수정 전 경로는 **같은 APK에서 이번 두 네이티브 변경만 끈 대조군**이다. 과거 ZeroList 전체 제품이나 오래된 APK와 비교한 것이 아니다.

'''
for cell in ['heavy','simple']:
 perf=json.loads((R/f'{cell}-perf/results.json').read_text());audit=json.loads((R/f'{cell}-audit/results.json').read_text());allrows += [dict(x,cell=cell) for x in perf+audit]
 names=list(labels) if cell=='heavy' else list(labels)[:-1]
 s+='## '+('무거운 셀' if cell=='heavy' else '가벼운 셀')+'\n\n비용 3회 평균(최소~최대), 공백·오류는 별도 1회 화면 검사다.\n\n| 리스트 | CPU % | PSS MiB | 지연 프레임 % | 평균 공백 % | 제목 오류 / 겹침 |\n|---|---:|---:|---:|---:|---:|\n'
 for name in names:
  p=[x for x in perf if x['name']==name];a=next(x for x in audit if x['name']==name);assert len(p)==3
  stats={k:{'mean':statistics.mean(x[k] for x in p),'min':min(x[k] for x in p),'max':max(x[k] for x in p)} for k in ['cpu_one_core_percent','memory_after_mib','late_percent','p95_ms','wall_seconds','cpu_seconds']}
  work={k:statistics.mean(x['work'][k] for x in p) for k in ['renders','mounts','unmounts','callbacks']}
  summary.append(dict(cell=cell,name=name,label=labels[name],stats=stats,work=work,audit=a))
  def f(k):
   v=stats[k];return f"{v['mean']:.2f} ({v['min']:.2f}~{v['max']:.2f})"
  s+=f"| {labels[name]} | {f('cpu_one_core_percent')} | {f('memory_after_mib')} | {f('late_percent')} | {a['mean_blank_area_percent']:.3f} | {a['wrong_frames']} / {a['overlap_frames']} |\n"
 s+='\n'
s+='''## 내용 준비와 실제 이동량

아래 이동량은 비용 실행과 별도의 화면 검사다. 이 값으로 위 CPU를 정규화하지 않는다. 같은 입력 횟수라도 관성·배치 정책에 따라 실제 이동량은 달라질 수 있다. 평균 공백만으로 순간 공백을 숨기지 않도록 최대와 지속 시간도 보인다. 2픽셀 이하는 허용 오차로 처리한다.

| 셀 / 리스트 | 이동 행 수 | 진입 내용 준비 % | 최대 공백 % | 최장 공백 ms | 부착 행 최대 |
|---|---:|---:|---:|---:|---:|
'''
for x in summary:
 a=x['audit'];s+=f"| {'무거움' if x['cell']=='heavy' else '가벼움'} / {x['label']} | {a['travel_rows']:.1f} | {a['entry_ready_percent']:.2f} | {a['max_blank_area_percent']:.2f} | {a['blank_episode_max_ms']:.2f} | {a['attached_max']:.0f} |\n"
s+='\n## 무거운 셀의 React 작업량\n\n준비 이후 측정 구간의 평균이다. 슬롯 내부 항목 key 보호를 유지했으므로 통합 ZeroList는 다른 항목으로 바뀔 때 생성·제거가 발생한다.\n\n| 리스트 | 렌더 | 마운트 | 언마운트 |\n|---|---:|---:|---:|\n'
for x in summary:
 if x['cell']=='heavy':
  w=x['work'];s+=f"| {x['label']} | {w['renders']:.1f} | {w['mounts']:.1f} | {w['unmounts']:.1f} |\n"
s+='''
## 해석의 한계

CPU는 한 코어 기준 사용량이며 처리 속도 개선율이 아니다. 메모리는 측정 종료 시 PSS이고 시작·준비 중 최대값이나 전력이 아니다. gfxinfo 지연은 에뮬레이터의 그래픽 완료·마감 판정에도 영향을 받으며 실제 기기의 체감과 동일하지 않다. 내용 검사는 네이티브 행의 제목·배치이며 최종 GPU 픽셀을 매 프레임 확인한 검사는 아니다.

실물 저사양 기기와 장시간 동적 데이터 변경 성능은 미검증이다. 기존 ZigPool 비교 어댑터도 최종 네이티브 배치 개선을 받지만 상태 보호·스크롤 콜백·기본 스크롤바가 통합 ZeroList와 다르다. 모든 창·배치 설정을 최적화한 절대 순위가 아니다. 외부 호스트 부하는 기록했지만 완전히 통제하지 못했다.

[실행 행렬](native-stage-matrix.json) · [요약 원본](native-stage-summary.json) · [최종 결과](README.md). 원본 조건·호스트 부하·로그는 그룹별 raw.zip에 보존한다.
'''
assert len(allrows)==44
(D/'native-stage-ko.md').write_text(s);(D/'native-stage-matrix.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2));(D/'native-stage-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print('최종 44회 집계 완료')
