import os
import subprocess,time,pathlib,re,json,statistics,hashlib
OUT=pathlib.Path(os.environ.get('OUT','/tmp/zerolist-large-heavy'))
OUT.mkdir(exist_ok=True)
ADB=os.environ.get('ADB','adb')
PKG='zerolist.example'
def adb(*args,binary=False):
 r=subprocess.run([ADB,'-s',os.environ.get('SERIAL','emulator-5554'),*args],capture_output=True,timeout=35)
 if r.returncode: raise RuntimeError(r.stderr.decode(errors='replace'))
 return r.stdout if binary else r.stdout.decode(errors='replace')
def counters(pid,engine):
 log=adb('logcat','-d','--pid='+pid,'-v','brief','ReactNativeJS:I','ZlPool:I','*:S')
 rows=re.findall(r'\[JS0\] '+engine+r' renders=(\d+) cbs=(\d+) mounts=(\d+) unmounts=(\d+)',log)
 return ([int(x) for x in rows[-1]] if rows else None),log
allrows=[]
engines=['flatlist','legend','flashlist','zigpool']
for rep in range(5):
 order=engines[rep%4:]+engines[:rep%4]
 for engine in order:
  name=f'{rep+1}-{engine}'
  adb('shell','am','force-stop',PKG)
  adb('shell','am','start','-W','-n',PKG+'/.SoloActivity','--es','engine',engine,'--ei','count',os.environ.get('COUNT','100000'),'--es','cell',os.environ.get('CELL','heavy'))
  time.sleep(3)
  pid=adb('shell','pidof',PKG).strip()
  if not pid: raise RuntimeError('No app process')
  base,_=counters(pid,engine)
  if base is None: raise RuntimeError('Missing engine readiness '+name)
  if rep==0:
   (OUT/(name+'-before.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
  adb('shell','dumpsys','gfxinfo',PKG,'reset')
  for i in range(4): adb('shell','input','swipe','540','1800','540','600','300')
  time.sleep(1.2)
  gfx=adb('shell','dumpsys','gfxinfo',PKG,'framestats')
  final,log=counters(pid,engine)
  (OUT/(name+'-gfx.txt')).write_text(gfx)
  (OUT/(name+'-log.txt')).write_text(log)
  if rep==0:
   (OUT/(name+'-after.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
   adb('shell','uiautomator','dump','/data/local/tmp/zerolist-window.xml')
   (OUT/(name+'-ui.xml')).write_text(adb('shell','cat','/data/local/tmp/zerolist-window.xml'))
  def match(p):
   m=re.search(p,gfx);return m.group(1) if m else None
  row={'run':rep+1,'engine':engine,'frames':match(r'Total frames rendered: (\d+)'),'jank_percent':match(r'Janky frames: \d+ \(([\d.]+)%\)'),'p50_ms':match(r'50th percentile: (\d+)ms'),'p95_ms':match(r'95th percentile: (\d+)ms'),'baseline':base,'final':final,'delta':([b-a for a,b in zip(base,final)] if final else None)}
  allrows.append(row)
  (OUT/'results.json').write_text(json.dumps(allrows,indent=2))
  print(json.dumps(row),flush=True)
summary={}
for e in engines:
 rows=[r for r in allrows if r['engine']==e]
 summary[e]={k:[r[k] for r in rows] for k in ['jank_percent','p50_ms','p95_ms','delta','frames']}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print('COMPLETE',flush=True)
