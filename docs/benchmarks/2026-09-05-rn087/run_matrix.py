"""RN 0.87.1 비교: Android 5개·iOS 6개 설정, 3종 조건, 각 3회."""
from pathlib import Path
import os,subprocess,json
D=Path(__file__).resolve().parent
selection={'android':'flatlist-5,flashlist-2,legend-5,zerolist-5,zigpool-5','ios':'flatlist-5,flashlist-12,legend-5,zerolist-5,zigpool-5,stable-12'}
groups=[]
for platform,configs in selection.items():
 for mode,block in [('perf',0),('audit',160),('perf',160)]:
  out=Path(f'/private/tmp/zerolist-rn087-{platform}-{mode}-{block}')
  if platform not in os.getenv('PLATFORMS','android,ios').split(','):
   c=json.loads((out/'conditions.json').read_text());r=json.loads((out/'results.json').read_text())
   assert len(r)==len(c['configs'])*c['repeats'],out
   groups.append(str(out));continue
  assert not out.exists(),out
  env=dict(os.environ,PLATFORM=platform,MODE=mode,BLOCK_MS=str(block),REPEATS='3',CONFIGS=configs,OUT=str(out),PYTHONUNBUFFERED='1')
  print('START',out,flush=True)
  subprocess.run(['python3','-I',str(D/'record.py')],env=env,check=True)
  groups.append(str(out))
  print('DONE',out,flush=True)
subprocess.run(['python3','-I',str(D/'collect.py'),*groups],check=True)
subprocess.run(['python3','-I',str(D/'analyze.py')],check=True)
