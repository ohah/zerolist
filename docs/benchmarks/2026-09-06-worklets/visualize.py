"""한글 결과 표와 처리 경로 이미지. 원자료 집계만 사용한다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
D=Path(__file__).resolve().parent
F='/System/Library/Fonts/AppleSDGothicNeo.ttc'
bg='#f5f7fb';ink='#142238';muted='#56647a';blue='#1b64c8';green='#127e63'
def canvas(h):
 im=Image.new('RGB',(1500,h),bg);return im,ImageDraw.Draw(im)
def txt(d,x,y,s,n=28,color=ink):d.text((x,y),s,font=ImageFont.truetype(F,n),fill=color)
def box(d,x,y,w,h,color):d.rounded_rectangle((x,y,x+w,y+h),18,fill=color)
im,d=canvas(960)
txt(d,48,35,'React 구조는 유지하고, 내용 갱신은 UI 워클릿으로',45)
txt(d,48,100,'GPU API는 그대로 · 요청 수신과 속성 갱신 경로 실험',30,muted)
rows=[('기존 ZigPool',['네이티브 요청','JS 수신 대기','React 셀 렌더','내용·매핑 커밋']),('JS 수신 템플릿',['네이티브 요청','JS 수신 대기','UI 워클릿 계산','내용·매핑 커밋']),('UI 수신 템플릿',['네이티브 요청','UI 직접 수신','UI 워클릿 계산','내용·매핑 커밋'])]
for i,(label,steps) in enumerate(rows):
 y=190+i*190;txt(d,48,y,label,32,green if i==2 else ink)
 for j,s in enumerate(steps):
  x=48+j*362;box(d,x,y+55,314,85,'#d8f1e9' if i==2 else '#e2eafa');txt(d,x+18,y+77,s,29)
  if j<3:txt(d,x+324,y+77,'→',32,muted)
txt(d,48,805,'두 템플릿은 같은 데이터·풀·연산·전용 텍스트를 사용합니다.',31)
txt(d,48,855,'제약: 고정 높이 / 임의 renderItem 호환 아님 / UI 계산 과부하·추가 메모리 주의',27,muted)
im.save(D/'worklet-path-ko.png')
rs=json.loads((D/'summary.json').read_text())
im,d=canvas(1120)
txt(d,48,32,'10만 건 비교: 내용 준비와 메모리를 함께 봅니다',43)
txt(d,48,94,'RN 0.87.1 · 고정 높이·무거운 셀 · 슬롯 14개 · 각 조건 3회 · 시뮬레이터/에뮬레이터',26,muted)
for i,platform in enumerate(['ios','android']):
 y=170+i*355
 txt(d,48,y,'iOS' if platform=='ios' else 'Android',35)
 columns=[(60,'엔진'),(470,'평균 공백'),(700,'무공백 실행'),(955,'메모리'),(1235,'평상시 CPU')]
 box(d,40,y+55,1420,55,'#dfe7f4')
 for x,s in columns:txt(d,x,y+65,s,25)
 for j,r in enumerate(v for v in rs if v['platform']==platform):
  yy=y+125+j*62
  if r['engine']=='template-worklet':box(d,40,yy-3,1420,57,'#d8f1e9')
  vals=[r['label'],f"{r['blank_mean_percent']:.3f}%",f"{r['zero_blank_runs']} / 3",f"{r['normal_memory_mib']:.1f} MiB",f"{r['normal_cpu_percent']:.1f}%"]
  for (x,_),v in zip(columns,vals):txt(d,x,yy,v,28)
 txt(d,48,y+318,('메모리: 종료 RSS' if platform=='ios' else '메모리: 종료 PSS')+' · CPU: 코어 하나 100% 기준',23,muted)
txt(d,48,915,'공백: JS 160ms 점유 / 40ms 여유 조건의 이동 중 평균 빈 면적',27)
txt(d,48,962,'메모리·CPU: 별도 평상시 실행. 호스트 외부 부하가 있어 비용은 탐색값입니다.',27)
txt(d,48,1010,'전용 템플릿의 효과이며, 일반 React 셀·동적 높이·실물 구형 태블릿의 검증은 남았습니다.',25,muted)
im.save(D/'worklet-summary-ko.png')
