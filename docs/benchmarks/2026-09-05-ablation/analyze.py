"""Derive medians and full-window FrameMetrics summaries from checked-in raw data.
Run from any directory. Requires Pillow only for PNG output.
TOTAL_DURATION and DEADLINE are compared per frame; do not sum overlapping stages.
"""
from pathlib import Path
import json, re, statistics as stats, zipfile
from PIL import Image, ImageDraw, ImageFont
P = Path(__file__).resolve().parent
NAMES = {'flatlist':'FlatList','legend':'LegendList','flashlist':'FlashList','zerolist':'기존 ZeroList','zigpool':'ZigPool','zigpool-freeze-content':'ZigPool: 내용 고정','zigpool-freeze-position':'ZigPool: 위치 고정','zigpool-keep-alive':'ZigPool: 그리기 유지'}
FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
def font(n):
    try: return ImageFont.truetype(FONT,n)
    except OSError: return ImageFont.load_default()
summary = {}
for kind in ['main','cadence-main']:
    path = P / f'results-{kind}.json'
    if not path.exists(): continue
    rows = json.loads(path.read_text())
    summary[kind] = []
    for variant in dict.fromkeys(r['variant'] for r in rows):
        rs = [r for r in rows if r['variant'] == variant]
        out = {'variant':variant,'runs':len(rs)}
        for key in ['frames','jank_count','jank_percent','p50_ms','p95_ms','slow_ui','slow_draw']:
            vals=[r[key] for r in rs]
            out[key]={'median':stats.median(vals),'min':min(vals),'max':max(vals)}
        out['delta_median']=[stats.median(r['delta'][i] for r in rs) for i in range(4)]
        summary[kind].append(out)
(P/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
trace_summary={}
traces={}
for kind in ['trace','cadence-trace']:
    path = P / f'raw-{kind}.zip'
    if not path.exists(): continue
    trace_summary[kind]=[]
    with zipfile.ZipFile(path) as z:
        for name in sorted(z.namelist()):
            if not name.endswith('-log.txt'): continue
            frames=[]; downs=[]; ups=[]
            for line in z.read(name).decode().splitlines():
                if 'ZlFrame' not in line: continue
                d={k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
                if 'frame intended=' in line: frames.append(d)
                if 'touch action=' in line: (downs if d['action']==0 else ups).append(d['nano'])
            if not downs or not ups: raise RuntimeError('No touch window: '+name)
            t0=downs[0]; end=ups[-1]+1_200_000_000
            # Intended VSYNC can precede the input dispatch within the same refresh.
            fs=[f for f in frames if t0-16_666_667<=f['intended']<=end and f['first']==0]
            late=[f for f in fs if f['deadline']>0 and f['total']>f['deadline']]
            variant=name[2:-8]
            details=[]
            for f in late:
                prev=[p for p in frames if p['intended']<f['intended']]
                down=[t for t in downs if t<=f['intended']]
                details.append({'t_ms':(f['intended']-t0)/1e6,'total_ms':f['total']/1e6,'deadline_ms':f['deadline']/1e6,'previous_frame_gap_ms':(f['intended']-prev[-1]['intended'])/1e6 if prev else None,'after_down_ms':(f['intended']-down[-1])/1e6 if down else None})
            trace_summary[kind].append({'variant':variant,'frames':len(fs),'late':len(late),'window_start_before_down_ms':16.666667,'window_end_after_up_ms':1200,'dropped_callbacks':sum(f['dropped'] for f in frames),'late_frames':details,'median_all_ms':{k:stats.median(f[k] for f in fs)/1e6 for k in ['total','deadline','gpu','layout','draw','sync','command','swap','unknown']}})
            traces[(kind,variant)]=(fs,downs,t0)
(P/'trace-summary.json').write_text(json.dumps(trace_summary,indent=2)+'\n')
# Five functional lists only: independent-run medians, min/max whiskers.
rs=summary['main'][:5]
im=Image.new('RGB',(1320,620),'#101827'); d=ImageDraw.Draw(im)
d.text((30,20),'10만 항목 · 고부하 셀 | 안드로이드 에뮬레이터 | 5회 측정',font=font(29),fill='white')
d.text((30,65),'지연 프레임 비율(%) · 중앙값과 최소~최대 · 녹화 및 추적 없이 측정',font=font(21),fill='#cbd5e1')
left=290; scale=51
for i,r in enumerate(rs):
    y=130+i*76; v=r['jank_percent']; x=left+v['median']*scale
    d.text((30,y+9),NAMES[r['variant']],font=font(24),fill='white')
    d.rectangle((left,y,x,y+38),fill='#f59e0b' if r['variant']=='zerolist' else '#38bdf8')
    lo=left+v['min']*scale; hi=left+v['max']*scale
    d.line((lo,y+19,hi,y+19),fill='white',width=2)
    for xx in [lo,hi]: d.line((xx,y+11,xx,y+27),fill='white',width=2)
    d.text((max(x,hi)+15,y+5),f"{v['median']:.2f}%   p95 {r['p95_ms']['median']}밀리초",font=font(22),fill='white')
d.text((30,535),'기존 ZeroList도 GPU로 화면을 그립니다. 구형 태블릿의 실제 성능은 확인하지 않았습니다.',font=font(20),fill='#cbd5e1')
d.text((30,575),'p95: 프레임의 95%가 이 시간 안에 끝났다는 기준값입니다.',font=font(20),fill='#cbd5e1')
im.save(P/'metrics.png')
# Full-window frames, with gesture-start lines. Red = per-frame deadline missed.
keys=[k for k in traces if k[0]=='trace' and k[1] in ['flatlist','zerolist','zigpool','zigpool-freeze-content']]
keys += [k for k in traces if k[0]=='cadence-trace']
im=Image.new('RGB',(1400,140+155*len(keys)),'#101827'); d=ImageDraw.Draw(im)
d.text((25,16),'별도 프레임 추적: 프레임 처리 시간과 손가락 동작 시작 시점',font=font(27),fill='white')
d.text((25,58),'파랑: 마감시간 충족 · 빨강: 마감 초과 · 회색 세로선: 터치 시작 · 세로축: 0~110밀리초',font=font(20),fill='#cbd5e1')
for i,key in enumerate(keys):
    fs,downs,t0=traces[key]; top=110+i*155; base=top+116; left=330; width=1020; seconds=5.6
    label=NAMES[key[1]]+(' [2단계]' if key[0]=='cadence-trace' else '')
    d.text((20,top+15),label,font=font(20),fill='white')
    late=sum(f['total']>f['deadline']>0 for f in fs)
    d.text((20,top+48),f'지연 {late}개 / 전체 {len(fs)}프레임',font=font(19),fill='#cbd5e1')
    d.line((left,base,left+width,base),fill='#64748b')
    for t in downs:
        x=left+(t-t0)/1e9/seconds*width
        d.line((x,top,x,base),fill='#334155')
    for f in sorted(fs, key=lambda frame: frame['total']>frame['deadline']>0):
        x=left+(f['intended']-t0)/1e9/seconds*width
        y=base-min(110,f['total']/1e6)
        miss=f['total']>f['deadline']>0
        radius=4 if miss else 2
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill='#fb7185' if miss else '#38bdf8')
    for t in range(6): d.text((left+t/seconds*width,base+5),f'{t}초',font=font(15),fill='#94a3b8')
im.save(P/'trace-timeline.png')
print(json.dumps({k:[(r['variant'],r['jank_percent']['median']) for r in v] for k,v in summary.items()}))
