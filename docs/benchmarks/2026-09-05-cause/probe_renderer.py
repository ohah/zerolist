"""그래픽 백엔드만 바꾸는 교차 실험. 종료 시 원래 시스템 설정을 복원한다."""
from pathlib import Path
import subprocess,os,json,shlex
P=Path(__file__).resolve().parent;O=Path(os.environ.get('OUT','/private/tmp/zerolist-renderer-confirm'));O.mkdir(parents=True,exist_ok=True)
A=[os.environ.get('ADB','/Users/yoonhb/Library/Android/sdk/platform-tools/adb')];key='debug.hwui.renderer'
old=subprocess.check_output(A+['shell','getprop',key],text=True).strip();rows=[]
try:
 for n,renderer in enumerate(['skiagl','skiavk','skiavk','skiagl','skiagl','skiavk'],1):
  subprocess.run(A+['shell','setprop',key,renderer],check=True)
  out=O/(str(n)+'-'+renderer)
  env=dict(os.environ,ADB=A[0],VARIANTS='zigpool',REPEATS='1',TRACE='1',OUT=str(out))
  subprocess.run(['python3',str(P.parent/'2026-09-05-sync/measure_android.py')],env=env,check=True)
  result=json.loads((out/'results.json').read_text())[0];result['renderer']=renderer;result['sequence']=n;rows.append(result)
  (O/'results.json').write_text(json.dumps(rows,indent=2))
finally:
 subprocess.run(A+['shell','setprop',key,shlex.quote(old)],check=True)
 (O/'restored-renderer.txt').write_text(subprocess.check_output(A+['shell','getprop',key],text=True))
