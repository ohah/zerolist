"""영상 전체 디코딩·타임스탬프와 보고서 내부 링크를 검증한다."""
from pathlib import Path
import subprocess,json,hashlib,re,ast
P=Path(__file__).resolve().parent
rows=[]
for f in sorted(P.glob('*.mp4')):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]));v=d['streams'][0]
 # 원본은 가변 프레임 간격이다. 기본 고정 시간 단위로 버리면 중복 DTS 경고가 생긴다.
 decoded=subprocess.run(['ffmpeg','-v','error','-i',str(f),'-fps_mode','passthrough','-enc_time_base','1:1000000','-f','null','-'],capture_output=True,check=True)
 assert not decoded.stderr,decoded.stderr.decode()
 times=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','json',str(f)]))
 pts=[float(x['best_effort_timestamp_time']) for x in times['frames']]
 assert all(b>a for a,b in zip(pts,pts[1:])),f
 assert v['codec_name']=='h264' and v['width']==(1080 if 'compare' in f.name else 540)
 rows.append({'file':f.name,'seconds':float(d['format']['duration']),'frames':len(pts),'width':v['width'],'height':v['height'],'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'full_decode':'pass','monotonic_pts':True})
assert len(rows)==14
(P/'video-validation.json').write_text(json.dumps(rows,indent=2))
for target in re.findall(r'\]\(([^)]+)\)',(P/'README.md').read_text()):
 if '://' not in target:assert (P/target).exists(),target
for f in P.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
print('영상 14개 전체 디코딩·시각 순서·규격, 문서 링크, Python 문법 검사 통과')
