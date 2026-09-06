"""최종 교차 비교와 재터치 원인을 한글 이미지로 만든다."""
from pathlib import Path
import json, statistics
from PIL import Image, ImageDraw, ImageFont
D=Path(__file__).resolve().parent
im=Image.new('RGB',(1500,1060),'#f5f7fb');d=ImageDraw.Draw(im)
def font(n):return ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',n)
def text(x,y,s,n=28,fill='#182337'):d.text((x,y),s,font=font(n),fill=fill)
text(60,40,'지연의 주요 원인: 재터치 때 드래그 인계 누락',43)
text(60,104,'Android 에뮬레이터 · 복잡한 행 10만 건 · OpenGL 유지',25,'#526178')
d.rounded_rectangle((45,155,1455,405),20,fill='white')
text(70,178,'수정 전',30,'#c44d49');text(255,178,'관성 중 재터치 → 드래그 상태 해제 → 움직임 판정 대기',29)
text(255,225,'프레임 기록 간격 증가 33/33회 · 주변 지연 프레임 30개',27,'#a54040')
text(70,298,'수정 후',30,'#167b73');text(255,298,'관성 중 재터치 → 진행 중인 드래그 즉시 인계',29)
text(255,346,'프레임 기록 간격 증가 0/33회 · 주변 지연 프레임 0개',27,'#167b73')
text(60,435,'계측 로그를 끈 최종 교차 비교: 지연 프레임 비율',32)
rows=json.loads((D/'final-results.json').read_text())
for i,(k,label,color) in enumerate([('flatlist','FlatList','#607b9c'),('zigpool-before','ZigPool 수정 전','#cf6864'),('zigpool-after','ZigPool 수정 후','#299c8e')]):
 vals=[r['percent'] for r in rows if r['variant']==k];m=statistics.median(vals);y=505+i*102
 text(70,y,label,29)
 d.rounded_rectangle((380,y,380+m*155,y+42),8,fill=color)
 text(400+m*155,y,f'{m:.2f}%',29)
 text(70,y+48,'3회: '+' / '.join(f'{v:.2f}%' for v in vals),23,'#526178')
d.rounded_rectangle((45,835,1455,1018),20,fill='#e5ebf3')
text(70,858,'프레임 시간 p95 중앙값은 세 경로 모두 20ms',30)
text(70,907,'지연 개수도 감소: 수정 전 19/12/12개 → 수정 후 6/1/1개',26)
text(70,951,'GPU 계산 가속·내용 준비 대기 해결·실물 기기 우위를 뜻하지 않음',25,'#526178')
im.save(D/'scroll-cause-ko.png')
