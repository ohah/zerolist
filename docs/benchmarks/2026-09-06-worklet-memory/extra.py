"""주 측정 이후 단순 셀 확인 4회와 시작 메모리 관측 12회를 직렬 실행한다."""
from pathlib import Path
import os,subprocess,sys
D=Path(__file__).resolve().parent;root=Path(os.environ['OUT_ROOT']);assert not root.exists()
for platform in ['ios','android']:
 env=dict(os.environ,PLATFORM=platform,MODE='audit',CELL='simple',COUNT='100000',BLOCK_MS='160',REPEATS='1',CONFIGS='template-worklet-5,template-compact-5',OUT=str(root/f'{platform}-simple'))
 subprocess.run([sys.executable,'-I',str(D/'run_group.py')],env=env,check=True)
subprocess.run([sys.executable,'-I',str(D/'startup.py')],env=dict(os.environ,OUT=str(root/'startup')),check=True)
