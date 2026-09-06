"""14행 풀 밖 실제 화면에서 OCR로 행 번호를 읽고 장식 64칸·본문·합계를 검증한다."""
from pathlib import Path
from PIL import Image
import json,subprocess,re,colorsys,math,unicodedata
D=Path(__file__).resolve().parent
paths=sorted((D/'screens').glob('*-after-scroll.png'))
ocr=json.loads(subprocess.check_output(['/private/tmp/zerolist-command-ocr',*map(str,paths)]))
(D/'ocr-observations.json').write_text(json.dumps(ocr,ensure_ascii=False,indent=2))
def runs(values):
 result=[];start=None
 for i,v in enumerate(values+[False]):
  if v and start is None:start=i
  if not v and start is not None:result.append((start,i-1));start=None
 return result
words='lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore'.split()
def text(seed,n):return ' '.join(words[(seed+j*7)%len(words)] for j in range(n))
def normalized(s):
 # OCR가 라틴 글자에 붙인 발음 기호와 점 없는 i만 정규화한다.
 s=''.join(c for c in unicodedata.normalize('NFKD',s.lower()).replace('ı','i') if not unicodedata.combining(c))
 return ' '.join(re.findall(r'[a-z]+',s))
results=[]
for path in paths:
 im=Image.open(path).convert('RGB');p=im.load();w,h=im.size
 def colored(c):return 125<=min(c)<=145 and 218<=max(c)<=230
 bands=runs([sum(colored(p[x,y]) for x in range(w))>100 for y in range(h)])
 groups=[]
 for band in bands:
  if not groups or band[0]-groups[-1][-1][1]>30:groups.append([])
  groups[-1].append(band)
 titles=[]
 for row in ocr[path.name]:
  m=re.match(r'#(\d+)\s',row['text'])
  if m:titles.append(dict(row,item_id=int(m[1]),top=(1-row['y']-row['height'])*h,bottom=(1-row['y'])*h))
 checked=0
 for g in groups:
  if len(g)!=4 or g[0][0]<2 or g[-1][1]>=h-2:continue
  before=[t for t in titles if 0<g[0][0]-t['top']<h/4]
  if not before:continue # 제목이 잘린 상단 행은 판정하지 않는다.
  title=max(before,key=lambda t:t['top']);i=title['item_id'];assert i>=14
  assert normalized(title['text'])==text(i,3),(path.name,i,title)
  actual=[]
  for a,b in g:
   y=(a+b)//2
   for left,right in runs([colored(p[x,y]) for x in range(w)]):
    if right-left>=8:actual.append(p[(left+right)//2,y])
  assert len(actual)==64,(path.name,i,len(actual))
  expected=[tuple(round(c*255) for c in colorsys.hls_to_rgb(((i*47+j*5)%360)/360,.7,.6)) for j in range(64)]
  diff=max(abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref));assert diff<=1,(path.name,i,diff)
  rows=[r for r in ocr[path.name] if title['bottom']<(1-r['y']-r['height']/2)*h<g[0][0] and r['x']>.15]
  sumrow=next(r for r in rows if re.search(r'\d{5}\.\d',r['text']))
  value=re.search(r'\d{5}\.\d',sumrow['text'])[0]
  reference=f'{sum(math.sqrt((j*(i+1))%97) for j in range(4000)):.1f}'
  assert value==reference,(path.name,i,value,reference)
  body=' '.join(r['text'] for r in sorted(rows,key=lambda r:-r['y']) if r['y']>sumrow['y']+sumrow['height']/2)
  body=normalized(body);expected_body=text(i+1,3+(i*37)%18)
  assert len(body)>10 and expected_body.startswith(body),(path.name,i,body,expected_body)
  checked+=1;results.append(dict(file=path.name,item_id=i,checked_dots=64,max_color_channel_difference=diff,body_prefix=body,sum=value))
 assert checked>=2,(path.name,checked)
(D/'reuse-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('풀 밖 실제 화면',len(results),'행 검증 통과')
