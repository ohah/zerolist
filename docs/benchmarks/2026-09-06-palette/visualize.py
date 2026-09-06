"""두 플랫폼의 8종 비교를 한글 표 이미지로 생성한다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
D=Path(__file__).resolve().parent;rs=json.loads((D/'summary.json').read_text())
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
for platform,title in [('ios','iOS'),('android','Android')]:
 im=Image.new('RGB',(1800,1260),'#101827');d=ImageDraw.Draw(im)
 def text(x,y,s,size=28,color='#edf4fc'):d.text((x,y),s,font=ImageFont.truetype(font,size),fill=color)
 text(60,40,title+' · 8종 리스트 전체 재측정',48)
 text(60,115,'10만 건 · 무거운 셀 · RN 0.87.1 · 같은 바이너리 · 각 조건 3회',29,'#b4c4d8')
 xs=[60,430,630,835,1045,1245,1495]
 headers=['엔진','시작 ms','메모리 MiB','CPU %','지연 %','점유 시 공백 %','점유 시 지연 %']
 for x,h in zip(xs,headers):text(x,210,h,26,'#b4c4d8')
 for i,r in enumerate(x for x in rs if x['platform']==platform):
  y=275+i*89
  d.rounded_rectangle((40,y-10,1760,y+65),10,fill='#203547' if r['engine']=='template-palette' else '#182638')
  values=[r['label'],f"{r['startup_ms']['median']:.1f}",f"{r['perf0']['memory']['mean']:.1f}",f"{r['perf0']['cpu']['mean']:.1f}",f"{r['perf0']['late']['mean']:.2f}",f"{r['audit']['blank']['mean']:.3f}",f"{r['perf160']['late']['mean']:.2f}"]
  for x,v in zip(xs,values):text(x,y,v,27)
 text(60,1020,'시작: 네이티브 진입 → 첫 제목·배치 확인, 중앙값 / 나머지: 각 3회 평균',27,'#b4c4d8')
 text(60,1070,'점유: JS 160ms 작업 + 40ms 여유 / 공백과 지연은 별도 실행·서로 다른 지표',27,'#b4c4d8')
 text(60,1120,('메모리 RSS · 지연 CADisplayLink 콜백' if platform=='ios' else '메모리 PSS · 지연 gfxinfo 프레임')+' / 준비 목표 5행, 실제 뷰 수는 다름',26,'#ffc785')
 text(60,1170,'외부 호스트 부하 미통제 · 실물 구형 기기 미검증 · 워클릿은 고정 템플릿 PoC',26,'#b4c4d8')
 if platform=='android':text(60,1215,'별도 추가 지연 검사: 후보 한 실행 21.23% · 위 정식 평균에 합치지 않고 원본 보존',23,'#ffc785')
 im.save(D/f'{platform}-summary-ko.png')
