from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def f(n):return ImageFont.truetype(font,n)
im=Image.new('RGB',(1500,1420),'#101827');d=ImageDraw.Draw(im)
def text(x,y,s,n=29,color='#e5edf7'):d.text((x,y),s,font=f(n),fill=color)
text(40,30,'Android 최종 유지 경로 · 10만 건',46)
text(40,100,'RN 0.87.1 · 비용 각 3회 평균 · 슬롯 memo 후보는 회수',28,'#b4c1d3')
r=json.loads((D/'native-stage-summary.json').read_text());y=165
for cell,label in [('heavy','무거운 셀'),('simple','가벼운 셀')]:
 text(40,y,label,34);y+=65
 for x,s in [(40,'리스트'),(675,'CPU %'),(940,'메모리 MiB'),(1230,'지연 %')]:text(x,y,s,26,'#b4c1d3')
 y+=42
 for row in r:
  if row['cell']!=cell:continue
  d.rounded_rectangle((25,y,1475,y+58),radius=9,fill='#1d2c3f');color='#58deca' if row['name']=='zerolist-5' else ('#ffc56a' if row['name']=='zerolist-before-5' else '#e5edf7')
  text(40,y+10,row['label'],28,color)
  for x,k in [(675,'cpu_one_core_percent'),(940,'memory_after_mib'),(1230,'late_percent')]:text(x,y+10,f"{row['stats'][k]['mean']:.2f}",29,color)
  y+=66
 y+=35
text(40,1220,'수정 전 경로: 같은 APK에서 두 네이티브 변경만 끈 대조군',27,'#ffc56a')
text(40,1270,'CPU는 사용량 · 메모리는 종료 PSS · 지연은 gfxinfo 프레임 판정',26,'#b4c1d3')
text(40,1320,'외부 호스트 부하 미통제 · 실물 저사양 기기 미검증 · 큰 속도 개선 확정 아님',26,'#b4c1d3')
im.save(D/'android-comparison-ko.png')
im=Image.new('RGB',(1500,780),'#101827');d=ImageDraw.Draw(im)
text(40,30,'좋은 단기 결과만으로 채택하지 않았습니다',43)
text(40,100,'슬롯 memo 후보 · 같은 APK의 켬/끔 비교 · Android 무거운 셀',28,'#b4c1d3')
text(40,180,'비교',29);text(530,180,'memo 끔',29);text(930,180,'memo 켬',29)
for y,label,a,b in [(245,'짧은 5회 · CPU 사용량','20.14%','18.32%'),(325,'긴 3회 · CPU 사용량','25.38%','29.57%'),(405,'긴 3회 · 종료 메모리','194.85 MiB','207.58 MiB'),(485,'긴 3회 · 지연 프레임','0.68%','2.13%')]:
 text(40,y,label,28);text(530,y,a,30);text(930,y,b,30,'#ffc56a')
text(40,590,'최종 결정: 슬롯 memo 회수 · 항목 상태 보호와 준비량 유지',30,'#58deca')
text(40,655,'짧은 실행 18회 / 긴 실행 90회 스와이프 · 두 실행 길이의 CPU 값은 직접 비교 금지',24,'#b4c1d3')
text(40,705,'외부 부하 영향과 원인 불확실성은 남음 · 실패한 로그 검사 1회는 기록 후 재개',24,'#b4c1d3')
im.save(D/'memo-decision-ko.png')
