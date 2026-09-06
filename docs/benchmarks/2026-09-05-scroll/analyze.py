from pathlib import Path
import re,json,statistics,os
O=Path(os.environ.get('OUT','/private/tmp/zerolist-scroll'));result={}
for file in sorted(O.glob('*.log')):
 draw=[];frames=[];down=[];up=[];fling=[];compute=[]
 for line in file.read_text().splitlines():
  row={k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',line)}
  if 'phase=predraw' in line:draw.append(row)
  if 'phase=fling' in line:fling.append(row)
  if 'phase=compute' in line:compute.append(row)
  if 'frame intended=' in line:frames.append(row)
  if 'touch action=0' in line:down.append(row['nano'])
  if 'touch action=1' in line:up.append(row['nano'])
 if len(down)!=12 or len(up)!=12:raise RuntimeError(file.name)
 detail=[]
 for n,t in enumerate(down):
  before=[d for d in draw if d['nano']<t];after=[d for d in draw if d['nano']>=t]
  gap=(after[0]['nano']-before[-1]['nano'])/1e6 if before and after else None
  candidates=[f for f in frames if t-16666667<=f['intended']<=t+80000000]
  between=[d for d in draw if n>0 and up[n-1]<=d['nano']<t]
  resume_gaps=[(b['intended']-a['intended'])/1e6 for a,b in zip(frames,frames[1:]) if t<=b['intended']<=t+80000000]
  detail.append({'frame_gaps_over_25ms':sum(g>25 for g in resume_gaps),'max_frame_gap_ms':max(resume_gaps,default=None),'gesture':n+1,'draw_gap_ms':gap,'draws_after_previous_up':len(between),'positions_between':[d['y'] for d in between],'short_deadlines':sum(f['deadline']<20000000 for f in candidates),'late':sum(f['total']>f['deadline'] for f in candidates)})
 result[file.stem]={'frames':len(frames),'late':sum(f['total']>f['deadline'] for f in frames),'draws':len(draw),'gaps_over_25ms':sum(b['nano']-a['nano']>25000000 for a,b in zip(draw,draw[1:])),'fling_velocities':[f['velocity'] for f in fling],'compute_calls':len(compute),'gestures':detail}
 print(file.stem,'late',result[file.stem]['late'],'gaps',result[file.stem]['gaps_over_25ms'],'fling',result[file.stem]['fling_velocities'][:3])
 print(detail[:4])
(O/'analysis.json').write_text(json.dumps(result,indent=2))
