"""같은 일반 셀 5종 정상 부하: 비용 60회, 화면 검사 20회. 시작 시간 측정 아님."""
from pathlib import Path
import os,subprocess,sys
D=Path(__file__).resolve().parent;root=Path(os.environ['OUT_ROOT']);assert not root.exists()
for platform in ['android','ios']:
 for cell in ['simple','heavy']:
  for mode,repeats in [('audit',1),('perf',3)]:
   env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS='0',REPEATS=str(repeats),CELL=cell,COUNT='100000',ORDER_SEED='870907',CONFIGS='flatlist-5,zerolist-5,flashlist-5,legend-5,zigpool-5',DIAGNOSTIC='normal',OUT=str(root/f'{platform}-{cell}-{mode}'))
   subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
