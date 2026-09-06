"""시작 8초의 외부 메모리 표본. 관측 최고치이며 순간 피크를 보장하지 않는다."""
from pathlib import Path
import os,subprocess,time,re,json,random
D=Path(os.environ['OUT']);assert not D.exists();D.mkdir(parents=True)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554'];U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
def run(*args):return subprocess.check_output(args,stderr=subprocess.STDOUT,timeout=60).decode()
results=[]
for platform in ['ios','android']:
 if platform=='ios':run(*A,'shell','am','force-stop','zerolist.example')
 else:subprocess.run(['xcrun','simctl','terminate',U,'zerolist.example'],capture_output=True)
 for rep in range(2):
  engines=['zigpool','template-worklet','template-compact'];random.Random(870201+rep).shuffle(engines)
  for engine in engines:
   load_start=os.getloadavg();started=time.monotonic();epoch=time.time()
   if platform=='ios':
    env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_ENGINE=engine,SIMCTL_CHILD_ZL_COUNT='100000',SIMCTL_CHILD_ZL_CELL='heavy',SIMCTL_CHILD_ZL_BUFFER_ROWS='5',SIMCTL_CHILD_ZL_COMMON_AUDIT='0',SIMCTL_CHILD_ZL_AUDIT='0',SIMCTL_CHILD_ZL_PREPARATION_TRACE='0',SIMCTL_CHILD_ZL_BLOCK_MS='0',SIMCTL_CHILD_ZL_FRAMES='0',SIMCTL_CHILD_ZL_DIAGNOSTIC='normal',SIMCTL_CHILD_ZL_LEGACY='0')
    raw=subprocess.check_output(['xcrun','simctl','launch','--terminate-running-process',U,'zerolist.example'],env=env,stderr=subprocess.STDOUT).decode();pid=int(re.search(r'zerolist.example: (\d+)',raw)[1])
   else:
    run(*A,'shell','am','force-stop','zerolist.example')
    run(*A,'shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--ei','count','100000','--es','cell','heavy','--ei','bufferRows','5','--ei','jsBlockMs','0')
    pid=int(run(*A,'shell','pidof','zerolist.example').strip())
   samples=[]
   try:
    while time.monotonic()-started<8:
     before=time.monotonic()-started
     if platform=='ios':mib=int(run('ps','-o','rss=','-p',str(pid)).strip())/1024
     else:mib=int(re.search(r'TOTAL PSS:\s+(\d+)',run(*A,'shell','dumpsys','meminfo','zerolist.example'))[1])/1024
     samples.append({'begin_seconds':before,'end_seconds':time.monotonic()-started,'mib':mib});time.sleep(.1)
   finally:
    if platform=='ios':run('xcrun','simctl','terminate',U,'zerolist.example')
    else:run(*A,'shell','am','force-stop','zerolist.example')
   assert len(samples)>10
   row={'platform':platform,'engine':engine,'run':rep+1,'metric':'RSS' if platform=='ios' else 'PSS','epoch':epoch,'host_load_start':load_start,'host_load_end':os.getloadavg(),'samples':samples,'observed_peak_mib':max(s['mib'] for s in samples),'last_mib':samples[-1]['mib'],'count':100000,'cell':'heavy','block_ms':0,'duration_seconds':8,'audit':False}
   results.append(row);(D/'results.json').write_text(json.dumps(results,indent=2));print(platform,engine,rep+1,'최고',round(row['observed_peak_mib'],1),flush=True)
