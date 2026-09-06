"""탐색과 다른 순서로 재검증. iOS는 기존 선행 준비와 보정을 분리 비교한다."""
import os,sys,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent
selection={'ios':'zigpool-5,legend-5,stable-5,pending-stable-5,stable-12,pending-stable-12','android':'zigpool-5,legend-5,pending-stable-5'}
for platform,configs in selection.items():
 if platform=='android':
  subprocess.run(['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554','shell','settings','put','system','user_rotation','0'],check=True)
 for mode,block in [('audit',160),('perf',0),('perf',160)]:
  out=f'/private/tmp/zerolist-readiness-confirm-{platform}-{mode}-{block}'
  print('START',out,flush=True)
  env=dict(os.environ,PLATFORM=platform,CONFIGS=configs,MODE=mode,BLOCK_MS=str(block),REPEATS='3',ORDER_SEED='870604',OUT=out)
  subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
  print('DONE',out,flush=True)
