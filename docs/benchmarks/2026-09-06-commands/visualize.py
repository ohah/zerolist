"""3개 갱신 경로의 평균과 JS 점유 지연 10회 전체를 한글로 표시한다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
D=Path(__file__).resolve().parent;summary=json.loads((D/'summary.json').read_text())
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
colors=['#b8c5d7','#ffbf69','#66d9c0']
for platform in ['ios','android']:
 rs=[r for r in summary if r['platform']==platform]
 im=Image.new('RGB',(1600,1260),'#101827');d=ImageDraw.Draw(im)
 def text(x,y,s,n=27,color='#edf4fc'):d.text((x,y),s,font=ImageFont.truetype(font,n),fill=color)
 title='iOS' if platform=='ios' else 'Android'
 text(45,30,title+' · 속성 갱신과 네이티브 명령 비교',43)
 text(45,95,'10만 건 · 같은 14행 풀 · RN 0.87.1 · 같은 새 Release 바이너리',29,'#b8c5d7')
 xs=[45,400,620,830,1040,1310]
 for x,s in zip(xs,['경로','시작 ms','메모리 MiB','CPU %','점유 지연 %','점유 공백 %']):text(x,175,s,26,'#b8c5d7')
 for i,r in enumerate(rs):
  y=235+i*90;d.rounded_rectangle((25,y-8,1575,y+67),9,fill='#1b2b3e')
  vals=[r['label'],f"{r['startup_ms']['median']:.1f}",f"{r['perf0']['memory']['mean']:.1f}",f"{r['perf0']['cpu']['mean']:.1f}",f"{r['perf160']['late']['mean']:.2f}",f"{r['audit']['blank']['mean']:.3f}"]
  for x,s in zip(xs,vals):text(x,y,s,28,colors[i])
 text(45,525,'JS 점유 시 지연 비율 · 10회 전체 · 느린 실행도 포함',32)
 left,right,top,bottom=115,1510,635,1000
 peak=max(x['value'] for r in rs for x in r['perf160']['late_runs']);limit=max(1,math.ceil(peak*1.05))
 for j in range(5):
  v=limit*j/4;y=bottom-(bottom-top)*j/4;d.line((left,y,right,y),fill='#354459',width=1);text(35,y-16,f'{v:.1f}%',22,'#b8c5d7')
 for i,r in enumerate(rs):
  pts=[(left+(right-left)*(x['run']-1)/9,bottom-(bottom-top)*x['value']/limit) for x in r['perf160']['late_runs']]
  d.line(pts,fill=colors[i],width=3)
  for x,y in pts:d.ellipse((x-5,y-5,x+5,y+5),fill=colors[i])
  text(90+i*500,578,r['label'],25,colors[i])
 for j in range(10):text(left+(right-left)*j/9-8,bottom+15,str(j+1),23,'#b8c5d7')
 text(45,1070,'시작: 첫 제목·배치 확인 5회 중앙값 / 평상시 비용: 5회 평균 / 점유 지연: 10회 평균',25,'#b8c5d7')
 text(45,1115,'JS 160ms 작업 + 40ms 여유 · 공백 검사는 별도 3회 · 각 경로는 별도 실행',25,'#b8c5d7')
 text(45,1160,('메모리 RSS · 지연 콜백' if platform=='ios' else '메모리 PSS · 지연 gfxinfo 프레임')+' · 외부 호스트 부하 미통제',25,'#ffbf69')
 text(45,1205,'고정 템플릿 PoC · 전체 리스트 순위 아님 · 실물 저사양 기기와 동적 높이는 미검증',25,'#b8c5d7')
 im.save(D/f'{platform}-summary-ko.png')
