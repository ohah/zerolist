"""프로세스를 새로 시작하여 두 워클릿의 시작 경로를 교대 비교한다.
첫 내용 확인은 네이티브 뷰 검사이며 실제 패널 표시 시각은 아니다.
"""
from pathlib import Path
import subprocess,os,time,json,re,stat
D=Path(os.environ['OUT']);assert not D.exists();D.mkdir(parents=True)
A=['/Users/yoonhb/Library/Android/sdk/platform-tools/adb','-s','emulator-5554']
U='ACA7BF91-E2D5-4CF7-909A-08D1AD95FF3D'
N=int(os.getenv('REPEATS','10'));results=[]
def run(*a):return subprocess.check_output(a,stderr=subprocess.STDOUT,timeout=60).decode()
def stop(platform):
 if platform=='android':run(*A,'shell','am','force-stop','zerolist.example')
 else:subprocess.run(['xcrun','simctl','terminate',U,'zerolist.example'],capture_output=True,timeout=30)
def host():
 rows=[]
 for line in run('ps','-axo','pid=,pcpu=,comm=').splitlines():
  v=line.strip().split(None,2)
  if len(v)==3 and float(v[1])>=5:rows.append({'pid':int(v[0]),'cpu_percent':float(v[1]),'name':Path(v[2]).name})
 return {'epoch':time.time(),'load':os.getloadavg(),'processes':rows}
for platform in ['ios','android']:
 stop('android' if platform=='ios' else 'ios')
 for rep in range(N+1):
  engines=['template-worklet','template-compact']
  if rep%2:engines.reverse()
  for engine in engines:
   stop(platform);name=f'{platform}-{rep}-{engine}';before=host()
   log=D/f'{name}.log';launch=None
   if platform=='android':run(*A,'logcat','-c')
   with log.open('w') as output:
    if platform=='android':
     reader=subprocess.Popen(A+['logcat','-v','brief','ZlStartup:I','ZlCommon:I','ReactNativeJS:I','*:S'],stdout=output,stderr=subprocess.STDOUT)
     start=time.monotonic()
     launch=subprocess.Popen(A+['shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--ei','bufferRows','5','--ei','count','100000','--es','cell','heavy','--ei','jsBlockMs','0','--ez','commonAudit','true','--es','diagnostic','trace-startup'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    else:
     env=dict(os.environ,SIMCTL_CHILD_ZL_SOLO='1',SIMCTL_CHILD_ZL_DIAGNOSTIC='trace-startup',SIMCTL_CHILD_ZL_ENGINE=engine,SIMCTL_CHILD_ZL_COUNT='100000',SIMCTL_CHILD_ZL_CELL='heavy',SIMCTL_CHILD_ZL_BUFFER_ROWS='5',SIMCTL_CHILD_ZL_COMMON_AUDIT='1',SIMCTL_CHILD_ZL_AUDIT='0',SIMCTL_CHILD_ZL_FRAMES='0',SIMCTL_CHILD_ZL_BLOCK_MS='0',SIMCTL_CHILD_ZL_PREPARATION_TRACE='0',SIMCTL_CHILD_ZL_DELAY='0',SIMCTL_CHILD_ZL_LEGACY='0')
     start=time.monotonic()
     reader=subprocess.Popen(['xcrun','simctl','launch','--console',U,'zerolist.example'],env=env,stdout=output,stderr=subprocess.STDOUT)
    try:
     for attempt in range(3):
      while time.monotonic()-start<20:
       raw=log.read_text()
       if 'phase=content_ready' in raw and 'phase=data_ready' in raw:break
       if reader.poll() is not None:break
       time.sleep(.02)
      else:raise RuntimeError(('startup timeout',name))
      if 'phase=content_ready' in raw and 'phase=data_ready' in raw:break
      # iOS 콘솔 연결 전의 정확한 FIFO 충돌만 복구한다. 앱 시작 이후 실패는 재시도하지 않는다.
      m=re.search(r'Unable to establish FIFO at (.+/launch_console-(\d+)-\d+): Error 17',raw)
      if platform!='ios' or not m or 'phase=native_start' in raw:raise RuntimeError(('launch failed',name))
      fifo=Path(m[1]);assert fifo.exists() and stat.S_ISFIFO(fifo.lstat().st_mode)
      assert subprocess.run(['ps','-p',m[2]],capture_output=True).returncode!=0
      fifo.rename(fifo.with_name(fifo.name+'-startup-stale-'+str(time.time_ns())))
      (D/f'{name}-console-attempt-{attempt}.log').write_text(raw)
      output.seek(0);output.truncate();start=time.monotonic()
      reader=subprocess.Popen(['xcrun','simctl','launch','--console',U,'zerolist.example'],env=env,stdout=output,stderr=subprocess.STDOUT)
     else:raise RuntimeError('FIFO retries exhausted')
     observed_ms=(time.monotonic()-start)*1000
     time.sleep(.6)
    finally:
     stop(platform)
     if platform=='android':reader.terminate()
     reader.wait(timeout=15)
     if launch:
      launch_text=launch.communicate(timeout=15)[0].decode();assert launch.returncode==0
      (D/f'{name}-launch.txt').write_text(launch_text)
   raw=log.read_text();phases={}
   for line in raw.splitlines():
    if 'ZlStartup' in line:
     phase=re.search(r'phase=(\w+)',line)[1]
     assert phase not in phases,(name,phase)
     phases[phase]={k:float(v) for k,v in re.findall(r'(wall|ms)=([\d.]+)',line)}
   assert set(phases)=={'native_start','render_begin','data_ready','content_ready'},(name,phases)
   origin=phases['native_start']['wall']
   values={p:phases[p]['wall']-origin for p in ['render_begin','data_ready']}
   values['content_ready']=phases['content_ready']['ms']
   assert all(0<=v<15000 for v in values.values()),(name,values)
   audits=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',line)} for line in raw.splitlines() if 'ZlCommon' in line and 'frame=' in line]
   assert audits and '[ZlRuntime] rn=0.87.1' in raw
   row={'platform':platform,'engine':engine,'run':rep,'warmup':rep==0,'milliseconds':values,'data_and_content_ms':max(values['data_ready'],values['content_ready']),'command_to_log_observed_ms':observed_ms,'audit_frames':len(audits),'wrong_frames':sum(f['wrong']>0 for f in audits),'overlap_frames':sum(f['overlap']>2 for f in audits),'host_before':before,'host_after':host()}
   results.append(row);(D/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
   print(name,{k:round(v,1) for k,v in values.items()},flush=True)
