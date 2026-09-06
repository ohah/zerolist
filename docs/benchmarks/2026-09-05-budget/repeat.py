"""최초 전체 탐색 종료 후 선택한 설정을 반복. 항상 새 출력 디렉터리를 사용한다."""
from pathlib import Path
import os,subprocess,json
D=Path(__file__).resolve().parent;selection=json.loads((D/'selection.json').read_text())
root=Path(os.environ.get('REPEAT_ROOT','/private/tmp/zerolist-budget-repeat'))
for platform,chosen in selection.items():
 for mode,block,repeats in [('perf',0,3),('audit',160,2),('perf',160,2)]:
  name=f'{platform}-{mode}-{block}';out=Path(str(root)+'-'+name)
  env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS=str(block),REPEATS=str(repeats),CONFIGS=','.join(chosen['configs']),OUT=str(out))
  with Path(str(out)+'-progress.log').open('w') as log:
   subprocess.run(['python3','-I',str(D/'record.py')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  print(name,'반복 완료',flush=True)
