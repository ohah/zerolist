"""첫 행 장식 64칸의 실제 화면 중심색·중심좌표를 기존 RN 뷰와 비교한다.
모서리 안티앨리어싱 전체의 픽셀 동일성을 주장하지 않는다.
"""
from pathlib import Path
from PIL import Image
import json,colorsys
D=Path(__file__).resolve().parent
def runs(values):
 result=[];start=None
 for i,v in enumerate(values+[False]):
  if v and start is None:start=i
  if not v and start is not None:result.append((start,i-1));start=None
 return result
def dots(path):
 im=Image.open(path).convert('RGB');p=im.load();w,h=im.size
 def colored(c):return 125<=min(c)<=145 and 218<=max(c)<=230
 bands=runs([sum(colored(p[x,y]) for x in range(w))>100 for y in range(h)])[:4]
 found=[]
 for a,b in bands:
  y=(a+b)//2
  for left,right in runs([colored(p[x,y]) for x in range(w)]):
   if right-left<8:continue
   x=(left+right)//2;found.append({'x':x,'y':y,'rgb':p[x,y]})
 assert len(found)==64,(path,len(found),bands)
 return found
results=[]
for platform in ['ios','android']:
 for old,new in [('flatlist','flatlist-palette'),('template-compact','template-palette')]:
  a=dots(D/'screens'/f'{platform}-{old}-initial.png');b=dots(D/'screens'/f'{platform}-{new}-initial.png')
  position=max(max(abs(x['x']-y['x']),abs(x['y']-y['y'])) for x,y in zip(a,b))
  color=max(max(abs(c-d) for c,d in zip(x['rgb'],y['rgb'])) for x,y in zip(a,b))
  assert position<=2 and color<=1,(platform,old,position,color)
  results.append({'platform':platform,'old':old,'new':new,'checked_dots':64,'max_center_position_difference_px':position,'max_center_color_channel_difference':color})
(D/'pixel-validation.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))

# 캡처에서 제목 #3, #4, #5를 직접 확인한 두 후보 화면.
# 초기 슬롯의 #0 색이 재활용 후 남아 있지 않은지 실제 픽셀을 검사한다.
updates=[]
for platform in ['ios','android']:
 im=Image.open(D/'screens'/f'{platform}-template-palette-after-scroll.png').convert('RGB')
 p=im.load();w,h=im.size
 def colored(c):return 125<=min(c)<=145 and 218<=max(c)<=230
 bands=runs([sum(colored(p[x,y]) for x in range(w))>100 for y in range(h)])
 groups=[]
 for band in bands:
  if not groups or band[0]-groups[-1][-1][1]>30:groups.append([])
  groups[-1].append(band)
 full=[g for g in groups if len(g)==4 and g[0][0]>2 and g[-1][1]<h-2][:3]
 assert len(full)==3,(platform,full)
 for item_id,g in zip([3,4,5],full):
  actual=[]
  for a,b in g:
   y=(a+b)//2
   for left,right in runs([colored(p[x,y]) for x in range(w)]):
    if right-left>=8:actual.append(p[(left+right)//2,y])
  assert len(actual)==64,(platform,item_id,len(actual))
  expected=[tuple(round(v*255) for v in colorsys.hls_to_rgb(((item_id*47+j*5)%360)/360,.7,.6)) for j in range(64)]
  difference=max(abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref))
  assert difference<=1,(platform,item_id,difference)
  updates.append(dict(platform=platform,item_id=item_id,checked_dots=64,max_color_channel_difference=difference))
(D/'recycled-color-validation.json').write_text(json.dumps(updates,indent=2));print(json.dumps(updates,indent=2))
