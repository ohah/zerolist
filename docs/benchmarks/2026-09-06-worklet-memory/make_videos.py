"""별도 실행 녹화본을 한글 설명과 함께 병렬 배치한다. 1배속이다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json
D=Path(__file__).resolve().parent
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def run(*a):return subprocess.check_output(list(a),stderr=subprocess.STDOUT,timeout=180)
def duration(p):return float(run('ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)))
validation=[]
for platform in ['android','ios']:
 im=Image.new('RGB',(1080,190),'#152137');d=ImageDraw.Draw(im)
 def text(x,y,s,n):d.text((x,y),s,font=ImageFont.truetype(font,n),fill='white')
 text(22,12,('Android' if platform=='android' else 'iOS')+' · JS 160ms 점유 / 40ms 여유',34)
 text(22,60,'RN 0.87.1 · 10만 건 · 별도 실행 · 1배속 · 60fps 합성 · 정량 측정과 분리',26)
 labels=['기존 지그풀','기존 UI 워클릿','메모리 개선 워클릿']
 for x,s in zip([22,382,742],labels):text(x,122,s,25)
 header=D/(platform+'-video-header.png');im.save(header)
 names=['zigpool-5','template-worklet-5','template-compact-5']
 clips=[D/f'{platform}-{v}-block.mp4' for v in names]
 seconds=max(duration(p) for p in clips)
 args=['ffmpeg','-v','error','-y','-loop','1','-framerate','60','-i',str(header)]
 for p in clips:args+=['-i',str(p)]
 filters=';'.join(f'[{i+1}:v]scale=360:-2,setsar=1,fps=60,tpad=stop_mode=clone:stop_duration=10[v{i}]' for i in range(3))+';[v0][v1][v2]hstack=inputs=3[b];[0:v][b]vstack=inputs=2[v]'
 out=D/f'{platform}-compare-block.mp4'
 run(*args,'-filter_complex',filters,'-map','[v]','-t',str(seconds),'-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(out))
 run('ffmpeg','-v','error','-i',str(out),'-f','null','-')
 actual=duration(out);assert abs(actual-seconds)<.1
 run('ffmpeg','-v','error','-y','-ss','1','-i',str(out),'-frames:v','1',str(D/f'{platform}-compare-preview.png'))
 validation.append({'file':out.name,'seconds':actual,'full_decode_ok':True,'playback_rate':1,'composite_fps':60,'separate_runs':True})
 print(out.name,actual,flush=True)
(D/'video-validation.json').write_text(json.dumps(validation,indent=2))
