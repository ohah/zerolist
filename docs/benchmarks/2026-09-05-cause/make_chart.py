"""한글 원인 분석 요약 그림. 측정값은 JSON에서 읽는다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,statistics
P=Path(__file__).resolve().parent
im=Image.new('RGB',(1500,1080),'#101827');d=ImageDraw.Draw(im);font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def text(x,y,s,size=30,color='#e7edf7'):d.text((x,y),s,font=ImageFont.truetype(font,size),fill=color)
text(40,25,'지연의 원인 · 내용 반영과 그래픽 완료를 분리',43)
text(40,90,'Android 에뮬레이터 / 같은 APK / 알고리즘 변경 없이 조건 비교',27,'#aebed5')
text(40,150,'내용 반영 · 강제 지연 없음 · 3회, 63개 요청',34,'#70dbc6')
b=json.loads((P/'binding-summary.json').read_text())
rows=[('요청 → JS 수신','request->receive'),('React 처리 구간','render->react_layout'),('React 이후 → 네이티브 반영','react_layout->native_commit'),('요청 → 그리기 전 배치 전체','request->placed')]
for n,(label,key) in enumerate(rows):
 y=215+n*65;d.rectangle((30,y-8,1470,y+48),fill='#1d2b42' if n%2==0 else '#101827')
 text(45,y,label);text(790,y,f"중앙값 {b[key]['p50']}밀리초");text(1120,y,f"p95 {b[key]['p95']}밀리초")
text(40,500,'그래픽 조건 · ZigPool 코드와 행 내용은 동일',34,'#70dbc6')
rr=json.loads((P/'renderer-confirm-results.json').read_text());gg=json.loads((P/'gfx-confirm-results.json').read_text())
entries=[('OpenGL / 상세 추적 끔',[r for r in rr if r['renderer']=='skiagl']),('Vulkan / 상세 추적 끔',[r for r in rr if r['renderer']=='skiavk']),('OpenGL / 그래픽 추적 켬',[r for r in gg if r['probe']=='gfx'])]
for n,(label,rows) in enumerate(entries):
 y=570+n*70;d.rectangle((30,y-8,1470,y+53),fill='#1d2b42' if n%2==0 else '#101827')
 text(45,y,label);text(790,y,f"지연률 {statistics.median(r['jank_percent'] for r in rows):.2f}%");text(1120,y,f"p95 {statistics.median(r['p95_ms'] for r in rows):.0f}밀리초")
text(40,830,'그래픽 추적은 GPU 완료 신호를 감시하는 스레드도 추가합니다.',28)
text(40,880,'0%는 제품 최적화 성과가 아닙니다. 이 조건의 결과로 일반 성능 순위를 매기지 않습니다.',26,'#f0bf82')
text(40,945,'내용 반영의 끝은 실제 화면 표시 완료가 아닙니다. 실물 기기·iOS의 같은 원인은 미확인입니다.',24,'#aebed5')
text(40,990,'p95: 시간 상위 5% 경계 / 각 그래픽 조건 3회 중앙값 / 두 표는 서로 다른 측정입니다.',24,'#aebed5')
im.save(P/'cause-summary-ko.png')
