"""Record the host emulator display; check wall time against encoded duration.
Requires Android Emulator console screenrecord, adb, ffprobe and ffmpeg.
Do not run alongside the quantitative benchmark.
"""
import os, pathlib, subprocess, time, json, hashlib
P = pathlib.Path(os.environ.get('OUT', '/tmp/zerolist-videos')).resolve()
P.mkdir(parents=True, exist_ok=True)
RAW = pathlib.Path(os.environ.get('RAW', '/tmp/zerolist-webm')).resolve()
RAW.mkdir(parents=True, exist_ok=True)
base = [os.environ.get('ADB', 'adb'), '-s', os.environ.get('SERIAL', 'emulator-5554')]
count = int(os.environ.get('COUNT', '100000'))
def adb(*a):
    result = subprocess.check_output(base + list(a), timeout=40)
    if a[0] == 'emu' and b'KO:' in result:
        raise RuntimeError(result.decode())
    return result
manifest = []
for cell in ['complex', 'heavy']:
    for engine in ['flatlist', 'legend', 'flashlist', 'zigpool']:
        name = cell + '-' + engine
        adb('shell', 'am', 'force-stop', 'zerolist.example')
        adb('shell', 'am', 'start', '-W', '-n', 'zerolist.example/.SoloActivity', '--es', 'engine', engine, '--ei', 'count', str(count), '--es', 'cell', cell)
        time.sleep(4)
        pid = adb('shell', 'pidof', 'zerolist.example').decode().strip()
        log = adb('logcat', '-d', '--pid=' + pid, 'ReactNativeJS:I', '*:S').decode(errors='replace')
        if '[JS0] ' + engine not in log:
            raise RuntimeError('Not ready: ' + name)
        (P / (name + '-before.png')).write_bytes(adb('exec-out', 'screencap', '-p'))
        raw = RAW / (name + '.webm')
        start = time.monotonic()
        adb('emu', 'screenrecord', 'start', '--size', '540x1200', '--fps', '60', '--bit-rate', '4M', '--time-limit', '30', str(raw))
        events = []
        try:
            time.sleep(1.5)
            for y1, y2, dur in [(1800, 600, 500)] * 2 + [(1900, 400, 120)] * 4 + [(500, 1900, 150)] * 3:
                events.append({'t': round(time.monotonic() - start, 3), 'from': [540, y1], 'to': [540, y2], 'duration_ms': dur})
                adb('shell', 'input', 'swipe', '540', str(y1), '540', str(y2), str(dur))
                time.sleep(.45)
            time.sleep(1.5)
        finally:
            elapsed = time.monotonic() - start
            adb('emu', 'screenrecord', 'stop')
        time.sleep(.3)
        duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(raw)]))
        if abs(duration - elapsed) > .3:
            raise RuntimeError(f'Timeline mismatch: {name}: host {elapsed}, video {duration}')
        (P / (name + '-after.png')).write_bytes(adb('exec-out', 'screencap', '-p'))
        manifest.append({'engine': engine, 'cell': cell, 'count': count, 'events': events, 'video': name + '.mp4', 'wall_seconds': round(elapsed, 3), 'source_seconds': duration, 'source_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(), 'note': 'Host emulator capture at requested 60fps; separate run from performance statistics. MP4 transcode keeps source timing. Different scroll physics apply.'})
        (P / 'capture-manifest.json').write_text(json.dumps(manifest, indent=2))
        print('CAPTURED', name, round(elapsed, 3), duration, flush=True)
# Transcode only after all device recordings are finished.
for entry in manifest:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(RAW / pathlib.Path(entry['video']).with_suffix('.webm')), '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough', '-movflags', '+faststart', str(P / entry['video'])], check=True)
