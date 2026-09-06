"""본 비교 이후 수신 경로·simple 셀·데이터 크기를 별도로 확인한다."""
from pathlib import Path
import subprocess,os,sys
D=Path(__file__).resolve().parent
root=Path(os.environ['OUT_ROOT']);assert not root.exists(),root
for platform in ['ios','android']:
 for name,mode,cell,count,block,diagnostic,configs in [
  ('trace','audit','heavy',100000,160,'trace-binding','zigpool-5,template-js-5,template-worklet-5'),
  ('simple','audit','simple',100000,160,'normal','template-js-5,template-worklet-5'),
  ('10k','perf','heavy',10000,0,'normal','zigpool-5,template-js-5,template-worklet-5')]:
  env=dict(os.environ,PLATFORM=platform,MODE=mode,CELL=cell,COUNT=str(count),BLOCK_MS=str(block),DIAGNOSTIC=diagnostic,REPEATS='1',CONFIGS=configs,OUT=str(root/f'{platform}-{name}'))
  subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
