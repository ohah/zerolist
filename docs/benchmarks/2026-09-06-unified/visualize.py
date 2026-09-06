"""일반 셀의 정상 부하 비용과 별도 1회 공백 검사를 한글로 표시한다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
D=Path(__file__).resolve().parent;rows=json.loads((D/'summary.json').read_text())
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
for platform in ['android','ios']:
 im=Image.new('RGB',(1500,1240),'#101827');d=ImageDraw.Draw(im)
 def text(x,y,s,n=27,c='#edf4fc'):d.text((x,y),s,font=ImageFont.truetype(font,n),fill=c)
 text(40,25,('Android' if platform=='android' else 'iOS')+' · ZeroList 통합 후 · 정상 부하',42)
 text(40,90,'10만 건 · RN 0.87.1 · 강제 JS 점유 없음 · 한쪽 5행 준비 목표',28,'#b8c5d7')
 for ci,cell in enumerate(['simple','heavy']):
  top=160+ci*430;text(40,top,'가벼운 셀' if cell=='simple' else '무거운 셀',31)
  xs=[40,410,670,920,1200]
  for x,s in zip(xs,['리스트','메모리 MiB','CPU %','지연 %','공백 %']):text(x,top+55,s,25,'#b8c5d7')
  for i,r in enumerate(x for x in rows if x['platform']==platform and x['cell']==cell):
   y=top+100+i*58;d.rounded_rectangle((25,y-4,1475,y+48),8,fill='#1b2b3e')
   color='#66d9c0' if r['engine']=='zerolist' else '#edf4fc'
   vals=[r['label'],f"{r['memory']['mean']:.1f}",f"{r['cpu']['mean']:.1f}",f"{r['late']['mean']:.2f}",f"{r['audit']['mean_blank_area_percent']:.3f}"]
   for x,s in zip(xs,vals):text(x,y,s,27,color)
 text(40,1060,'비용: 각 3회 평균 / 공백: 별도 1회 / 동적 변경 성능·수정 전후 속도 비교 아님',25,'#ffbf69')
 text(40,1110,('PSS · gfxinfo 프레임' if platform=='android' else 'RSS · CADisplayLink 콜백')+' · 에뮬레이터/시뮬레이터 · 호스트 외부 부하 미통제',25,'#b8c5d7')
 text(40,1160,'모든 창·배치 설정을 최적화한 순위 아님 · 실물 기기·준비 중 최대 메모리는 미검증',25,'#b8c5d7')
 im.save(D/f'{platform}-normal-ko.png')
