"""이전 비교와 독립 재측정을 나란히 보고하고 구조 설명을 실제 수치와 연결한다."""
from pathlib import Path
import json,statistics
D=Path(__file__).resolve().parent
s=json.loads((D/'summary.json').read_text());p=json.loads((D/'points.json').read_text());m=json.loads((D/'matrix.json').read_text())
old=json.loads((D.parent/'2026-09-05-rn087'/'summary.json').read_text())
labels={'flatlist':'FlatList','flashlist':'FlashList','legend':'LegendList','zerolist':'기존 ZeroList','zigpool':'ZigPool 고정','stable':'ZigPool 범위 유지'}
def name(n):
 a,b=n.rsplit('-',1);return f'{labels[a]} · {b}행'
def median(r,k):return r[k]['median']
def fmt(v,n=1):return f'{v:.{n}f}'
def table(h,rows):return '| '+' | '.join(h)+' |\n|'+'|'.join(['---']*len(h))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def get(os,n,mode='perf',block=0):return next(r for r in s if (r['platform'],r['name'],r['mode'],r['block_ms'])==(os,n,mode,block))
def runs(os,n,mode='audit',block=160):return [r for r in m if (r['platform'],r['name'],r['mode'],r['block_ms'])==(os,n,mode,block)]
def zero(os,n):return sum(r['mean_blank_area_percent']==0 for r in runs(os,n))
assert len(m)==117,len(m)
assert all(r.get('wrong_frames',0)==0 and r.get('overlap_frames',0)==0 for r in m), '내용 불일치나 겹침을 조사해야 함'
f=get('android','flatlist-5');z=get('android','zigpool-5');reduction=100*(1-median(z,'cpu_one_core_percent')/median(f,'cpu_one_core_percent'))
sp=next(r for r in p if r['platform']=='ios' and r['name']=='stable-12');fp=next(r for r in p if r['platform']=='ios' and r['name']=='flashlist-12')
summary=f'''## 이번 재측정에서 확인한 우위와 한계

- Android 일반 스크롤에서 ZigPool/FlatList의 종료 메모리는 **{median(z,'memory_after_mib'):.1f}/{median(f,'memory_after_mib'):.1f}MiB**, CPU는 **{median(z,'cpu_one_core_percent'):.1f}/{median(f,'cpu_one_core_percent'):.1f}%**였다. ZigPool의 CPU가 **{reduction:.1f}% 낮았다**. 같은 입력의 앱 프로세스 비용이며 화면이 그만큼 빨라졌다는 뜻은 아니다.
- 같은 두 설정의 p95 중앙값은 **{median(z,'p95_ms'):.0f}/{median(f,'p95_ms'):.0f}ms**였다. 다른 리스트까지 포함한 프레임 시간 범위는 아래에서 확인한다. CPU 우위를 프레임 속도 전체 순위로 바꾸지 않는다.
- iOS 부하에서 범위 유지 12행/FlashList 12행의 종료 RSS는 **{sp['memory_mib']:.1f}/{fp['memory_mib']:.1f}MiB**였다. 범위 유지 설정의 차이는 **{sp['memory_mib']-fp['memory_mib']:+.1f}MiB**다. 공백 없는 실행은 각각 **{zero('ios','stable-12')}/3, {zero('ios','flashlist-12')}/3회**다.
- 순간 최대 공백 면적은 두 iOS 설정에서 **{sp['worst_blank_area_percent']:.1f}/{fp['worst_blank_area_percent']:.1f}%**, 검사상 최대 공백 지속 시간은 **{sp['blank_episode_max_ms']:.1f}/{fp['blank_episode_max_ms']:.1f}ms**였다. 면적 %는 시간 비율이 아니다.

'''
zi=get('ios','zigpool-5');fi=get('ios','flatlist-5')
summary+=f"- 같은 5행 iOS 일반 조건에서 ZigPool/FlatList CPU는 **{median(zi,'cpu_one_core_percent'):.1f}/{median(fi,'cpu_one_core_percent'):.1f}%**, 종료 RSS는 **{median(zi,'memory_after_mib'):.1f}/{median(fi,'memory_after_mib'):.1f}MiB**였다. 반면 JS 부하의 평균 공백은 **{median(get('ios','zigpool-5','audit',160),'mean_blank_area_percent'):.2f}/{median(get('ios','flatlist-5','audit',160),'mean_blank_area_percent'):.2f}%**로 ZigPool이 더 나빴다.\n"
summary+=f"- Android 일반 조건의 지연 프레임 비율도 ZigPool/FlatList **{median(z,'late_percent'):.2f}/{median(f,'late_percent'):.2f}%**로 ZigPool이 소폭 높았다. p95 한 지표만으로 모든 끊김이 줄었다고 평가하지 않는다.\n\n"
lines=['# RN 0.87.1 독립 재비교 — 같은 5행 조건 포함\n',f'지난 99회와 같은 RN 0.87.1 바이너리로 **{len(m)}회**를 추가 측정했다. Android 6개·iOS 7개 설정에 대해 일반 비용, JS 부하 공백, JS 부하 비용을 각각 3회 실행했다. 이전 결과와 합쳐 평균을 내지 않고 나란히 표시한다.\n',summary,'[어디서 앞서며 어떤 접근을 했는가](approach-ko.md)\n','## 조건\n','고정 높이의 무거운 RN 셀 10만 건, 준비 스와이프 12회, 측정 스와이프 18회. JS 부하는 160ms 점유/40ms 여유 반복이다. Android API 36 에뮬레이터와 iOS 26.2 시뮬레이터에서 Release/Fabric/Hermes로 실행했다. 정량 구간에서는 빌드·녹화를 하지 않았고 다른 플랫폼의 앱은 종료했다. 실행 순서를 고정 seed로 섞었다.\n','모든 리스트의 5행 준비 조건을 포함했다. **같은 5행 설정이 같은 메모리 사용량을 보장하는 것은 아니다.** 기존 선택 설정인 Android FlashList 2행, iOS FlashList 12행·ZigPool 범위 유지 12행도 유지했다. FlashList 2.3.1·LegendList 2.0.19이며 라이브러리 자체나 앱 런타임 코드는 바꾸지 않았다.\n','[기존 측정 방법](../2026-09-05-budget/methodology-ko.md) · [바이너리 해시](provenance.json) · [실행 스크립트](run_matrix.py)\n','![일반 비용](normal-cost-ko.png)\n']
for os in ['android','ios']:
 lines += [f"## {'Android' if os=='android' else 'iOS'} 일반 스크롤\n"]
 rs=[]
 for r in s:
  if (r['platform'],r['mode'],r['block_ms'])!=(os,'perf',0):continue
  k='p95_ms' if os=='android' else 'callback_p95_ms';a=r[k]
  rs.append([name(r['name']),fmt(median(r,'memory_after_mib')),fmt(median(r,'cpu_one_core_percent')),fmt(a['median'],2),f"{a['min']:.2f}–{a['max']:.2f}"])
 lines += [table(['설정','메모리 MiB','CPU %','p95 ms','p95 반복 범위'],rs),'\n',f"## {'Android' if os=='android' else 'iOS'} JS 부하\n",f'![메모리와 공백]({os}-budget-ko.png)\n']
 rs=[]
 for r in p:
  if r['platform']!=os:continue
  rs.append([name(r['name']),fmt(r['memory_mib']),f"{zero(os,r['name'])}/3",fmt(r['blank_area_percent'],3),fmt(r['worst_blank_area_percent']),fmt(r['blank_episode_max_ms']),fmt(r['cpu_percent']),fmt(r['frame_p95_ms'],2)])
 lines += [table(['설정','메모리 MiB','공백 없는 실행','평균 공백 %','최대 공백 %','최대 지속 ms','CPU %','p95 ms'],rs),'\n']
