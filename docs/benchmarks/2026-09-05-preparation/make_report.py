# -*- coding: utf-8 -*-
"""수집한 원자료에서 한글 표와 그래프를 만든다."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
s=json.loads((D/'summary.json').read_text())
names={'baseline':'기본 5행','wide':'고정 12행','adaptive-small':'작은 풀 예측','adaptive':'큰 풀 예측','coalesce':'요청 병합','memo':'슬롯 메모화','combined':'예측·병합·메모','adaptive-stable':'범위 유지 예측','combined-stable':'범위 유지·병합·메모'}
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def image(name,title,headers,rows,notes,width=1660):
 height=190+len(rows)*62+len(notes)*36+35
 im=Image.new('RGB',(width,height),'#f5f7fb');draw=ImageDraw.Draw(im)
 def text(x,y,t,size=26,color='#20304a'):draw.text((x,y),str(t),font=ImageFont.truetype(font,size),fill=color)
 text(42,30,title,36)
 columns=[42]+[430+i*((width-470)/(len(headers)-1)) for i in range(len(headers)-1)]
 for x,h in zip(columns,headers):text(x,105,h,25,'#53677e')
 for i,row in enumerate(rows):
  y=158+i*62
  draw.rounded_rectangle((25,y-6,width-25,y+49),8,fill='#e0f1eb' if row[0] in [names['wide'],names['adaptive-stable']] else 'white')
  for x,v in zip(columns,row):text(x,y,v,25)
 y=170+len(rows)*62
 for note in notes:text(42,y,note,23,'#53677e');y+=36
 im.save(D/name)
rows=[]
for v,n in names.items():
 a=s['android'][v];i=s['ios'][v]
 rows.append([n,f"{a['400']['ready_percent']:.1f}%",f"{i['400']['ready_percent']:.1f}%",f"{a['0']['ready_p50_ms']:.1f}ms",f"{i['0']['ready_p50_ms']:.1f}ms"])
image('preparation-ready-ko.png','9개 PoC: 준비 시간 단축과 화면 진입 준비율은 다르다',['방식','안드로이드 준비율','iOS 준비율','안드로이드 준비 시간','iOS 준비 시간'],rows,['준비율: 400ms 강제 반영 지연에서 새로 진입한 행 중 준비된 비율. 각 조건 1회 검사.','준비 시간: 강제 지연 없는 조건의 요청→네이티브 배치 중앙값. 실제 화면 표시 시각이 아님.','정상 조건에서는 양쪽 9개 방식 모두 화면 진입 준비율 100%. OS 사이 수치를 직접 비교하지 않음.'])
for platform in ['android','ios']:
 rows=[]
 for v,n in names.items():
  p=s[platform][v]['perf'];late=p['late_percent' if platform=='android' else 'late_callback_percent'];time=p['p95_ms' if platform=='android' else 'callback_p95_ms'];mem=p['memory_after_mib']
  rows.append([n,f"{late['median']:.2f}%",f"{time['median']:.1f}ms",f"{mem['median']:.1f}MiB",f"{mem['min']:.1f}~{mem['max']:.1f}"])
 image(platform+'-cost-ko.png',('안드로이드' if platform=='android' else 'iOS')+' 비용 비교: 강제 지연 없이 각 3회',['방식','지연 프레임' if platform=='android' else '늦은 화면 콜백','프레임 p95' if platform=='android' else '콜백 간격 p95','종료 PSS' if platform=='android' else '종료 RSS','메모리 3회 범위'],rows,['복잡한 고정 높이 행 10만 건, 준비 이동 12회 뒤 정상·고속·역방향 혼합 스와이프 18회.','감사·준비 로그와 녹화는 끈 별도 측정. 메모리는 시작/종료 표본이며 최대 사용량이 아님.',('iOS는 화면 갱신 콜백 간격의 참고값이다. 실제 표시 지연률 또는 Android 지연률과 같지 않다.' if platform=='ios' else '표는 3회 중앙값과 메모리 범위. 실물 기기의 최대 메모리·전력·발열을 검증한 값이 아님.')])
rows=[]
for v in ['baseline','wide','adaptive-stable','coalesce']:
 a=s['android'][v]['block'];i=s['ios'][v]['block']
 rows.append([names[v],f"{a['ready_percent']:.1f}%",f"{i['ready_percent']:.1f}%",f"{a['ready_p50_ms']:.1f}ms",f"{i['ready_p50_ms']:.1f}ms"])
image('js-block-ko.png','실제 JS 부하: 200ms 주기 중 약 160ms를 JS 연산으로 점유',['방식','안드로이드 준비율','iOS 준비율','안드로이드 준비 시간','iOS 준비 시간'],rows,['반영 타이머 지연은 0ms. JS 스레드가 실제로 점유되는 별도 스트레스 검사, 각 조건 1회.','준비율과 준비 시간은 별개다. 단일 스트레스 검사가 실물 저사양 기기의 성능을 대신하지 않는다.'])
lines=['# 내용 준비 PoC 9종: 양 플랫폼 비교','','**미리 준비하는 효과는 확인했지만, 내용 반영 대기 자체를 일반적으로 단축했다는 근거는 얻지 못했다.** Android에서는 고정 여유 확대가 단순하고 안정적이었고, iOS에서는 요청 범위를 유지하는 예측이 강제 지연에 더 잘 대응했다. 풀 확대의 메모리 비용이 있어 기본값은 기존 방식으로 유지했다.','','![준비율과 준비 시간](preparation-ready-ko.png)','','## 비교한 구현','','| 이름 | 풀 크기 | 바뀐 부분 |','|---|---:|---|']
explain={'baseline':'앞뒤 여유 5행, 기존 반영 경로','wide':'앞뒤 여유 12행','adaptive-small':'기존 풀에서 속도·반영 시간으로 앞뒤 배분','adaptive':'확대한 풀에서 속도·반영 시간으로 앞뒤 배분','coalesce':'한 요청 반영 중에는 다음 요청을 보류하고 완료 후 최신 범위 요청','memo':'이미 memo인 Cell에 더해 슬롯 래퍼도 memo','combined':'확대한 예측 풀 + 요청 병합 + 슬롯 memo','adaptive-stable':'필요한 여유를 포함하는 요청 범위는 유지','combined-stable':'범위 유지 예측 + 요청 병합 + 슬롯 memo'}
for v,n in names.items():lines.append(f"| {n} (`{v}`) | {28 if v in ['wide','adaptive','combined','adaptive-stable','combined-stable'] else 14} | {explain[v]} |")
lines += ['',
 '풀 크기는 이번 기기·고정 행 높이의 값이다. 코드는 화면 높이/행 높이의 올림에 여유 10개 또는 24개를 더하고, 데이터 길이로 제한한다. React JSX와 Cell '
 '내용은 유지한다. PoC는 예제의 선택 옵션이며 제품 목록 API로 완성한 기능이 아니다.',
 '',
 '예측은 네이티브 스크롤 위치 차이/시간의 이동 평균과 완료된 최근 32개 요청의 p95를 사용한다. 시간 예산은 34~500ms, 계산식은 `속도 × (시간 예산 × '
 '1.25 + 16ms)`에 2행 여유를 더한 값이다. 반대 방향에 최소 3행을 남기고 풀 용량으로 제한한다. 속도 추정은 플랫폼 콜백 주기의 영향을 받으므로 이번 구현의 '
 '결과를 모든 예측 알고리즘의 한계로 확대하지 않는다.',
 '',
 '범위 유지 변형은 **이미 요청한 범위**가 필요한 선행/후행 여유를 포함하면 그 범위를 유지한다. 아직 반영되지 않은 요청까지 완료됐다고 간주하는 것은 아니다. 완료된 '
 '내용과 행 번호 매핑은 같은 React 커밋으로 전달하며, 네이티브에서는 배치 후 버전을 확인한다.',
 '',
 '## 준비 완료율과 반영 시간',
 '',
 '화면 진입 준비율은 관측 프레임에서 새로 가시 영역에 들어온 행 중 실제 내용과 위치가 맞게 준비된 행의 비율이다. 빈 공간의 면적이나 지속 시간과는 다른 지표다. '
 '`blank_moving_frames`는 위치가 바뀐 관측 프레임에서 2px를 넘는 빈 공간이 있던 횟수다. 반올림 1px 공백은 허용한다.',
 '',
 '| 방식 | Android 120ms | Android 400ms | iOS 120ms | iOS 400ms |',
 '|---|---:|---:|---:|---:|']
for v,n in names.items():lines.append('| '+n+' | '+' | '.join(f"{s[p][v][str(delay)]['ready_percent']:.1f}%" for p,delay in [('android',120),('android',400),('ios',120),('ios',400)])+' |')
lines += ['',
 '각 준비 검사 조건은 1회 탐색이다. 정상 0ms 조건은 양쪽 9개 방식 모두 준비율 100%, 실제 행 불일치와 겹침은 모든 감사 조건에서 0회다. 숫자 차이를 통계적으로 '
 '확정한 보편적 순위로 읽지 않는다.',
 '',
 '준비 시간은 요청부터 Android의 그리기 전 배치 또는 iOS의 하위 뷰 반영 후 배치까지다. 실제 화면 표시 완료 시간이 아니다. 같은 실행 안에서 요청 버전과 완료 '
 '버전을 연결한다. 반영되지 않은 버전은 지연 분포에서 제외되며, 병합 때문에 아직 보내지 않은 요청의 대기는 포함하지 않는다. 따라서 완료된 요청의 p50이 낮아졌다는 '
 '이유만으로 내용 전체의 지연이 줄었다고 판단하지 않는다.',
 '',
 '## 지연 프레임과 메모리',
 '',
 '![Android 비용](android-cost-ko.png)',
 '',
 '![iOS 비용](ios-cost-ko.png)',
 '',
 '같은 최종 바이너리에서 9개 방식의 순서를 회전해 각 3회 비교했다. 준비/감사 로그와 녹화를 끈 별도 실행이다. Android는 `gfxinfo` 마감 초과 판정, '
 'iOS는 CADisplayLink 시각 간격이 이전 예산의 1.5배를 넘는 비율이다. **iOS 값은 실제 표시 프레임의 지연률이 아니다.**',
 '',
 'Android 메모리는 앱 PSS, iOS는 시뮬레이터 프로세스 RSS의 시작/종료 표본이다. 최대 메모리·전력·발열·실물 저사양 기기를 검증한 것은 아니다. 행을 두 배 '
 '준비할 때의 메모리 부담을 함께 보아야 한다. 초기 마운트 완료 시간도 별도로 측정하지 않았다.',
 '',
 '## 실제 JS 점유 부하',
 '',
 '![JS 점유 부하](js-block-ko.png)',
 '',
 '160ms 동안 `performance.now()`를 확인하며 JS 스레드를 점유하고, 40ms 여유를 둔다. 별도의 반영 지연 타이머는 0ms다. 네 방식, 양 플랫폼에서 '
 '실행하고 실제 점유 로그를 확인했다. 정상 앱 동작을 대표하는 부하가 아니라, JS 스레드가 바쁠 때의 별도 스트레스 조건이다. 부하가 걸린 상태로 준비 이동을 한 뒤 '
 '측정했으므로 갑작스러운 부하 변화에 대한 검증은 아니다.',
 '',
 '## 해석과 채택 판단',
 '',
 '- **고정 여유 확대:** 가장 단순한 유효 대안. Android의 강제 지연 공백을 크게 줄였지만 메모리 비용이 늘었다. 메모리 상한에 맞춘 풀 크기 선택이 필요하다.',
 '- **범위 유지 예측:** iOS에서 고정 확대보다 강제 지연 대응이 좋았다. 단순 예측이 같은 첫 행 안에서 요청 범위를 바꾸며 작업을 늘리는 문제를 줄였다.',
 '- **단순 예측:** 준비율 개선이 있어도 불필요한 범위 이동과 갱신 증폭이 컸다. 현재 형태를 기본값으로 채택하지 않는다.',
 '- **요청 병합:** 요청 수 감소가 준비율 개선으로 이어지지 않았다. 반영 중 다음 요청을 보류하는 대기가 추가된다. 큰 풀과 결합해도 항상 유리하지 않다.',
 '- **슬롯 메모화:** Cell 자체는 이미 memo였으며, 래퍼 최적화만으로 반영 대기를 뚜렷하게 줄이지 못했다.',
 '',
 '전체 결론은 기다리는 시간을 GPU나 Zig가 없앴다는 것이 아니다. 이미 준비한 행을 유지하고 적절한 선행 여유를 확보하는 접근의 효과와 비용을 확인했다. 동적 높이, '
 '이미지 네트워크 다운로드/실제 대형 이미지 디코딩, 데이터 교체, 실물 구형 태블릿까지 검증한 제품 기능은 아니다.',
 '',
 '## 영상',
 '',
 '400ms 강제 지연에서 기본·고정 여유 확대·범위 유지 예측을 각각 별도로 녹화했다. 정량 측정과 분리하며 정상 속도 영상이다. 실행별 스크롤 물리와 입력 전달 시간이 '
 '달라 프레임별 동기 비교는 아니다. iOS 영상에는 세 방식 모두 내용이 비는 구간이 있으며, 정지 후 다시 채워진다. 400ms 강제 지연에서 공백을 완전히 없앤다는 의미가 아니다.',
 '',
 '- [Android 비교](android-compare-400.mp4)',
 '- [iOS 비교](ios-compare-400.mp4)',
 '',
 '## 재현과 원자료',
 '',
 '- [측정 스크립트](record.py), [수집/검증](collect.py), [표·그림 생성](make_report.py)',
 '- [전체 행렬](matrix.json), [요약](summary.json), [바이너리와 코드 해시](provenance.json), [측정 코드 '
 '변경](runtime.patch)',
 '- [영상 녹화](capture.py), [녹화 시각·입력·해시](capture-manifest.json)',
 '',
 '```sh',
 'PLATFORM=android MODE=audit OUT=/private/tmp/preparation-new-audit python3 -I '
 'docs/benchmarks/2026-09-05-preparation/record.py',
 'PLATFORM=ios MODE=perf OUT=/private/tmp/preparation-new-perf python3 -I '
 'docs/benchmarks/2026-09-05-preparation/record.py',
 'BLOCK_MS=160 DELAYS=0 VARIANTS=baseline,wide,adaptive-stable,coalesce '
 'OUT=/private/tmp/preparation-new-block python3 -I '
 'docs/benchmarks/2026-09-05-preparation/record.py',
 '```',
 '',
 '항상 새 OUT 디렉터리를 사용한다. Android는 세로 1080×2400을 검사하며 화면 설정을 자동 변경하지 않는다. 10만 건의 복잡한 고정 높이 행, 준비용 빠른 '
 '스와이프 12회와 관성 중단 터치·2초 대기 후, 정상 3회·고속 6회·역방향 6회·정상 3회를 측정한다. 준비용 이동으로 목록 시작 경계가 큰 풀에 주는 이점을 줄였다. '
 'OS별 입력 좌표와 스크롤 물리가 달라 OS 간 수치를 직접 비교하지 않는다.',
 '',
 '최초 파일럿에서 초기 내용이 같은 경우 완료 확인이 다음 스크롤까지 늦어지는 Android PoC 문제를 발견했다. 버전 반영 시 그리기를 요청해 수정한 후 다시 측정했다. '
 '파일럿은 최종 수치에 합산하지 않는다. A는 완료 확인 수정 후 7개 Android 방식, B는 범위 유지 2개와 기본 대조군 재검사, C는 JS 점유 옵션과 iOS 로그 '
 '전달을 추가한 최종 바이너리다. Android 기본 대조군은 A/B 모두 정상 준비 시간 중앙값 18ms로 재확인했다. 전체 성능 교차 비교와 iOS·JS 점유 검사는 '
 'C다.',
 '',
 '73개 테스트, 린트, 라이브러리 타입 검사, Android arm64 Release와 iOS arm64 시뮬레이터 Release 빌드를 통과했다. 빌드 CI는 추가하지 '
 '않았다.']
for p in sorted(D.glob('*-raw.zip')):lines.append(f'- [{p.name}]({p.name})')
(D/'README.md').write_text('\n'.join(lines)+'\n')
print('한글 보고서와 그래프 생성 완료')
import csv
matrix=json.loads((D/'matrix.json').read_text())
with (D/'comparison-ko.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['플랫폼','방식','강제 반영 지연(ms)','화면 진입 준비율(%)','준비 중앙값(ms)','준비 p95(ms)','요청 수','완료 요청 수','행 렌더 수','이동 중 빈 공간 프레임','내용 불일치 프레임','겹침 프레임'])
 for platform,values in matrix.items():
  for r in values['audit']:w.writerow(['안드로이드' if platform=='android' else 'iOS',names[r['variant']],r['delay_ms'],r['entry_ready_percent'],r['ready_p50_ms'],r['ready_p95_ms'],r['requests'],r['completed'],r['renders_during'],r['blank_moving_frames'],r['wrong_frames'],r['overlap_frames']])
p=D/'README.md';p.write_text(p.read_text().replace('- [전체 행렬]', '- [한글 CSV](comparison-ko.csv)\n- [전체 행렬]'))
