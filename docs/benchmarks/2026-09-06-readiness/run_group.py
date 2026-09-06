"""그룹 실행. 실행 전 simctl FIFO 충돌만 복구하며 계측 실패는 중단한다."""
import os, subprocess, sys, re, stat, time
from pathlib import Path
D=Path(__file__).resolve().parent
out=Path(os.environ['OUT']);assert not out.exists(),out
env=dict(os.environ,PYTHONUNBUFFERED='1')
for attempt in range(3):
 result=subprocess.run([sys.executable,'-I',str(D/'record.py')],env=env)
 if result.returncode==0:break
 fixed=False
 for log in out.glob('*.log'):
  match=re.search(r'Unable to establish FIFO at (.+/launch_console-(\d+)-\d+): Error 17',log.read_text())
  if not match:continue
  fifo=Path(match[1])
  if fifo.exists() and stat.S_ISFIFO(fifo.lstat().st_mode) and subprocess.run(['ps','-p',match[2]],capture_output=True).returncode!=0:
   fifo.rename(fifo.with_name(fifo.name+'-readiness-stale-'+str(time.time_ns())));fixed=True
 if not fixed:raise RuntimeError(('measurement failed',out,result.returncode))
 if not (out/'results.json').exists():(out/'results.json').write_text('[]\n')
 env['RESUME']='1'
else:raise RuntimeError('FIFO retries exhausted')
