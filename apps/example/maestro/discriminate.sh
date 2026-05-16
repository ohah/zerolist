#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# ZeroList 변별 테스트 — chrome-free 루트 + Maestro 플링 + adb gfxinfo.
#
# rAF/animated-driver/jsLag 계측은 전부 측정 무효였음(메모리 참조).
# 앱 밖에서 OS 가 직접 잰 프레임 통계를 쓰고, 측정 대상 엔진만
# 풀스크린으로 띄워(harness chrome 제거) gfxinfo(프로세스 단위)
# 오염을 없앤다(태스크 #18):
#   1) am start  : SoloActivity(엔진만, intent extra) / NativeBenchActivity
#   2) readiness  : 해당 Activity 가 떴는지 확인(렌더 전 측정 방지)
#   3) gfxinfo reset
#   4) Maestro scroll : 실제 swipe 플링(왕복)
#   5) gfxinfo dump   : 그 구간 OS p50/p90/p95/p99 + jank%
# 엔진당 RUNS 회 반복.
#
# 엔진 토큰: flatlist|legend|flashlist|native(=Fabric 임베드)|
#            nativepure(=맨 RecyclerView Activity, RN 0).
# native vs nativepure 델타 = RN루트+Fabric mount 비용(깨끗 귀속).
#
# ⚠ 한계(불변): 에뮬 절대치 부풀림 → **상대 순위만**. p90+ 는
#   2000ms 히스토그램 상한에 가려질 수 있어 jank%/p50 이 신뢰 지표.
#   절대치/체감은 실기기. RUNS=2 는 표본부족 — 변별엔 ≥5.
#
# 사용: ENGINES="flatlist,legend,flashlist,native,nativepure" \
#       RUNS=5 CELL=complex COUNT=20000 ./discriminate.sh
# ─────────────────────────────────────────────────────────────────────
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MAESTRO="${MAESTRO:-$HOME/.maestro/bin/maestro}"
ADB="${ADB:-${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb}"
PKG="${PKG:-zerolist.example}"
RUNS="${RUNS:-5}"
CELL="${CELL:-complex}"
COUNT="${COUNT:-20000}"
IFS=',' read -ra ENG <<< "${ENGINES:-flatlist,legend,flashlist,native,nativepure}"
[ -z "${JAVA_HOME:-}" ] && command -v mise >/dev/null && export JAVA_HOME="$(mise where java 2>/dev/null)"

[ -x "$MAESTRO" ] || { echo "maestro 없음: $MAESTRO" >&2; exit 1; }
[ -x "$ADB" ] || { echo "adb 없음: $ADB" >&2; exit 1; }
"$ADB" get-state >/dev/null 2>&1 || { echo "기기/에뮬 미연결" >&2; exit 1; }

echo "ZeroList 변별 | cell=$CELL count=$COUNT runs=$RUNS | chrome-free, 에뮬 상대순위만"
printf '%-12s | %-26s | %s\n' "engine" "jank% (per-run)" "mean jank% / p50(ms)"
echo "---------------------------------------------------------------------------"

# Solo 가 모르는 토큰이면 빈 화면 → jank 0 으로 "조용히 통과"하는
# 거짓 결과 방지. 알려진 엔진만 허용.
KNOWN="flatlist legend flashlist native zerolist nativepure"
for E in "${ENG[@]}"; do
  case " $KNOWN " in *" $E "*) ;; *)
    echo "$E: UNKNOWN_ENGINE (허용: $KNOWN)"; continue ;;
  esac
  if [ "$E" = "nativepure" ]; then
    ACT=".NativeBenchActivity"; EXTRA=(--ei count "$COUNT")
  else
    ACT=".SoloActivity"
    EXTRA=(--es engine "$E" --ei count "$COUNT" --es cell "$CELL")
  fi
  janks=(); p50s=()
  for r in $(seq 1 "$RUNS"); do
    "$ADB" shell am force-stop "$PKG" >/dev/null 2>&1
    "$ADB" shell am start -n "$PKG/$ACT" "${EXTRA[@]}" >/dev/null 2>&1 \
      || { echo "  run$r START_FAILED"; continue; }
    # resumed 상태의 정확한 컴포넌트만 인정(stale 기록·콜드스타트
    # 중 측정 방지). RN 콜드스타트 대비 폴링(최대 ~12s).
    ok=""
    for _ in $(seq 1 12); do
      sleep 1
      "$ADB" shell dumpsys activity activities 2>/dev/null \
        | grep -E 'mResumedActivity|topResumedActivity' \
        | grep -q "$PKG/$ACT" && { ok=1; break; }
    done
    [ -n "$ok" ] || { echo "  run$r NOT_FG"; continue; }
    sleep 1 # 첫 프레임 정착
    "$ADB" shell dumpsys gfxinfo "$PKG" reset >/dev/null 2>&1
    "$MAESTRO" test "$HERE/scroll.yaml" >/dev/null 2>&1
    g=$("$ADB" shell dumpsys gfxinfo "$PKG" 2>/dev/null)
    j=$(echo "$g" | grep -m1 'Janky frames' | grep -oE '\([0-9.]+%' | tr -d '(%')
    # "50th percentile: 9ms" → 'ms' 앵커로 "50" 오추출 방지(값만).
    p=$(echo "$g" | grep -m1 '50th' | grep -oE '[0-9]+ms' | grep -oE '[0-9]+')
    janks+=("${j:-NA}"); p50s+=("${p:-NA}")
  done
  mj=$(printf '%s\n' "${janks[@]}" | awk '/^[0-9.]+$/{s+=$1;n++} END{if(n)printf "%.1f",s/n; else print "NA"}')
  mp=$(printf '%s\n' "${p50s[@]}"  | awk '/^[0-9.]+$/{s+=$1;n++} END{if(n)printf "%.0f",s/n; else print "NA"}')
  printf '%-12s | %-26s | jank %s%% / p50 %sms\n' "$E" "$(IFS=,; echo "${janks[*]}")" "$mj" "$mp"
done
