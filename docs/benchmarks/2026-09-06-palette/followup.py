"""추가 지연 검사 6회를 정식 192회와 분리해 보존한다. 최근 프레임만 진단한다."""
from pathlib import Path
import json,csv,math,statistics,zipfile,re
D=Path(__file__).resolve().parent;root=Path('/private/tmp/zerolist-palette-followup')
a=json.loads((root/'results.json').read_text());assert len(a)==6
for r in a:
 p=root/f"{r['run']}-{r['name']}"
 h=json.loads(p.with_name(p.name+'-host.json').read_text())
 r['host_load']=[x['load'][0] for x in h]
 r['external_build_processes']=[sum(x['name'] in ['zig','build','test'] for x in y['processes']) for y in h]
 raw=p.with_name(p.name+'-gfx.txt').read_text()
 lines=raw.split('---PROFILEDATA---')[1].strip().splitlines()
 frames=[{k:int(v) for k,v in x.items() if k and v} for x in csv.DictReader(lines)]
 frames=[f for f in frames if f['Flags']==0];stages={}
 for key,end,start in [('callback_wait','HandleInputStart','IntendedVsync'),('ui_work','SyncQueued','HandleInputStart'),('render_queue','SyncStart','SyncQueued'),('draw_commands','SwapBuffers','IssueDrawCommandsStart'),('complete_after_swap','FrameCompleted','SwapBuffers')]:
  vals=sorted((f[end]-f[start])/1e6 for f in frames if 0<=f[end]-f[start]<1e9)
  stages[key]=dict(valid_frames=len(vals),p95_ms=vals[math.ceil(len(vals)*.95)-1],max_ms=max(vals))
 r['recent_frame_stages']=dict(retained_frames=len(frames),stages=stages)
 r['gfx_diagnostics']={key:int(re.search(pattern,raw)[1]) for key,pattern in [('slow_ui',r'Number Slow UI thread: (\d+)'),('slow_issue_commands',r'Number Slow issue draw commands: (\d+)')]}
(D/'followup-results.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
for name,folder in [('followup',root),('startup-smoke',Path('/private/tmp/zerolist-palette-smoke-start'))]:
 with zipfile.ZipFile(D/f'{name}-raw.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in folder.iterdir():
   if p.is_file():z.write(p,p.name)
lines=['# Android 지연 추가 검사','',
'정식 비교에서 JS 점유 지연이 0.85% → 1.57%로 증가하여 두 워클릿만 순서 시드 870309로 3회씩 추가 검사했다. **이 6회를 정식 192회 평균에 합치거나 느린 실행을 제외하지 않았다.**','',
'| 회차 | 버전 | 지연 프레임 / 전체 | 지연 % | p95 ms | 호스트 부하 전→후 | 외부 빌드 프로세스 전→후 |','|---|---|---:|---:|---:|---:|---:|']
labels={'template-compact':'직전 워클릿','template-palette':'장식 통합 후보'}
for r in a:
 lines.append(f"| {r['run']} | {labels[r['engine']]} | {r['late']} / {r['frames']} | {r['late_percent']:.2f} | {r['p95_ms']} | {r['host_load'][0]:.1f} → {r['host_load'][1]:.1f} | {r['external_build_processes'][0]} → {r['external_build_processes'][1]} |")
lines+=['','## 최근 프레임 기록의 한계','',
'gfxinfo 상세 기록은 실행마다 최근 120프레임만 남았다. 전체 실행의 모든 지연을 재구성한 것이 아니다. 아래는 상세 기록에서 유효한 타임스탬프 차이의 p95이며, 마지막 열은 GPU 실행 시간 자체가 아니다. 실제 GPU 프로파일러나 운영체제 스케줄링 추적을 대신하지 않는다.','',
'| 회차·버전 | 콜백 시작 대기 ms | UI 작업 ms | 렌더 큐 대기 ms | 그리기 명령 ms | 스왑 이후 완료 ms |','|---|---:|---:|---:|---:|---:|']
for r in a:
 s=r['recent_frame_stages']['stages'];v=[s[k]['p95_ms'] for k in ['callback_wait','ui_work','render_queue','draw_commands','complete_after_swap']]
 lines.append(f"| {r['run']} {labels[r['engine']]} | "+' | '.join(f'{x:.2f}' for x in v)+' |')
lines+=['','후보 첫 실행의 큰 지연과 외부 빌드 34개가 같은 시점에 관측됐다. 최근 기록에서도 콜백 시작 대기와 렌더 큐 대기가 함께 늘었다. 그러나 외부 작업이 유일한 원인이라고 확정할 수 없으며 후보 자체의 회귀 가능성도 남는다. 직전 워클릿의 추가 2회차에도 렌더 큐·그리기 명령 구간의 큰 편차가 있었다.','',
'**판정: 시작·메모리 개선을 지연 안정성 해결로 확대 해석하지 않는다.** 실물 기기의 통제된 부하와 전체 구간 시스템 추적이 필요하다.','',
'재현: `PLATFORM=android MODE=perf BLOCK_MS=160 REPEATS=3 CONFIGS=template-compact-5,template-palette-5 ORDER_SEED=870309 DIAGNOSTIC=normal OUT=<새 경로> python3 -I docs/benchmarks/2026-09-06-palette/run_group.py`','']
(D/'followup-ko.md').write_text('\n'.join(lines));print('추가 6회 보존 완료')
