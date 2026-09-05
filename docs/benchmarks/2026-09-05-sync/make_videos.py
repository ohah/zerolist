"""별도 실행 녹화본에 한글 설명을 붙인다. 재생 속도는 1배다."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json
P=Path(__file__).resolve().parent
font='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def run(*a):return subprocess.run(a,capture_output=True,check=True).stdout
def dur(p):return float(run('ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)))
for platform in ['android','ios']:
 for delay in [0,120]:
  header=P/f'{platform}-header-{delay}.png'
  im=Image.new('RGB',(1080,180),'#101827');d=ImageDraw.Draw(im)
  def text(x,y,s,n=29):d.text((x,y),s,font=ImageFont.truetype(font,n),fill='#e7edf7')
  text(25,12,('Android' if platform=='android' else 'iOS')+' · '+('정상 조건' if delay==0 else '내용 반영 120ms 강제 지연'),36)
  text(25,62,'10만 건 / 별도 실행 비교 / 1배속',26)
  text(25,119,'이전: 위치를 먼저 변경',29);text(560,119,'수정: 확정된 내용과 함께 배치',29)
  im.save(header)
  left=P/f'{platform}-legacy-{delay}.mp4';right=P/f'{platform}-fixed-{delay}.mp4'
  seconds=max(dur(left),dur(right))
  graph='[1:v]scale=540:-2,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=5[l];[2:v]scale=540:-2,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=5[r];[l][r]hstack=inputs=2[b];[0:v][b]vstack=inputs=2[v]'
  out=P/f'{platform}-compare-{delay}.mp4'
  run('ffmpeg','-v','error','-y','-loop','1','-framerate','30','-i',str(header),'-i',str(left),'-i',str(right),'-filter_complex',graph,'-map','[v]','-t',str(seconds),'-c:v','libx264','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out))
  run('ffmpeg','-v','error','-i',str(out),'-f','null','-')
  assert abs(dur(out)-seconds)<.08
  run('ffmpeg','-v','error','-y','-ss','4','-i',str(out),'-frames:v','1',str(P/f'{platform}-compare-{delay}-preview.png'))
  print(out.name,seconds,flush=True)

# 강제 지연 장면을 자세히 볼 수 있게 0.25배속도 만든다.
for platform in ['android','ios']:
 source=P/f'{platform}-compare-120.mp4'
 band=P/f'{platform}-slow-label.png'
 im=Image.new('RGB',(1080,65),'#542c18');d=ImageDraw.Draw(im)
 d.text((25,12),'관찰용 0.25배속 · 강제 120ms 지연 · 정상 속도 평가용 아님',font=ImageFont.truetype(font,28),fill='white');im.save(band)
 out=P/f'{platform}-compare-120-slow.mp4'
 run('ffmpeg','-v','error','-y','-loop','1','-framerate','30','-i',str(band),'-i',str(source),'-filter_complex','[1:v]setpts=4*PTS,fps=30[b];[0:v][b]vstack=inputs=2,pad=ceil(iw/2)*2:ceil(ih/2)*2[v]','-map','[v]','-t',str(dur(source)*4),'-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(out))
 run('ffmpeg','-v','error','-i',str(out),'-f','null','-')
 print(out.name,dur(out),flush=True)
