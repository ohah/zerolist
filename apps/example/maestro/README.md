# 변별 테스트 (Maestro + gfxinfo)

리스트 엔진 성능을 **OS-truth**로 비교한다. RN 의 rAF / animated
scroll driver / jsLag 계측은 모두 측정 무효(관찰자 효과·순환논리·
프레임 부족)였으므로 폐기하고, 앱 **밖에서** 측정한다:

- **Maestro** — 실제 네이티브 플링 제스처(JS 스크롤 아님).
- **adb dumpsys gfxinfo** — OS Choreographer 파이프라인이 직접 잰
  프레임 p50/p90/p95/p99 + jank%. 관찰자 효과 0, JS 막혀도 유효.

## 실행

```bash
# 에뮬레이터/기기 연결 + Release APK 설치 상태에서:
RUNS=3 CELL=complex COUNT=20000 \
  apps/example/maestro/discriminate.sh
```

harness 앱은 `AUTO_MATRIX=false`(정적 UI)여야 한다 — Maestro 가
Seg 버튼을 탭해 엔진/cell/count 를 설정하고 실제 swipe 로 구동한다.

## 해석 규칙 (정직성)

- **에뮬레이터 = 절대치 부풀림 → 상대 순위만 유효**(동일 환경·
  제스처·OS-truth). 절대치/체감은 실기기 필요.
- **p90+ 는 2000ms 히스토그램 상한에 가려질 수 있음** → jank% 와
  p50 을 신뢰 지표로 본다.
- Native/ZeroList③ 는 미포함(Phase B 합류 후 동일 방식으로 비교).
- 엔진당 다회(RUNS) 평균·변동으로 본다. 단일 run 결론 금지.

## 측정 예 (Android 에뮬 Release, complex, n=20000, 실제 플링)

| engine | jank% | p50 |
|---|---|---|
| Legend List | ~35% (최소) | ~25ms |
| FlashList | ~45% | ~23ms (최선) |
| FlatList | ~47% (최악) | ~28ms (최악) |

→ FlatList 일관 최하. 부드러움(jank) 우선 Legend, 평속 우선
FlashList. (에뮬 상대순위 기준)
