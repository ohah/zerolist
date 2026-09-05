# coding: utf-8
"""Run beside captured artifacts. Requires Pillow and ffmpeg; no frame interpolation."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, subprocess, statistics, tempfile
P=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(n):
 try:return ImageFont.truetype(FONT,n)
 except OSError:return ImageFont.truetype('DejaVuSans.ttf',n)
def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*args],check=True)
engines=['flatlist','legend','flashlist','zigpool']; names=['FlatList','LegendList','FlashList','ZigPool']
colors=['#3b82f6','#16a34a','#a855f7','#ea580c']
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for cell in ['complex','heavy']:
  im=Image.new('RGB',(1080,80),'#111827'); d=ImageDraw.Draw(im)
  d.text((20,7),f'100,000 items / {cell} / 1x / separate runs',font=font(21),fill='white')
  for i,n in enumerate(names):d.text((i*270+15,43),n,font=font(23),fill=colors[i])
  im.save(t/'header.png')
  inputs=[]
  for e in engines:inputs+=['-i',str(P/f'{cell}-{e}.mp4')]
  filters=';'.join(f'[{i}:v]setpts=PTS-STARTPTS,fps=30,scale=270:600[v{i}]' for i in range(4))
  filters+=';[v0][v1][v2][v3]hstack=inputs=4:shortest=1[grid];[4:v][grid]vstack=inputs=2[out]'
  run(inputs+['-loop','1','-i',str(t/'header.png'),'-filter_complex',filters,'-map','[out]','-t','9','-c:v','libx264','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(P/f'comparison-{cell}.mp4')])
 # Zoom crops from exactly the same interval in each original.
 inputs=[]
 for e in engines:inputs+=['-ss','2','-t','6','-i',str(P/f'heavy-{e}.mp4')]
 im=Image.new('RGB',(1080,70),'#111827');d=ImageDraw.Draw(im)
 d.text((15,5),'HEAVY / 100,000 / 0.25x / source 2-8s / no interpolation',font=font(23),fill='white')
 d.text((15,38),'Top: FlatList | LegendList    Bottom: FlashList | ZigPool',font=font(22),fill='white');im.save(t/'slow.png')
 filters=';'.join(f'[{i}:v]crop=540:440:0:300,setpts=4*(PTS-STARTPTS),fps=30[v{i}]' for i in range(4))
 filters+=';[v0][v1]hstack[top];[v2][v3]hstack[bottom];[5:v][top][bottom]vstack=inputs=3[out]'
 # Header is input 4.
 filters=filters.replace('[5:v]','[4:v]')
 run(inputs+['-loop','1','-i',str(t/'slow.png'),'-filter_complex',filters,'-map','[out]','-t','24','-c:v','libx264','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'heavy-detail-slow.mp4')])
 run(['-ss','1','-t','6','-i',str(P/'comparison-heavy.mp4'),'-filter_complex','fps=10,scale=540:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer','-loop','0',str(P/'preview-heavy.gif')])
# Full-height before/after contact sheet.
im=Image.new('RGB',(1080,1310),'#111827');d=ImageDraw.Draw(im)
for row,phase in enumerate(['before','after']):
 for i,(e,n) in enumerate(zip(engines,names)):
  d.text((i*270+8,row*655+8),n+' / '+phase,font=font(19),fill='white')
  shot=Image.open(P/f'heavy-{e}-{phase}.png').convert('RGB').resize((270,600))
  im.paste(shot,(i*270,row*655+40))
im.save(P/'contact-heavy.jpg',quality=85)
# Every run is shown; black tick = median, not pooled frames.
rows=json.loads((P/'results-100k-heavy.json').read_text())
im=Image.new('RGB',(1200,740),'white');d=ImageDraw.Draw(im)
d.text((35,20),'100,000 heavy items | 5 runs | emulator | no recording',font=font(28),fill='#111827')
for panel,(key,label,limit) in enumerate([('jank_percent','Janky frames (%) - lower is better',6),('p95_ms','Frame duration p95 (ms) - lower is better',30)]):
 left=80+panel*600; top=130;bottom=570;width=470
 d.text((left-35,85),label,font=font(21),fill='#111827')
 for j in range(6):
  y=bottom-j/5*(bottom-top);d.line((left,y,left+width,y),fill='#d1d5db')
  d.text((left-35,y-9),f'{j*limit/5:g}',font=font(17),fill='#4b5563')
 for i,(e,n) in enumerate(zip(engines,names)):
  x=left+50+i*120;vals=[float(r[key]) for r in rows if r['engine']==e]
  for j,v in enumerate(vals):
   y=bottom-v/limit*(bottom-top);xx=x+(j-2)*8;d.ellipse((xx-5,y-5,xx+5,y+5),fill=colors[i])
  med=statistics.median(vals);y=bottom-med/limit*(bottom-top);d.line((x-24,y,x+24,y),fill='black',width=3)
  d.text((x-40,590),n,font=font(16),fill='#111827');d.text((x-30,620),f'{med:g}',font=font(22),fill=colors[i])
d.text((45,690),'Dots: individual runs. Black tick / number: median. Different scroll physics and small samples apply.',font=font(20),fill='#374151')
im.save(P/'metrics.png')
print('Visuals generated')
