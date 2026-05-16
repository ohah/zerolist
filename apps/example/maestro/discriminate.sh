#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# ZeroList 변별 테스트 — Maestro(실제 네이티브 플링) + adb gfxinfo(OS-truth).
#
# rAF/animated-driver/jsLag 계측은 전부 측정 무효였음(메모리 참조).
# 이 테스트는 앱 밖에서 OS 가 직접 잰 프레임 통계를 쓴다:
#   1) Maestro prep  : 앱 초기화 + 엔진/cell/count 설정
#   2) gfxinfo reset  : OS 프레임 통계 초기화
#   3) Maestro scroll : 실제 swipe 플링(왕복)
#   4) gfxinfo dump   : 그 구간의 OS p50/p90/p95/p99 + jank%
# 엔진당 RUNS 회 반복해 jank%/p50 평균과 변동을 본다.
#
# ⚠ 한계(불변): 에뮬레이터는 절대치 부풀림 → **상대 순위만 유효**
#   (동일 환경·동일 제스처·OS-truth). p90+ 는 2000ms 히스토그램
#   상한에 가려질 수 있어 jank%/p50 이 신뢰 지표. 절대치/체감은
#   실기기 필요. Native/ZeroList③ 는 미포함(Phase B).
#
# 사용: ENGINES="FlatList,Legend List,FlashList" RUNS=3 CELL=complex \
#       COUNT=20000 ./discriminate.sh
# ─────────────────────────────────────────────────────────────────────
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MAESTRO="${MAESTRO:-$HOME/.maestro/bin/maestro}"
ADB="${ADB:-${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb}"
PKG="${PKG:-zerolist.example}"
RUNS="${RUNS:-3}"
CELL="${CELL:-complex}"
COUNT="${COUNT:-20000}"
IFS=',' read -ra ENG <<< "${ENGINES:-FlatList,Legend List,FlashList}"
[ -z "${JAVA_HOME:-}" ] && command -v mise >/dev/null && export JAVA_HOME="$(mise where java 2>/dev/null)"

[ -x "$MAESTRO" ] || { echo "maestro 없음: $MAESTRO (MAESTRO= 로 지정)" >&2; exit 1; }
[ -x "$ADB" ] || { echo "adb 없음: $ADB (ANDROID_HOME/ADB= 로 지정)" >&2; exit 1; }
"$ADB" get-state >/dev/null 2>&1 || { echo "기기/에뮬 미연결" >&2; exit 1; }

echo "ZeroList 변별 테스트 | cell=$CELL count=$COUNT runs=$RUNS | (에뮬: 상대순위만, NOT device)"
printf '%-14s | %-22s | %s\n' "engine" "jank% (per-run)" "mean jank% / mean p50(ms)"
echo "---------------------------------------------------------------------------"

for E in "${ENG[@]}"; do
  janks=(); p50s=()
  for r in $(seq 1 "$RUNS"); do
    if [ "$E" = "Native" ]; then
      # 순수 네이티브 베이스라인: RN harness 대신 전용 Activity 직접 실행.
      "$ADB" shell am start -n "$PKG/.NativeBenchActivity" >/dev/null 2>&1 \
        || { echo "  run$r NATIVE_FAILED"; continue; }
      sleep 3
      # JS 경로의 visible 게이트와 대칭 — 렌더 전 측정 방지.
      "$ADB" shell dumpsys activity activities 2>/dev/null \
        | grep -q NativeBenchActivity \
        || { echo "  run$r NATIVE_NOT_FG"; continue; }
    else
      "$MAESTRO" test --env ENGINE="$E" --env CELL="$CELL" --env COUNT="$COUNT" \
        "$HERE/prep.yaml" >/dev/null 2>&1 || { echo "  run$r PREP_FAILED"; continue; }
    fi
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
  printf '%-14s | %-22s | jank %s%% / p50 %sms\n' "$E" "$(IFS=,; echo "${janks[*]}")" "$mj" "$mp"
done
