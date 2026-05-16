#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# ZeroList 렌더링 구간별 측정 — gfxinfo **framestats**(프레임별 나노초
# 파이프라인) + **결정론적 고정 스와이프**(adb input, Maestro 랜덤 X).
#
# 집계 jank% 는 에뮬+호스트 부하 비결정성에 압도(같은 코드 2%↔20%).
# 구간 분해는 "어느 구간이 프레임시간을 지배하느냐" 비율이라 환경
# 노이즈에 훨씬 둔감 + 진단적: JS 엔진은 UI스레드 traversal/draw 가
# JS 공급 대기로 부풀고, 네이티브는 그 구간 ≈0·GPU bound 여야 함
# (= "병목은 JS 스레드" 가설의 OS-truth 직접 검증).
#
# 구간(framestats 컬럼 delta, ms):
#   inputAnim   = PerformTraversalsStart − IntendedVsync
#   measureLay  = DrawStart − PerformTraversalsStart
#   drawRec     = SyncQueued − DrawStart      (UI스레드 디스플레이리스트 기록)
#   sync        = IssueDrawCommandsStart − SyncStart
#   gpu         = FrameCompleted − IssueDrawCommandsStart
#   total       = FrameCompleted − IntendedVsync
# Flags 의 0x1(미드로우/첫프레임) 비트 set 프레임은 제외.
#
# 결정론 입력: 동일 좌표·동일 duration 의 input swipe 를 SWIPES 회.
# framestats 는 최근 ~120프레임만 보관 → SWIPES 작게(기본 6)로 전부 포착.
#
# 사용: ENGINES="flatlist,native,nativepure" RUNS=3 CELL=complex \
#       COUNT=20000 SWIPES=6 ./phasebench.sh
# ⚠ 에뮬 절대 ms 는 부풀림 → 구간 **비율/순위**로 해석. 절대치 실기기.
# ─────────────────────────────────────────────────────────────────────
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ADB="${ADB:-${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb}"
PKG="${PKG:-zerolist.example}"
RUNS="${RUNS:-3}"
CELL="${CELL:-complex}"
COUNT="${COUNT:-20000}"
SWIPES="${SWIPES:-6}"
IFS=',' read -ra ENG <<< "${ENGINES:-flatlist,legend,flashlist,native,nativepure}"

[ -x "$ADB" ] || { echo "adb 없음: $ADB" >&2; exit 1; }
"$ADB" get-state >/dev/null 2>&1 || { echo "기기/에뮬 미연결" >&2; exit 1; }
KNOWN="flatlist legend flashlist native zerolist nativepure"

# framestats PROFILEDATA 블록 → 구간별 median(ms) + frames + jank%(>16.7).
parse_framestats() {
  awk -F, '
    /---PROFILEDATA---/ { blk = !blk; if (blk) hdr=0; next }
    !blk { next }
    hdr==0 {
      for (i=1;i<=NF;i++){ gsub(/^ +| +$/,"",$i); col[$i]=i } hdr=1; next
    }
    {
      f=$col["Flags"]+0; if (f % 2 == 1) next            # 0x1 비트 → 제외
      iv=$col["IntendedVsync"]+0
      pt=$col["PerformTraversalsStart"]+0
      ds=$col["DrawStart"]+0
      sq=$col["SyncQueued"]+0
      ss=$col["SyncStart"]+0
      ic=$col["IssueDrawCommandsStart"]+0
      fc=$col["FrameCompleted"]+0
      if (fc<=iv || pt<iv) next
      n++
      A[n]=(pt-iv)/1e6; M[n]=(ds-pt)/1e6; D[n]=(sq-ds)/1e6
      S[n]=(ic-ss)/1e6; G[n]=(fc-ic)/1e6; T[n]=(fc-iv)/1e6
      if (T[n] > 16.7) jank++
    }
    END {
      if (n==0){ print "0|0|0|0|0|0|0|0"; exit }
      print med(A,n)"|"med(M,n)"|"med(D,n)"|"med(S,n)"|"med(G,n)"|"med(T,n)"|"n"|"int(jank*100/n)
    }
    function med(a,c,  i,b,t){ for(i=1;i<=c;i++)b[i]=a[i];
      for(i=1;i<=c;i++)for(t=i+1;t<=c;t++)if(b[t]<b[i]){x=b[i];b[i]=b[t];b[t]=x}
      return sprintf("%.1f", b[int((c+1)/2)]) }
  '
}

echo "ZeroList 구간별 측정 | cell=$CELL count=$COUNT runs=$RUNS swipes=$SWIPES"
echo "(에뮬: 구간 비율/순위로 해석, 절대 ms 부풀림·NOT device)"
printf '%-11s | %6s %7s %6s %5s %5s | %6s %5s %5s\n' \
  engine inAnim measLay drawRec sync gpu total frm jnk%
echo "----------------------------------------------------------------------"

for E in "${ENG[@]}"; do
  case " $KNOWN " in *" $E "*) ;; *) echo "$E: UNKNOWN"; continue ;; esac
  if [ "$E" = "nativepure" ]; then
    ACT=".NativeBenchActivity"; EXTRA=(--ei count "$COUNT")
  else
    ACT=".SoloActivity"; EXTRA=(--es engine "$E" --ei count "$COUNT" --es cell "$CELL")
  fi
  acc=""
  for r in $(seq 1 "$RUNS"); do
    "$ADB" shell am force-stop "$PKG" >/dev/null 2>&1
    "$ADB" shell am start -n "$PKG/$ACT" "${EXTRA[@]}" >/dev/null 2>&1 || continue
    ok=""
    for _ in $(seq 1 12); do
      sleep 1
      "$ADB" shell dumpsys activity activities 2>/dev/null \
        | grep -E 'mResumedActivity|topResumedActivity' \
        | grep -q "$PKG/$ACT" && { ok=1; break; }
    done
    [ -n "$ok" ] || continue
    sleep 1
    "$ADB" shell dumpsys gfxinfo "$PKG" reset >/dev/null 2>&1
    # 결정론 스크롤: 동일 좌표·duration 고정 스와이프 SWIPES 회.
    for _ in $(seq 1 "$SWIPES"); do
      "$ADB" shell input swipe 540 1500 540 400 300 >/dev/null 2>&1
    done
    sleep 1
    row=$("$ADB" shell dumpsys gfxinfo "$PKG" framestats 2>/dev/null | parse_framestats)
    # per-run 노출 — 재현성을 평균 뒤에 숨기지 않는다(inAnim|...|total|frm).
    echo "  run$r $E: $row"
    acc="$acc$row"$'\n'
  done
  # run 들의 각 구간 평균(결정론이라 안정적이어야).
  echo "$acc" | awk -F'|' 'NF>=8 && $7>0 {for(i=1;i<=8;i++)s[i]+=$i; c++}
    END{ if(!c){print "  (측정 실패)"; exit}
      printf "%-11s | %6.1f %7.1f %6.1f %5.1f %5.1f | %6.1f %5d %4d\n",
      ENG, s[1]/c,s[2]/c,s[3]/c,s[4]/c,s[5]/c, s[6]/c, s[7]/c, s[8]/c }' ENG="$E"
done
