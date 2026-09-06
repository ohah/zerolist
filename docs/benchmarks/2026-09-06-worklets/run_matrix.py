"""동일 바이너리: 양쪽 플랫폼을 직렬로 측정하고 원시 결과를 보존한다."""
from pathlib import Path
import subprocess,os,sys
D=Path(__file__).resolve().parent
root=Path(os.environ['OUT_ROOT']);assert not root.exists(),root
for platform in ['ios','android']:
 for mode,block in [('audit',160),('perf',0),('perf',160)]:
  env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS=str(block),REPEATS='3',CONFIGS='zigpool-5,template-js-5,template-worklet-5',OUT=str(root/f'{platform}-{mode}{block}'))
  subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
