"""한글 표 이미지. python3 make_images.py (Pillow 필요)."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
points=json.loads((D/'points.json').read_text());summary=json.loads((D/'summary.json').read_text())
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def f(n):return ImageFont.truetype(font,n)
labels={'flatlist':'플랫리스트','flashlist':'플래시리스트','legend':'레전드리스트','zerolist':'기존 제로리스트','zigpool':'지그풀 고정','stable':'지그풀 범위 유지'}
def label(name):
 family,rows=name.rsplit('-',1);return f'{labels[family]} · {rows}행'
def table(file,title,subtitle,headers,rows,notes):
 assert all(len(r)==len(headers) for r in rows)
 widths=[440]+[200 if len(headers)>7 else 230]*(len(headers)-1);width=sum(widths)+64;rowh=66
 height=195+rowh*(len(rows)+1)+len(notes)*40+35
 im=Image.new('RGB',(width,height),'#f5f7fb');d=ImageDraw.Draw(im)
 d.text((32,22),title,font=f(43),fill='#16233b');d.text((32,85),subtitle,font=f(25),fill='#43536b')
 y=154
 for i,row in enumerate([headers]+rows):
  x=32;d.rectangle((32,y,width-32,y+rowh),fill='#17283f' if i==0 else ('#ffffff' if i%2 else '#eaf0f7'))
  for text,w in zip(row,widths):d.text((x+14,y+18),str(text),font=f(25),fill='white' if i==0 else '#182c43');x+=w
  y+=rowh
 for note in notes:d.text((32,y+19),note,font=f(23),fill='#43536b');y+=40
 im.save(D/file)
for os,title in [('android','Android'),('ios','iOS')]:
 rows=[]
 for p in points:
  if p['platform']!=os:continue
  rows.append([label(p['name']),f"{p['memory_mib']:.1f}",f"{p['blank_area_percent']:.2f}%",f"{p['blank_frames_percent']:.1f}%",f"{p['worst_blank_area_percent']:.1f}%",f"{p['cpu_percent']:.1f}%",f"{p['frame_p95_ms']:.2f}",f"{p['late_percent']:.2f}%"])
 table(f'{os}-budget-ko.png',f'{title}: 메모리 비용과 화면 공백을 함께 비교','RN 0.87.1 · 10만 건 · JS 160ms 점유 / 40ms 여유 반복 · 녹화 없음',['설정: 한쪽 여유','메모리 MiB','평균 공백','공백 프레임','최대 공백','앱 CPU','p95 ms','지연 비율'],rows,[
  '메모리·CPU·프레임은 검사 로그를 끈 별도 실행. 공백은 실제 네이티브 행의 영역을 검사.',
  '평균 공백·비용은 중앙값, 최대 공백은 반복 전체 최댓값. 짧은 전체 공백도 함께 확인.',
  'CPU는 앱 전체 사용량을 1코어 기준으로 표시하며, 의도적으로 준 JS 점유 부하를 포함.',
  'Android: 종료 PSS / gfxinfo 지연 프레임. iOS: 종료 RSS / 늦은 CADisplayLink 콜백.',
  'iOS 콜백 지연은 실제 표시 프레임 지연이 아님. 모든 설정은 각 조건 3회 중앙값.'
 ])
rows=[]
for r in summary:
 if r['mode']!='perf' or r['block_ms']!=0:continue
 late=r.get('late_percent',r.get('late_callback_percent'));p95=r.get('p95_ms',r.get('callback_p95_ms'))
 rows.append([f"{r['platform']} · {label(r['name'])}",f"{r['memory_after_mib']['median']:.1f}",f"{r['cpu_one_core_percent']['median']:.1f}%",f"{p95['median']:.2f}",f"{late['median']:.2f}%",str(r['n'])])
if rows:table('normal-cost-ko.png','정상 조건: 얼마나 느린가','RN 0.87.1 · JS 강제 점유 없음 · 같은 18회 혼합 스와이프 · 각 설정 3회',['설정','메모리 MiB','앱 CPU','p95 ms','지연 비율','반복'],rows,['지연 비율이 2배라는 것이 실행 속도가 2배 느리다는 뜻은 아님.','Android PSS와 iOS RSS, 표시 마감과 콜백 간격은 서로 다른 지표다.'])
