-- 그래픽 추적은 계측 대상 동작을 바꾼다. 아래 시간을 정상 성능 점수로 사용하지 않는다.
SELECT name, count(*) n, avg(dur)/1e6 average_ms, max(dur)/1e6 max_ms
FROM slice WHERE name = 'ZL.reposition' GROUP BY name;
SELECT jank_type, present_type, on_time_finish, count(*) n
FROM actual_frame_timeline_slice GROUP BY 1,2,3;
SELECT t.name thread_name, s.name, count(*) n, avg(s.dur)/1e6 average_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t USING(utid)
WHERE t.name='GPU completion' AND s.name='waitForever' GROUP BY 1,2;
