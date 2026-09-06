from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
r=json.loads((D/'summary.json').read_text())
im=Image.new('RGB',(1550,1000),'#101827');d=ImageDraw.Draw(im)
def text(x,y,s,n=28,color='#e5edf7'):
 d.text((x,y),s,font=ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',n),fill=color)
text(45,30,'Android 실기기 · 10만 건 리스트 비교',44)
text(45,98,'SM-S731N · Android 16 · RN 0.87.1 · 60Hz · 기본 Vulkan',28,'#b4c1d3')
text(45,144,'각 3회 · 무거운 행 · CPU와 메모리는 평균, 지연은 전체 프레임 기준',26,'#b4c1d3')
for x,s in [(45,'리스트'),(590,'CPU 사용률 %'),(930,'메모리 MiB'),(1260,'지연 %')]:text(x,222,s,28)
for i,row in enumerate(r):
 y=280+i*80;d.rounded_rectangle((30,y,1520,y+66),radius=10,fill='#1d2c3f')
 c='#58deca' if row['name']=='zerolist-5' else '#ffc56a' if row['name']=='zerolist-before-5' else '#e5edf7'
 text(45,y+14,row['label'],30,c)
 for x,v in [(590,row['stats']['cpu_one_core_percent']['mean']),(930,row['stats']['memory_after_mib']['mean']),(1260,row['weighted_late_percent'])]:text(x,y+14,f'{v:.2f}',30,c)
text(45,800,'최적화 이전 경로: 같은 APK에서 최근 네이티브 변경 2개를 끈 대조군',27,'#ffc56a')
text(45,849,'기존 ZigPool은 동일한 공개 API·항목 상태 보장을 제공하는 대체재로 해석하지 않음',25,'#b4c1d3')
text(45,895,'한 기기·한 시나리오 결과 · 저사양 태블릿과 120Hz 성능은 별도 검증 필요',26,'#b4c1d3')
text(45,941,'실행별 범위와 별도 화면 검사는 comparison-ko.md 참고',25,'#b4c1d3')
im.save(D/'comparison-ko.png')
