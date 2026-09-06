"""측정 결과와 전달 경로를 한글 이미지로 만든다."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
D=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def canvas(title, subtitle):
 im=Image.new('RGB',(1600,1100),'#101827');d=ImageDraw.Draw(im)
 put(d,60,45,title,48);put(d,60,115,subtitle,25,'#b4c4d8')
 return im,d
def put(d,x,y,s,size=30,color='#edf4fc'):
 d.text((x,y),s,font=ImageFont.truetype(FONT,size),fill=color)
rows=json.loads((D/'summary.json').read_text())
im,d=canvas('UI 워클릿 메모리 감소 결과','RN 0.87.1 · 10만 건 · 무거운 셀 · 동일한 14개 슬롯 · 각 3회 평균')
for p,y in [('ios',190),('android',550)]:
 rs=[r for r in rows if r['platform']==p];old,new=rs[1:]
 put(d,60,y,('iOS · RSS' if p=='ios' else 'Android · PSS'),35)
 saved=old['memory_mib']-new['memory_mib']
 put(d,770,y,f"{saved:.1f}MiB 감소 ({saved/old['memory_mib']*100:.1f}%)",35,'#65e4b1')
 for i,r in enumerate(rs):
  yy=y+67+i*77
  put(d,60,yy,r['label'],28)
  w=720*r['memory_mib']/650
  d.rounded_rectangle((400,yy,400+w,yy+46),8,fill='#27ac88' if i==2 else '#52769e')
  put(d,425+w,yy+5,f"{r['memory_mib']:.1f} MiB",28)
 put(d,60,y+305,'JS 점유 시 기존·개선 워클릿 모두 공백 0% / 내용 오류·겹침 0',25,'#b4c4d8')
put(d,60,945,'기본 ZigPool보다 메모리는 여전히 높습니다. CPU 개선을 뜻하지 않습니다.',28,'#ffc785')
put(d,60,995,'시뮬레이터·에뮬레이터 탐색값 / 외부 호스트 부하 미통제 / 플랫폼 간 수치 직접 비교 불가',23,'#b4c4d8')
im.save(D/'memory-summary-ko.png')
im,d=canvas('무엇을 바꿨나요?','전체 10만 건의 실제 값을 유지하면서 데이터 전달 과정의 할당을 줄였습니다.')
stages=[('1. JS 원본 데이터','객체마다 id / title / body / height / hue'),('2. 필드별 배열로 정리','키를 항목마다 반복하는 대신 다섯 배열로 묶기'),('3. 문자열로 한 번 전달','직렬화한 문자열을 UI 워클릿으로 예약 전달'),('4. UI에서 복원하여 보관','보이는 슬롯의 항목만 조립 · 스크롤 중 JS 재요청 없음')]
for i,(title,body) in enumerate(stages):
 y=190+i*165
 d.rounded_rectangle((65,y,1535,y+125),18,fill='#1e3047')
 put(d,95,y+18,title,32,'#65e4b1');put(d,95,y+66,body,28)
 if i<3:put(d,775,y+128,'↓',30)
put(d,65,885,'전달용 문자열·JS 중간 배열은 작업 후 회수 가능 · 즉시 RSS 반환을 보장하지 않음',27,'#b4c4d8')
put(d,65,943,'대가: 시작 시 UI 복원 비용 / 추가 런타임·전체 UI 데이터 보관 비용은 남음',28,'#ffc785')
put(d,65,1000,'고정 높이 PoC · 동적 높이 / 임의 React 컴포넌트 / 실물 구형 기기 미검증',25,'#b4c4d8')
im.save(D/'memory-path-ko.png')
