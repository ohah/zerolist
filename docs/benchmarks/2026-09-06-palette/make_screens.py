"""실제 초기 화면 4종을 한글 설명과 함께 배치한다. 원본은 screens/에 보존한다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
for platform in ['ios','android']:
 im=Image.new('RGB',(1440,1100),'#101827');d=ImageDraw.Draw(im)
 def text(x,y,s,n=25,color='#edf4fc'):d.text((x,y),s,font=ImageFont.truetype(font,n),fill=color)
 text(25,20,('iOS' if platform=='ios' else 'Android')+' · 같은 64칸, 장식 뷰를 하나로 통합',38)
 text(25,80,'실제 화면 캡처 · 원본 비율 유지 · 정량 측정과 분리',27,'#b4c4d8')
 for j,(e,label) in enumerate([('flatlist','FlatList'),('flatlist-palette','FlatList 장식 통합'),('template-compact','메모리 개선 워클릿'),('template-palette','장식 통합 워클릿')]):
  x=15+j*360;text(x,135,label)
  shot=Image.open(D/'screens'/f'{platform}-{e}-initial.png').convert('RGB')
  shot=shot.resize((330,round(shot.height*330/shot.width)),Image.Resampling.LANCZOS)
  im.paste(shot,(x,185))
 text(25,970,'초기 64칸 중심 검사: 위치 차이 최대 1픽셀 · 색상 차이 채널당 최대 1',26,'#ffc785')
 text(25,1015,'칸 수·데이터·텍스트·이미지는 유지 · 모서리 전체 픽셀 동일성을 뜻하지 않음',26,'#b4c4d8')
 text(25,1060,'워클릿 풀 14행: 장식용 애니메이션 구독 896개 → 14개',26,'#b4c4d8')
 im.save(D/f'{platform}-screens-ko.png')
