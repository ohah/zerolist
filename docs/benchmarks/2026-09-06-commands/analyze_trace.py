"""Perfetto 진단 원본의 앱 프레임·스레드·뷰 작업을 조회한다. 정량 점수와 분리."""
from pathlib import Path
import subprocess,json,csv,io,os
D=Path(__file__).resolve().parent;R=Path('/private/tmp/zerolist-command-traces')
TP=os.environ.get('TRACE_PROCESSOR','/Users/yoonhb/.local/share/perfetto/prebuilts/trace_processor_shell-d29864d1ba3b3685')
queries={
 'frame_timeline': """SELECT a.jank_type,a.present_type,a.on_time_finish,count(*) n,
 avg(a.dur)/1e6 avg_ms,max(a.dur)/1e6 max_ms
 FROM actual_frame_timeline_slice a JOIN process p USING(upid)
 WHERE p.name='zerolist.example' AND a.dur>0 GROUP BY 1,2,3""",
 'thread_states': """SELECT t.name,t.is_main_thread,s.state,count(*) n,
 sum(s.dur)/1e6 total_ms,max(s.dur)/1e6 max_ms
 FROM thread_state s JOIN thread t USING(utid) JOIN process p USING(upid)
 WHERE p.name='zerolist.example' AND s.dur>0
 AND (t.is_main_thread=1 OR t.name IN ('RenderThread','mqt_js')) GROUP BY 1,2,3""",
 'view_slices': """SELECT t.name thread_name,t.is_main_thread,s.name slice_name,count(*) n,
 avg(s.dur)/1e6 avg_ms,max(s.dur)/1e6 max_ms
 FROM slice s JOIN thread_track tt ON s.track_id=tt.id
 JOIN thread t USING(utid) JOIN process p USING(upid)
 WHERE p.name='zerolist.example' AND s.dur>0
 GROUP BY 1,2,3 ORDER BY max_ms DESC LIMIT 40""",
 'late_frame_main_states': """SELECT a.jank_type,s.state,count(*) overlaps,
 sum(min(a.ts+a.dur,s.ts+s.dur)-max(a.ts,s.ts))/1e6 overlapping_ms
 FROM actual_frame_timeline_slice a JOIN process p USING(upid)
 JOIN thread t USING(upid) JOIN thread_state s USING(utid)
 WHERE p.name='zerolist.example' AND t.is_main_thread=1
 AND a.jank_type LIKE '%App Deadline Missed%' AND a.dur>0 AND s.dur>0
  AND s.ts<a.ts+a.dur AND s.ts+s.dur>a.ts GROUP BY 1,2""",
 'slow_slice_states': """SELECT t.name thread_name,t.is_main_thread,s.name slice_name,
 s.ts,s.dur/1e6 wall_ms,
 (SELECT sum(min(s.ts+s.dur,st.ts+st.dur)-max(s.ts,st.ts))/1e6
 FROM thread_state st WHERE st.utid=t.utid AND st.dur>0 AND st.state='Running'
 AND st.ts<s.ts+s.dur AND st.ts+st.dur>s.ts) running_ms,
 (SELECT sum(min(s.ts+s.dur,st.ts+st.dur)-max(s.ts,st.ts))/1e6
 FROM thread_state st WHERE st.utid=t.utid AND st.dur>0 AND st.state IN ('R','R+')
 AND st.ts<s.ts+s.dur AND st.ts+st.dur>s.ts) runnable_ms,
 (SELECT sum(min(s.ts+s.dur,st.ts+st.dur)-max(s.ts,st.ts))/1e6
 FROM thread_state st WHERE st.utid=t.utid AND st.dur>0 AND st.state='S'
 AND st.ts<s.ts+s.dur AND st.ts+st.dur>s.ts) sleeping_ms
 FROM slice s JOIN thread_track tt ON s.track_id=tt.id
 JOIN thread t USING(utid) JOIN process p USING(upid)
 WHERE p.name='zerolist.example' AND s.dur>16000000
 AND (t.is_main_thread=1 OR t.name='RenderThread') ORDER BY s.dur DESC LIMIT 12""",
 'trace_errors': "SELECT name,value,severity FROM stats WHERE value>0 AND severity IN ('error','data_loss')",
}
result={}
for p in sorted(R.glob('*.perfetto-trace')):
 result[p.stem]={}
 for name,sql in queries.items():
  out=subprocess.run([TP,'query',str(p),sql],capture_output=True,text=True,check=True)
  result[p.stem][name]=list(csv.DictReader(io.StringIO(out.stdout)))
  (R/f'{p.stem}-{name}.csv').write_text(out.stdout)
 assert result[p.stem]['frame_timeline'],(p,'앱 프레임 누락')
 assert result[p.stem]['thread_states'],(p,'앱 스레드 누락')
(D/'trace-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(D/'trace-queries.json').write_text(json.dumps(queries,indent=2))
print('진단 추적 3종 분석 완료')
