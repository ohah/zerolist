"""한글 비용 표와 공백 원인 도식. 과학적 측정치는 집계 JSON에서 읽는다."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def font(n):return ImageFont.truetype(FONT,n)
def table_image(os,ps):
 w=1920;h=370+len(ps)*76+230
 im=Image.new('RGB',(w,h),'#f4f7fc');d=ImageDraw.Draw(im)
 d.text((35,24),('iOS' if os=='ios' else 'Android')+' 내용 준비 개선: 비용과 공백',font=font(43),fill='#17263e')
 d.text((35,88),('외부 테스트와 시간대 겹침: Android 비용·프레임은 통제 비교에서 제외' if os=='android' else 'RN 0.87.1 · 고정 높이 10만 건 · 각 조건 3회 · 기본값 변경 없음'),font=font(26),fill='#465b76')
 xs=[35,420,630,850,1060,1250,1460,1690]
 heads=['설정','일반 CPU','일반 메모리','부하 CPU','평균 공백','최대 공백','최대 지속','무공백 실행']
 d.rectangle((24,150,w-24,218),fill='#182a40')
 for x,head in zip(xs,heads):d.text((x,169),head,font=font(25),fill='white')
 for i,p in enumerate(ps):
  y=218+i*76;d.rectangle((24,y,w-24,y+76),fill='white' if i%2==0 else '#e7eff8')
  vals=[p['label'],f"{p['normal_cpu']:.1f}%",f"{p['normal_memory']:.1f} MiB",f"{p['stress_cpu']:.1f}%",f"{p['mean_blank']:.3f}%",f"{p['worst_blank']:.1f}%",f"{p['max_duration']:.1f} ms",f"{p['zero_runs']}/3"]
  for x,v in zip(xs,vals):d.text((x,y+22),v,font=font(24),fill='#18314c')
 y=240+len(ps)*76
 notes=['부하: JS 160ms 점유 / 40ms 여유. 공백 검사와 비용 측정은 별도 실행.', '평균 공백·비용은 실행별 수치의 중앙값. 최대 공백·지속은 3회 전체 최댓값.', '평균 공백 중앙값 0%여도 한 실행에서 공백이 생길 수 있어 무공백 횟수를 함께 표시.', '메모리는 종료 표본: Android PSS / iOS RSS. CPU는 앱 프로세스 전체, 1코어 기준.', '최대 지속은 검사 시각 차이이며 실제 GPU 표시 시각의 직접 측정이 아님.', '실기기·동적 높이·발열·배터리는 미검증. 프레임 지표와 모든 반복은 한글 문서 참조.']
 for line in notes:d.text((35,y),line,font=font(24),fill='#465b76');y+=44
 im=im.crop((0,0,w,y+28));im.save(D/f'{os}-readiness-ko.png')
ps=json.loads((D/'confirmation-summary.json').read_text())
for os in ['ios','android']:table_image(os,[p for p in ps if p['platform']==os])
c=json.loads((D/'blank-case.json').read_text());im=Image.new('RGB',(1660,720),'#f4f7fc');d=ImageDraw.Draw(im)
d.text((35,25),'공백의 직접 원인: 화면이 준비 범위를 넘어감',font=font(43),fill='#17263e')
d.text((35,90),'iOS 대기 보정 12행 · 실제 공백 검사 로그의 한 구간',font=font(28),fill='#465b76')
d.rounded_rectangle((45,170,780,345),radius=12,fill='#dcece4')
d.text((70,192),'마지막으로 반영된 셀: 234~261번',font=font(32),fill='#174b3c')
d.text((70,246),'28개 × 행 높이 234pt',font=font(28),fill='#174b3c')
d.text((70,291),'준비 범위 끝: 61,308pt',font=font(31),fill='#174b3c')
d.rounded_rectangle((865,170,1615,345),radius=12,fill='#f9dfdf')
d.text((892,192),'그다음 화면 시작: 61,448pt',font=font(32),fill='#813332')
d.text((892,246),'화면 높이: 874pt',font=font(28),fill='#813332')
d.text((892,291),'화면 전체가 준비 범위 밖 → 공백',font=font(31),fill='#813332')
d.line((785,254,852,254),fill='#465b76',width=5);d.polygon([(852,254),(837,244),(837,264)],fill='#465b76')
notes=['새 요청은 발생했지만 JS가 점유되어 다음 내용 반영을 기다렸다.', '우선순위를 높여도 실행 중인 JS 루프를 강제로 중단하지는 못한다.', '이 사례의 공백은 방향 전환 직전부터 시작됐다.', '모든 공백의 원인이 같다는 뜻은 아니다. 이 구간은 로그로 범위 소진을 확인했다.']
y=390
for line in notes:d.text((45,y),line,font=font(29),fill='#18314c');y+=58
d.text((45,650),'원자료: blank-case.json / blank-case-lines.log',font=font(24),fill='#465b76');im.save(D/'blank-cause-ko.png')
