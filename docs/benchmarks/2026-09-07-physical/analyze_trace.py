"""전체 FrameMetrics와 같은 시각의 Perfetto 작업을 대조한다. 단위는 명시하지 않으면 ns."""
from pathlib import Path
import re,json,subprocess,csv,io,collections,os
D=Path(__file__).resolve().parent;R=Path(os.environ.get('INPUT','/private/tmp/zerolist-physical-traces'))
TP=os.environ.get('TRACE_PROCESSOR','/Users/yoonhb/.local/share/perfetto/prebuilts/trace_processor_shell-d29864d1ba3b3685')
def query(p,q):
 r=subprocess.run([TP,'query',str(p),q],capture_output=True,text=True,check=True)
 return list(csv.DictReader(io.StringIO(r.stdout)))
def overlap(a,b,c,d):return max(0,min(b,d)-max(a,c))
result={}
for p in sorted(R.glob('*.log')):
 if 'startup' in p.name:continue
 s=p.read_text();touch=[int(x) for x in re.findall(r'touch action=\d nano=(\d+)',s)]
 assert len(touch)==36,(p,len(touch))
 frames=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',l)} for l in s.splitlines() if 'frame intended=' in l]
 gfx=(R/(p.stem+'-gfx.txt')).read_text()
 cutoff=int(re.search(r'Uptime: (\d+)',gfx)[1])*1000000
 frames=[f for f in frames if f['intended']>=touch[0]-16666667 and f['intended']+f['total']<=cutoff]
 assert all(not f['first'] for f in frames)
 metric_keys=['total','deadline','gpu','unknown','layout','draw','sync','command','swap']
 def quantile(xs,q):return sorted(xs)[min(len(xs)-1,int((len(xs)-1)*q))]/1e6
 metrics={k:{'p50_ms':quantile([f[k] for f in frames],.5),'p95_ms':quantile([f[k] for f in frames],.95),'max_ms':max(f[k] for f in frames)/1e6} for k in metric_keys}
 late=[dict(f) for f in frames if f['total']>f['deadline']]
 gfx=(R/(p.stem+'-gfx.txt')).read_text();total=int(re.search(r'Total frames rendered: (\d+)',gfx)[1]);jank=int(re.search(r'Janky frames: (\d+)',gfx)[1])
 assert frames and total==len(frames),(p,total,len(frames))
 out={'metrics':metrics,'frames':len(frames),'late':len(late),'dropped':sum(f['dropped'] for f in frames),'gfx_frames':total,'frame_count_difference':len(frames)-total,'gfx_jank':jank,'gfx_jank_matches':jank==len(late),'late_frames':late,'late_ratio_percent':100*len(late)/len(frames)}
 lines=gfx.splitlines();header=next(i for i,l in enumerate(lines) if l.startswith('Flags,'))
 gfxrows={int(r['IntendedVsync']):r for r in csv.DictReader(lines[header:]) if (r.get('IntendedVsync') or '').isdigit()}
 for f in late:
  if f['intended'] in gfxrows:
   f['gfx_timeline_ms']={k:(int(v)-f['intended'])/1e6 for k,v in gfxrows[f['intended']].items() if k in ['HandleInputStart','AnimationStart','PerformTraversalsStart','DrawStart','SyncQueued','SyncStart','IssueDrawCommandsStart','SwapBuffers','FrameCompleted','GpuCompleted','SwapBuffersCompleted','CommandSubmissionCompleted','FrameDeadline']}
  f['from_first_touch_ms']=(f['intended']-touch[0])/1e6
  f['excess_ms']=(f['total']-f['deadline'])/1e6
 trace=R/(p.stem+'.trace')
 if trace.exists():
  clocks=query(trace,"SELECT ts,clock_value,clock_name FROM clock_snapshot WHERE clock_id=3 ORDER BY ts")
  assert clocks,(p,'MONOTONIC snapshot missing')
  out['clock_snapshots']=clocks
  common=" FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t USING(utid) JOIN process p USING(upid) WHERE p.name='zerolist.example' AND s.dur>0"
  slices=query(trace,'SELECT s.ts,s.dur,s.name,t.name thread,t.is_main_thread'+common)
  states=query(trace,"SELECT s.ts,s.dur,s.state,t.tid,t.name thread,t.is_main_thread FROM thread_state s JOIN thread t USING(utid) JOIN process p USING(upid) WHERE p.name='zerolist.example' AND s.dur>0 AND (t.is_main_thread=1 OR t.name IN ('RenderThread','mqt_v_js'))")
  out['trace_errors']=query(trace,"SELECT name,value,severity FROM stats WHERE value>0 AND severity IN ('error','data_loss')")
  for f in late:
   nearest=min(clocks,key=lambda c:abs(int(c['clock_value'])-f['intended']))
   offset=int(nearest['ts'])-int(nearest['clock_value'])
   a=f['intended']+offset;b=a+f['total'];f['trace_clock_offset_ns']=offset;ss=collections.defaultdict(float)
   for st in states:
    n=overlap(a,b,int(st['ts']),int(st['ts'])+int(st['dur']))
    if n:ss[('main' if st['is_main_thread']=='1' else st['thread']+'['+st['tid']+']')+':'+st['state']]+=n/1e6
   assert ss,(p,f['intended'],'no matching thread states after clock conversion')
   f['thread_states_ms']=dict(ss)
   matches=[x for x in slices if overlap(a,b,int(x['ts']),int(x['ts'])+int(x['dur']))]
   f['slices']=[dict(x,relative_ms=(int(x['ts'])-a)/1e6,duration_ms=int(x['dur'])/1e6) for x in matches if x['is_main_thread']=='1' or x['thread']=='RenderThread']
   f['mount_slices']=[x for x in matches if 'mount' in x['name'].lower() or 'CREATE' in x['name']]
  (R/(p.stem+'-slices.json')).write_text(json.dumps(slices,indent=2))
 result[p.stem]=out
(D/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for name,r in result.items():
 print(name,r['frames'],r['late'],round(r['late_ratio_percent'],3),'errors',r.get('trace_errors'))
 for f in r['late_frames']:
  if 'thread_states_ms' in f:print('late',f['intended'],'states',f['thread_states_ms'],'mounts',len(f['mount_slices']))