lines += ['## 지난 RN 0.87.1 비교와 달라진 정도\n']
rs=[]
for r in s:
 if r['mode']!='perf' or r['block_ms']!=0:continue
 a=next((x for x in old if all(x[k]==r[k] for k in ['platform','name','mode','block_ms'])),None)
 if not a:continue
 k='p95_ms' if r['platform']=='android' else 'callback_p95_ms'
 rs.append([r['platform']+' · '+name(r['name']),f"{median(a,'cpu_one_core_percent'):.1f} → {median(r,'cpu_one_core_percent'):.1f}",f"{median(a,k):.2f} → {median(r,k):.2f}"])
lines += [table(['같은 설정','CPU %: 이전 → 이번','p95 ms: 이전 → 이번'],rs),'\n']
rs=[]
for r in s:
 if r['mode']!='audit':continue
 a=next((x for x in old if all(x[k]==r[k] for k in ['platform','name','mode','block_ms'])),None)
 if a:rs.append([r['platform']+' · '+name(r['name']),f"{median(a,'mean_blank_area_percent'):.3f} → {median(r,'mean_blank_area_percent'):.3f}",f"{a['max_blank_area_percent']['max']:.1f} → {r['max_blank_area_percent']['max']:.1f}"])
lines += [table(['같은 설정','평균 공백 %: 이전 → 이번','최대 공백 %: 이전 → 이번'],rs),'\n','## 지표의 뜻과 한계\n','- 메모리는 종료 시점 PSS(Android)/RSS(iOS)이며 피크나 메모리 상한이 아니다. CPU는 앱 프로세스 전체를 1코어 기준으로 표시하며 부하 조건에는 인위적인 JS 점유도 포함한다.\n- 평균 공백은 이동 중 검사 프레임의 빈 면적 평균을 실행별로 계산한 뒤 취한 중앙값이다. 최대 공백은 반복 전체의 최댓값이다. 2px/포인트 오차를 허용한다.\n- 최대 지속 시간은 첫 공백 관측부터 첫 해소 관측까지의 검사 시각 차이다. 정지 구간도 포함하며 실제 화면 표시 시각을 직접 측정한 값은 아니다. 마지막까지 공백이 남은 경우 하한이며 `blank_tail_open`에 기록한다.\n- iOS p95는 CADisplayLink 콜백 간격이다. 실제 표시 프레임의 끊김과 같지 않다. Android 지표와 직접 비교하지 않는다.\n- 같은 제스처여도 관성과 스케줄링에 따라 이동 거리가 다르다. 카운트를 전체 처리 속도로 환산하지 않는다. 실물 저사양 기기·동적 높이·배터리·발열은 미검증이다.\n',f"- 공통 검사 {sum(r['mode']=='audit' for r in m)}회에서 내용 불일치와 겹침은 0이었다. 모든 설정이 무공백이었다는 의미는 아니다.\n",'## 원자료\n','[행렬](matrix.json) · [집계](summary.json) · [한글 CSV](comparison-ko.csv) · [코드와 원인 설명](approach-ko.md)\n']
lines += [f'- [{q.name}]({q.name})' for q in sorted(D.glob('*-raw.zip'))]
(D/'README.md').write_text('\n'.join(lines))
work=[]
for os in ['android','ios']:
 for n in dict.fromkeys(x['name'] for x in m if x['platform']==os):
  a=runs(os,n,'perf',0)
  if not a:continue
  work.append([os+' · '+name(n),fmt(statistics.median(x['cpu_one_core_percent'] for x in a)),*[fmt(statistics.median(x['work'][k] for x in a),0) for k in ['callbacks','renders','mounts','unmounts']]])
insert=summary+'## 구조를 확인하는 보조 계측\n\n'+table(['일반 스크롤 설정','CPU %','계측 콜백','Cell 렌더','Cell 생성','Cell 제거'],work)+'\n동일한 18회 입력 후 3회 중앙값이다. 콜백 종류와 로그 경계의 한계는 아래에 설명한다.\n'
(D/'approach-ko.md').write_text((D/'approach-template.md').read_text().replace('<!-- RESULTS -->',insert))
