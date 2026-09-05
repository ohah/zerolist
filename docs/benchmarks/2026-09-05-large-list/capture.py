import os
import pathlib,subprocess,time,json,signal
P=pathlib.Path(os.environ.get('OUT','/tmp/zerolist-videos'))
P.mkdir(parents=True,exist_ok=True)
A=os.environ.get('ADB','adb'); base=[A,'-s',os.environ.get('SERIAL','emulator-5554')]
def adb(*a):return subprocess.check_output(base+list(a),timeout=40)
manifest=[]
for cell in ['complex','heavy']:
 for engine in ['flatlist','legend','flashlist','zigpool']:
  name=cell+'-'+engine
  adb('shell','am','force-stop','zerolist.example')
  adb('shell','am','start','-W','-n','zerolist.example/.SoloActivity','--es','engine',engine,'--ei','count',os.environ.get('COUNT','100000'),'--es','cell',cell)
  time.sleep(4)
  pid=adb('shell','pidof','zerolist.example').decode().strip()
  log=adb('logcat','-d','--pid='+pid,'ReactNativeJS:I','*:S').decode(errors='replace')
  if '[JS0] '+engine not in log:raise RuntimeError('Not ready: '+name)
  (P/(name+'-before.png')).write_bytes(adb('exec-out','screencap','-p'))
  device='/data/local/tmp/zl-'+name+'.mp4'
  proc=subprocess.Popen(base+['shell','screenrecord','--size','540x1200','--bit-rate','2500000','--time-limit','20',device],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  start=time.monotonic(); events=[]
  time.sleep(1.5)
  for y1,y2,dur in [(1800,600,500)]*2+[(1900,400,120)]*4+[(500,1900,150)]*3:
   events.append({'t':round(time.monotonic()-start,3),'from':[540,y1],'to':[540,y2],'duration_ms':dur})
   adb('shell','input','swipe','540',str(y1),'540',str(y2),str(dur))
   time.sleep(.45)
  time.sleep(1)
  (P/(name+'-after.png')).write_bytes(adb('exec-out','screencap','-p'))
  proc.communicate(timeout=30)
  if proc.returncode:raise RuntimeError('screenrecord failed: '+name)
  adb('pull',device,str(P/(name+'.mp4')))
  manifest.append({'engine':engine,'cell':cell,'count':int(os.environ.get('COUNT','100000')),'events':events,'video':name+'.mp4','note':'Separate recording run; not used for performance statistics. Screenrecord overhead and different scroll physics apply.'})
  (P/'capture-manifest.json').write_text(json.dumps(manifest,indent=2))
  print('CAPTURED '+name,flush=True)
