"""네이티브 시작 이후 준비 시간의 한글 비교 이미지."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
D=Path(__file__).resolve().parent;rows=json.loads((D/'summary.json').read_text())
im=Image.new('RGB',(1600,1170),'#101827');d=ImageDraw.Draw(im)
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def text(x,y,s,size=28,color='#edf4fc'):d.text((x,y),s,font=ImageFont.truetype(font,size),fill=color)
text(60,40,'시작 준비 시간도 줄었습니다',48)
text(60,110,'10만 건 · 무거운 셀 · RN 0.87.1 Release · 각 10회 중앙값',28,'#b4c4d8')
for p,y in [('ios',200),('android',570)]:
 old,new=[r for r in rows if r['platform']==p]
 o=old['startup']['both']['median'];n=new['startup']['both']['median']
 text(60,y,'iOS' if p=='ios' else 'Android',36)
 text(710,y,f'{o-n:.1f}ms 단축 ({(o-n)/o*100:.1f}%)',36,'#65e4b1')
 for i,(r,label,color) in enumerate([(old,'기존 UI 워클릿','#52769e'),(new,'메모리 개선 워클릿','#27ac88')]):
  yy=y+75+i*90;v=r['startup']['both']['median'];w=v/1500*760
  text(60,yy+10,label,29);d.rounded_rectangle((390,yy,390+w,yy+55),8,fill=color);text(415+w,yy+10,f'{v:,.1f}ms',29)
 text(60,y+270,f"첫 제목·배치 확인: {old['startup']['content_ready']['median']:,.1f} → {new['startup']['content_ready']['median']:,.1f}ms",29,'#b4c4d8')
 text(60,y+315,f"같은 회차에서 데이터·내용 모두 준비 시간이 짧았던 횟수: {new['paired_faster_runs']} / 10",25,'#b4c4d8')
text(60,990,'막대: 네이티브 시작 진입 → 첫 화면 내용과 UI 데이터 모두 준비',28,'#ffc785')
text(60,1040,'OS 프로세스 생성 이전 구간 제외 · 실제 패널 표시 시각이 아닌 네이티브 관측',26,'#b4c4d8')
text(60,1090,'시뮬레이터·에뮬레이터 / 외부 호스트 부하 미통제 / 실물 구형 기기 미검증',25,'#b4c4d8')
im.save(D/'startup-summary-ko.png')
