"""최종 Android 비교. 각 그룹은 순차 실행하고 실패 시 중단한다."""
from pathlib import Path
import os,subprocess,sys
D=Path(__file__).resolve().parent
root=Path(os.environ.get('BENCH_ROOT','/private/tmp/zerolist-android-focus-final'))
for cell in ['heavy','simple']:
 engines='flatlist-5,zerolist-5,flashlist-5,legend-5,zigpool-5'+(',zerolist-before-5' if cell=='heavy' else '')
 for mode,n in [('perf','3'),('audit','1')]:
  out=root/f'{cell}-{mode}';assert not out.exists(),out
  env=dict(os.environ,PLATFORM='android',CELL=cell,MODE=mode,REPEATS=n,BLOCK_MS='0',CONFIGS=engines,ORDER_SEED='870913',OUT=str(out),PYTHONUNBUFFERED='1')
  subprocess.run([sys.executable,'-I',str(D/'record.py')],env=env,check=True)
