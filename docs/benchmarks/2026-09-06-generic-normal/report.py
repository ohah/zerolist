"""정상 부하의 비용 60회와 별도 화면 검사 20회만 재집계한다."""
from pathlib import Path
import json,statistics,zipfile,sys
D=Path(__file__).resolve().parent;R=Path(sys.argv[1]);matrix=[];summary=[]
labels={'flatlist':'FlatList','zerolist':'ZeroList','flashlist':'FlashList','legend':'LegendList','zigpool':'기존 ZigPool'}
def stats(v):return dict(n=len(v),mean=statistics.mean(v),median=statistics.median(v),min=min(v),max=max(v))
for platform in ['android','ios']:
 for cell in ['simple','heavy']:
  groups={}
  for mode,n in [('audit',5),('perf',15)]:
   p=R/f'{platform}-{cell}-{mode}';rs=json.loads((p/'results.json').read_text());assert len(rs)==n
   groups[mode]=rs
   matrix.extend(dict(r,platform=platform,cell=cell) for r in rs)
   with zipfile.ZipFile(D/f'{p.name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in p.iterdir():
     if f.is_file():z.write(f,f.name)
  for engine,label in labels.items():
   perf=[r for r in groups['perf'] if r['engine']==engine];audit=[r for r in groups['audit'] if r['engine']==engine];assert len(perf)==3 and len(audit)==1
   late='late_percent' if platform=='android' else 'late_callback_percent'
   row=dict(platform=platform,cell=cell,engine=engine,label=label,memory=stats([r['memory_after_mib'] for r in perf]),cpu=stats([r['cpu_one_core_percent'] for r in perf]),late=stats([r[late] for r in perf]),work={k:stats([r['work'][k] for r in perf]) for k in ['renders','callbacks','mounts','unmounts']},audit=audit[0])
   summary.append(row)
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(D/'matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2))
lines=['# 일반 React 셀 5종 정상 부하 비교','',
'**정상 부하에서 simple/heavy를 나눠 같은 새 바이너리로 비교했다.** 비용 각 3회 총 60회, 별도 실제 제목·행 배치 검사 각 1회 총 20회다. 강제 JS 점유는 없다. 동적 변경의 기기 성능 시험이나 수정 전후 동일 앱 비교는 아니다.','',
'RN 0.87.1 arm64 Release, 10만 건, 화면 밖 한쪽 5행 목표. 임의의 특별 텍스트·장식 뷰를 요구하지 않는 공통 React 셀을 사용한다. FlatList에는 getItemLayout·초기 화면 행 수를 주고, FlashList·LegendList도 같은 높이 힌트를 사용한다. [범위와 구현 검증](implementation-ko.md) · [판단과 후속 기준](findings-ko.md).','']
for platform in ['android','ios']:
 for cell in ['simple','heavy']:
  title=('Android' if platform=='android' else 'iOS')+' / '+('가벼운 셀' if cell=='simple' else '무거운 셀')
  lines += ['## '+title,'','비용은 3회 평균이며 괄호는 실행별 범위다. 공백은 별도 1회 화면 검사다.','',
   '| 리스트 | 메모리 MiB | CPU % | 지연 % | 공백 % | 제목 오류 / 겹침 프레임 |','|---|---:|---:|---:|---:|---:|']
  for r in summary:
   if r['platform']!=platform or r['cell']!=cell:continue
   a=r['audit'];vals=[f"{r[k]['mean']:.2f} ({r[k]['min']:.2f}~{r[k]['max']:.2f})" for k in ['memory','cpu','late']]
   lines.append(f"| {r['label']} | {' | '.join(vals)} | {a['mean_blank_area_percent']:.3f} | {a['wrong_frames']} / {a['overlap_frames']} |")
  lines+=['']
lines += ['## 공백이 관측된 화면 검사','','각 조합 1회다. 평균은 이동 중 프레임의 공백 면적이며, 순간 최대와 공백 구간도 함께 확인한다. 2픽셀 이하는 허용 오차로 처리한다. 기기 뷰의 제목·배치 검사이며 최종 GPU 픽셀을 매 프레임 검사한 결과는 아니다.','','| 환경 | 리스트 | 평균 공백 % | 순간 최대 공백 % | 가장 긴 공백 구간 ms |','|---|---|---:|---:|---:|']
for r in summary:
 a=r['audit']
 if a['mean_blank_area_percent']>0:
  lines.append(f"| {r['platform']} / {'가벼운 셀' if r['cell']=='simple' else '무거운 셀'} | {r['label']} | {a['mean_blank_area_percent']:.3f} | {a['max_blank_area_percent']:.2f} | {a['blank_episode_max_ms']:.2f} |")
lines+=['']
lines += ['## 측정 구간의 셀 작업량','','아래 값도 비용 실행 3회 평균이다. 초기 생성은 제외한 준비 이후 증분이며, 0 mount는 앱 전체에서 생성 비용이 없다는 뜻이 아니다. 리스트별 이동량·준비 정책이 달라 작업량만으로 효율을 확정하지 않는다.','','| 환경 | 리스트 | 렌더 | 마운트 | 언마운트 |','|---|---|---:|---:|---:|']
for r in summary:
 if r['cell']=='heavy':
  lines.append(f"| {r['platform']} 무거운 셀 | {r['label']} | {r['work']['renders']['mean']:.1f} | {r['work']['mounts']['mean']:.1f} | {r['work']['unmounts']['mean']:.1f} |")
lines+=['']
lines += ['## 해석','','Android는 PSS·gfxinfo 프레임, iOS는 RSS·CADisplayLink 콜백을 사용한다. OS끼리 같은 지연 지표로 비교하지 않는다. CPU는 한 코어 기준 평균 사용률이며 처리 속도가 아니다. 실제 이동 거리와 측정 창도 확인해야 한다.','',
'같은 데이터·순서 섞기·준비 스와이프 12회·측정 스와이프 18회를 사용하고, 측정 중 빌드·녹화를 하지 않았다. 준비 중 최대 메모리와 시작 비용은 이 표에 없다. 외부 호스트 부하를 통제하지 못했고, 창 크기·배치 정책 전체를 최적화한 순위도 아니다.','',
'동적 높이·키·상태 변경은 별도 React 테스트에서 확인했다. 이 표는 고정 높이 스크롤이며 데이터 변경 중 실제 기기 성능을 확인한 것으로 확대 해석하지 않는다. 각 공백 검사는 1회이므로 장시간 무공백 보장도 아니다.','',
'한글 비교 이미지: [Android](android-normal-ko.png) · [iOS](ios-normal-ko.png).','','원본 조건·호스트 부하·로그는 각 raw.zip, 실행별 수치는 [행렬](matrix.json)에 보존했다. 느린 실행도 포함했다.']
(D/'README.md').write_text('\n'.join(lines)+'\n');print('비용 60회·화면 검사 20회 집계 완료')
