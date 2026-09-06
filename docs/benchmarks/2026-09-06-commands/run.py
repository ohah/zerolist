"""갱신 경로 3종 집중 비교: 시작30 + 평상시30 + JS 점유60 + 화면검사18 = 138회."""
from pathlib import Path
import os,subprocess,sys
D=Path(__file__).resolve().parent;root=Path(os.environ['OUT_ROOT']);assert not root.exists()
subprocess.run([sys.executable,'-I',str(D/'startup.py')],env=dict(os.environ,OUT=str(root/'startup'),REPEATS='5'),check=True)
for platform in ['android','ios']:
 for mode,block,repeats in [('audit',160,3),('perf',0,5),('perf',160,10)]:
  env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS=str(block),REPEATS=str(repeats),CELL='heavy',COUNT='100000',ORDER_SEED='870611',CONFIGS='template-palette-5,template-palette-command-5,template-command-5',DIAGNOSTIC='normal',OUT=str(root/f'{platform}-{mode}{block}'))
  subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
