"""8개 엔진, 두 플랫폼. 시작48 + 비용96 + 화면검사48 = 정식192회."""
from pathlib import Path
import os,subprocess,sys
D=Path(__file__).resolve().parent;root=Path(os.environ['OUT_ROOT']);assert not root.exists()
subprocess.run([sys.executable,'-I',str(D/'startup.py')],env=dict(os.environ,OUT=str(root/'startup'),REPEATS='3'),check=True)
for platform in ['ios','android']:
 for mode,block in [('audit',160),('perf',0),('perf',160)]:
  env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS=str(block),REPEATS='3',CELL='heavy',COUNT='100000',ORDER_SEED='870307',CONFIGS='flatlist-5,flatlist-palette-5,zerolist-5,flashlist-5,legend-5,zigpool-5,template-compact-5,template-palette-5',DIAGNOSTIC='normal',OUT=str(root/f'{platform}-{mode}{block}'))
  subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
