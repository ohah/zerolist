"""Compose five-engine videos and stills. Requires ffmpeg/ffprobe and Pillow.
Original presentation times are preserved; slow motion duplicates, not interpolates.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json, subprocess,tempfile
P=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(n):
 try:return ImageFont.truetype(FONT,n)
 except OSError:return ImageFont.truetype('DejaVuSans.ttf',n)
def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*args],check=True)
engines=['flatlist','legend','flashlist','zerolist','zigpool']
names=['FlatList','LegendList','FlashList','ZeroList (JS)','ZigPool']
colors=['#60a5fa','#4ade80','#c084fc','#fbbf24','#fb923c']
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for cell in ['complex','heavy']:
  im=Image.new('RGB',(1350,80),'#111827');d=ImageDraw.Draw(im)
  d.text((20,7),f'100,000 items / {cell} / 1x / separate runs / normal modes',font=font(23),fill='white')
  for i,n in enumerate(names):d.text((i*270+15,43),n,font=font(23),fill=colors[i])
  im.save(t/'header.png')
  inputs=[]
  for e in engines:inputs+=['-i',str(P/f'{cell}-{e}.mp4')]
  filters=';'.join(f'[{i}:v]setpts=PTS-STARTPTS,fps=30,scale=270:600[v{i}]' for i in range(5))
  filters+=';[v0][v1][v2][v3][v4]hstack=inputs=5:shortest=1[grid];[5:v][grid]vstack=inputs=2[out]'
  run(inputs+['-loop','1','-i',str(t/'header.png'),'-filter_complex',filters,'-map','[out]','-t','9','-c:v','libx264','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(P/f'comparison-{cell}.mp4')])
 inputs=[]
 for e in engines:inputs+=['-ss','2','-t','6','-i',str(P/f'heavy-{e}.mp4')]
 im=Image.new('RGB',(1350,80),'#111827');d=ImageDraw.Draw(im)
 d.text((20,7),'HEAVY / 100,000 / 0.25x / source 2-8s / no interpolation',font=font(23),fill='white')
 for i,n in enumerate(names):d.text((i*270+15,43),n,font=font(23),fill=colors[i])
 im.save(t/'slow.png')
 filters=';'.join(f'[{i}:v]crop=540:880:0:160,scale=270:440,setpts=4*(PTS-STARTPTS),fps=30[v{i}]' for i in range(5))
 filters+=';[v0][v1][v2][v3][v4]hstack=inputs=5:shortest=1[grid];[5:v][grid]vstack=inputs=2[out]'
 run(inputs+['-loop','1','-i',str(t/'slow.png'),'-filter_complex',filters,'-map','[out]','-t','24','-c:v','libx264','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'heavy-detail-slow.mp4')])
 run(['-ss','1','-t','6','-i',str(P/'comparison-heavy.mp4'),'-filter_complex','fps=10,scale=810:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer','-loop','0',str(P/'preview-heavy.gif')])
im=Image.new('RGB',(1350,1310),'#111827');d=ImageDraw.Draw(im)
for row,phase in enumerate(['before','after']):
 for i,(e,n) in enumerate(zip(engines,names)):
  d.text((i*270+8,row*655+8),n+' / '+phase,font=font(18),fill='white')
  im.paste(Image.open(P/f'heavy-{e}-{phase}.png').convert('RGB').resize((270,600)),(i*270,row*655+40))
im.save(P/'contact-heavy.jpg',quality=88)
# Both cell types at rest, all five engines.
im=Image.new('RGB',(1350,1310),'#111827');d=ImageDraw.Draw(im)
for row,cell in enumerate(['complex','heavy']):
 for i,(e,n) in enumerate(zip(engines,names)):
  d.text((i*270+8,row*655+8),n+' / '+cell,font=font(18),fill='white')
  im.paste(Image.open(P/f'{cell}-{e}-before.png').convert('RGB').resize((270,600)),(i*270,row*655+40))
im.save(P/'layout-check.jpg',quality=88)
valid=[]
for f in sorted(P.glob('*.mp4')):
 run(['-i',str(f),'-fps_mode','passthrough','-enc_time_base','1/1000000','-f','null','-'])
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,nb_frames,avg_frame_rate','-of','json',str(f)]))
 valid.append({'video':f.name,'full_decode':'passed',**probe})
(P/'video-validation.json').write_text(json.dumps(valid,indent=2)+'\n')
print('Visuals generated and decoded')
