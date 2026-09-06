"""명령 후보의 실제 제목·본문·합계 잉크를 동일 행의 props 기준 화면과 비교한다."""
from pathlib import Path
from PIL import Image,ImageChops
import colorsys,json
D=Path(__file__).resolve().parent
def ink_sum(im):return sum(i*n for i,n in enumerate(im.histogram()))
def rows(path):
 im=Image.open(path).convert('RGB');w,h=im.size;p=im.load();segments=[];start=0
 for y in range(1,h+1):
  if y==h or p[0,y]!=p[0,start]:
   if y-start>h/6:
    rgb=p[0,start]
    refs=[tuple(round(c*255) for c in colorsys.hls_to_rgb((i*47%360)/360,.92,.6)) for i in range(10)]
    i=min(range(10),key=lambda i:sum(abs(a-b) for a,b in zip(rgb,refs[i])))
    if max(abs(a-b) for a,b in zip(rgb,refs[i]))<=1 and start>h*.06 and y<h-2:
     # 각 행 전체를 남기되 글자가 있는 오른쪽 상단 영역만 비교한다.
     scale=w/(402 if 'ios-' in path.name else 411.4285714286)
     box=(round(80*scale),start+round(15*scale),round(w-16*scale),start+round(132*scale))
     crop=im.crop(box);mask=crop.point(lambda v:0 if v<140 else 255).convert('RGB')
     mask=Image.eval(ImageChops.lighter(ImageChops.lighter(mask.getchannel('R'),mask.getchannel('G')),mask.getchannel('B')),lambda v:255-v)
     segments.append((i,mask))
   start=y
 return dict(segments)
results=[]
for platform in ['ios','android']:
 for step in ['initial']:
  baseline=rows(D/'screens'/f'{platform}-template-palette-{step}.png')
  for engine in ['template-palette-command','template-command']:
   candidate=rows(D/'screens'/f'{platform}-{engine}-{step}.png')
   common=sorted(baseline.keys() & candidate.keys());assert len(common)>=2,(platform,step,engine,common)
   for i in common:
    a,b=baseline[i],candidate[i];assert a.size==b.size
    # 1px 수준의 행 경계 반올림만 허용하며, 빈 배경으로 오차를 희석하지 않는다.
    ink=max(ink_sum(a),ink_sum(b));assert ink>10000
    mismatch=min(ink_sum(ImageChops.difference(a,ImageChops.offset(b,x,y)))/ink for x in [-1,0,1] for y in [-1,0,1])
    results.append(dict(platform=platform,step=step,engine=engine,item_id=i,ink_mismatch=mismatch))
    assert mismatch<.05,(platform,step,engine,i,mismatch)
(D/'text-pixel-validation.json').write_text(json.dumps(results,indent=2));print('텍스트 비교',len(results),'행, 최대 잉크 차이',max(r['ink_mismatch'] for r in results))
