"""실기기 반복 비용 측정과 별도 화면 검사를 합쳐 한국어 비교표를 만든다."""
from pathlib import Path
import json,statistics,os
D=Path(__file__).resolve().parent
P=Path(os.getenv('PERF','/private/tmp/zerolist-physical-heavy-perf'))
A=Path(os.getenv('AUDIT','/private/tmp/zerolist-physical-heavy-audit'))
rows=json.loads((P/'results.json').read_text());audits=json.loads((A/'results.json').read_text())
labels={'flatlist-5':'FlatList','zerolist-5':'현재 ZeroList','zerolist-before-5':'최적화 이전 경로','flashlist-5':'FlashList','legend-5':'LegendList','zigpool-5':'기존 ZigPool'}
summary=[]
for name,label in labels.items():
 group=[x for x in rows if x['name']==name];assert sorted(x['run'] for x in group)==[1,2,3]
 a=[x for x in audits if x['name']==name];assert len(a)==1
 stats={k:{'mean':statistics.mean(x[k] for x in group),'min':min(x[k] for x in group),'max':max(x[k] for x in group)} for k in ['cpu_one_core_percent','cpu_seconds','memory_after_mib','late_percent','p95_ms']}
 summary.append({'name':name,'label':label,'n':len(group),'stats':stats,'late':sum(x['late'] for x in group),'frames':sum(x['frames'] for x in group),'weighted_late_percent':100*sum(x['late'] for x in group)/sum(x['frames'] for x in group),'audit':a[0]})
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
out=['# 실기기 비교 결과','', 'SM-S731N · Android 16 · RN 0.87.1 · 60Hz · Skia Vulkan · 무거운 행 100,000개','', '비용은 각 3회 평균이며 괄호는 최솟값–최댓값이다. CPU는 앱 전체 스레드 합계를 한 코어 기준으로 환산한 사용률, 메모리는 실행 종료 PSS이다. 지연은 3회 전체 프레임에서 마감을 놓친 비율이다.','', '| 경로 | CPU % | 종료 PSS MiB | 지연 프레임 % | 지연 / 전체 |','|---|---:|---:|---:|---:|']
for x in summary:
 c=x['stats']['cpu_one_core_percent'];m=x['stats']['memory_after_mib'];out.append(f"| {x['label']} | {c['mean']:.2f} ({c['min']:.2f}–{c['max']:.2f}) | {m['mean']:.2f} ({m['min']:.2f}–{m['max']:.2f}) | {x['weighted_late_percent']:.2f} | {x['late']} / {x['frames']} |")
out+=['','## 별도 화면 검사','', '내용 검사와 준비 추적을 켠 각 1회다. 위 비용 측정과 합산하지 않는다. 같은 스와이프라도 엔진의 스크롤 처리에 따라 이동량과 내용 갱신량이 달라질 수 있다.','', '| 경로 | 잘못된 내용 프레임 | 겹침 프레임 | 이동 중 빈 화면 % | 진입 준비율 % | 이동 행 수 |','|---|---:|---:|---:|---:|---:|']
for x in summary:
 a=x['audit'];out.append(f"| {x['label']} | {a['wrong_frames']} | {a['overlap_frames']} | {a['blank_moving_percent']:.2f} | {a['entry_ready_percent']:.2f} | {a['travel_rows']:.1f} |")
(D/'comparison-ko.md').write_text('\n'.join(out)+'\n')
print('\n'.join(out))
