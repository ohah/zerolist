"""시작40(+준비4), 스크롤40, 정확성4, Android 보조6회를 직렬 실행한다."""
from pathlib import Path
import subprocess,os,sys
D=Path(__file__).resolve().parent;prior=D.parent/'2026-09-06-worklet-memory'
root=Path(os.environ['OUT_ROOT']);assert not root.exists()
subprocess.run([sys.executable,'-I',str(D/'startup.py')],env=dict(os.environ,OUT=str(root/'startup')),check=True)
for platform in ['ios','android']:
 for mode,block,repeats in [('perf',0,5),('perf',160,5),('audit',160,1)]:
  env=dict(os.environ,PLATFORM=platform,MODE=mode,CELL='heavy',COUNT='100000',BLOCK_MS=str(block),REPEATS=str(repeats),CONFIGS='template-worklet-5,template-compact-5',ORDER_SEED='870206',DIAGNOSTIC='normal',OUT=str(root/f'{platform}-{mode}{block}'))
  subprocess.run([sys.executable,'-I',str(prior/'run_group.py')],env=env,check=True)
# 최초 84회에서 Android 점유 조건의 큰 지연이 관측되어 추가한 고정 6회 보조 비교.
# 주 비교 수치를 대체하거나 보조 결과와 합치지 않는다.
env=dict(os.environ,PLATFORM='android',MODE='perf',CELL='heavy',COUNT='100000',BLOCK_MS='160',REPEATS='3',CONFIGS='template-worklet-5,template-compact-5',ORDER_SEED='870207',DIAGNOSTIC='normal',OUT=str(root/'android-stress-followup'))
subprocess.run([sys.executable,'-I',str(prior/'run_group.py')],env=env,check=True)
