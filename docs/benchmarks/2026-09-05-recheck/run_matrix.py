"""같은 바이너리에서 117회 독립 재측정. 기존 결과를 덮어쓰지 않는다."""
from pathlib import Path
import os,subprocess,json,re,stat,time
D=Path(__file__).resolve().parent
selection={'android':'flatlist-5,flashlist-2,flashlist-5,legend-5,zerolist-5,zigpool-5','ios':'flatlist-5,flashlist-5,flashlist-12,legend-5,zerolist-5,zigpool-5,stable-12'}
groups=[]
for platform,configs in selection.items():
 for mode,block in [('perf',0),('audit',160),('perf',160)]:
  out=Path(f'/private/tmp/zerolist-recheck-{platform}-{mode}-{block}');assert not out.exists(),out
  env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS=str(block),REPEATS='3',CONFIGS=configs,OUT=str(out),PYTHONUNBUFFERED='1',ORDER_SEED='870102')
  print('START',out,flush=True)
  for attempt in range(3):
   result=subprocess.run(['python3','-I',str(D/'record.py')],env=env)
   if result.returncode==0:break
   # 앱이 시작되지 않은 simctl FIFO 충돌만 복구한다. 계측 실패는 건너뛰지 않는다.
   fixed=False
   for log in out.glob('*.log'):
    match=re.search(r'Unable to establish FIFO at (.+/launch_console-(\d+)-\d+): Error 17',log.read_text())
    if not match:continue
    fifo=Path(match[1])
    if fifo.exists() and stat.S_ISFIFO(fifo.lstat().st_mode) and subprocess.run(['ps','-p',match[2]],capture_output=True).returncode!=0:
     fifo.rename(fifo.with_name(fifo.name+'-recheck-stale-'+str(time.time_ns())));fixed=True
   if not fixed:raise RuntimeError(('measurement failed',out,result.returncode))
   if not (out/'results.json').exists():(out/'results.json').write_text('[]\n')
   env['RESUME']='1';print('RETRY inactive FIFO collision',out,flush=True)
  else:raise RuntimeError(('retry exhausted',out))
  groups.append(str(out));print('DONE',out,flush=True)
subprocess.run(['python3','-I',str(D/'collect.py'),*groups],check=True)
subprocess.run(['python3','-I',str(D/'analyze.py')],check=True)
