"""동시에 겹치는 두 스레드 구간을 각각 표시한다. 합산·성능 순위가 아니다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
D=Path(__file__).resolve().parent
rs=json.loads((D/'trace-analysis.json').read_text())['template-command']['slow_slice_states']
ui=next(r for r in rs if r['slice_name'].startswith('Choreographer#doFrame ') and 'resynced' not in r['slice_name'])
rt=next(r for r in rs if r['slice_name'].startswith('DrawFrames '))
im=Image.new('RGB',(1500,800),'#101827');d=ImageDraw.Draw(im)
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def text(x,y,s,n=27,c='#edf4fc'):d.text((x,y),s,font=ImageFont.truetype(font,n),fill=c)
text(40,25,'긴 프레임은 실제 실행과 대기를 나눠 봐야 합니다',40)
text(40,90,'Android · 글자·장식 명령 · 별도 시스템 추적 1회 · 정량 비교와 분리',28,'#b8c5d7')
colors=['#66d9c0','#ffbf69','#8faadc'];keys=['running_ms','runnable_ms','sleeping_ms']
for x,s,c in zip([45,440,980],['CPU에서 실행','실행 가능하지만 CPU 대기','잠든 상태의 대기'],colors):
 d.rectangle((x,155,x+22,177),fill=c);text(x+33,148,s,26)
for y,label,r in [(230,'UI 프레임',ui),(420,'렌더 스레드 작업',rt)]:
 text(45,y,f"{label} · 전체 {float(r['wall_ms']):.2f}ms",30)
 x=45
 for key,c in zip(keys,colors):
  value=float(r[key]);w=value/80*1390;d.rectangle((x,y+57,x+w,y+108),fill=c);x+=w
 text(45,y+124,' / '.join(f'{s} {float(r[k]):.2f}ms' for s,k in zip(['CPU 실행','CPU 대기','잠든 대기'],keys)),25,'#b8c5d7')
text(45,650,'두 구간은 시간상 겹칩니다. 합산하지 않습니다. 한 번의 느린 관측으로 순위를 매기지 않습니다.',25,'#ffbf69')
text(45,705,'잠든 대기만으로 GPU·드라이버 중 하나를 원인으로 확정할 수 없습니다.',26,'#b8c5d7')
text(45,750,'스레드 상태와 실제 구간을 겹쳐 계산 · GPU 실행 시간 자체는 미측정',24,'#b8c5d7')
im.save(D/'trace-summary-ko.png')
