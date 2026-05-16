# 변별 테스트 (chrome-free + Maestro + gfxinfo)

리스트 엔진 성능을 **OS-truth**로 비교한다. RN 의 rAF / animated
scroll driver / jsLag 계측은 모두 측정 무효(관찰자 효과·순환논리·
프레임 부족)였고, harness UI 를 띄운 채 측정하면 `dumpsys gfxinfo`
가 프로세스 단위라 harness chrome+RN런타임이 수치를 오염시켰다.
그래서 **측정 대상 엔진만 풀스크린으로 띄우는 chrome-free 루트**
에서, 앱 밖에서 측정한다(태스크 #18):

- **SoloActivity** — `ZLSolo` RN 컴포넌트(단일 엔진만)를 풀스크린.
  engine/count/cell 은 `am start` intent extra → initialProps.
- **NativeBenchActivity** — 맨 RecyclerView(RN 0). 셀 코드는
  SoloActivity 의 Fabric 뷰와 공유(buildNativeList) → 차이는
  RN루트+Fabric mount 뿐.
- **Maestro** — 실제 네이티브 플링 제스처(JS 스크롤 아님).
- **adb dumpsys gfxinfo** — OS 가 직접 잰 프레임 p50/p90/p95/p99 +
  jank%. 관찰자 효과 0, JS 막혀도 유효.

## 실행

```bash
# 에뮬레이터/기기 + Release APK 설치 상태에서:
RUNS=5 CELL=complex COUNT=20000 \
  ENGINES="flatlist,legend,flashlist,native,nativepure" \
  apps/example/maestro/discriminate.sh
```

엔진 토큰: `flatlist|legend|flashlist|native`(=RN 내 Fabric 임베드
네이티브 리스트) `|nativepure`(=맨 RecyclerView, RN 0).
**native vs nativepure 델타 = RN루트+Fabric mount 비용**(깨끗 귀속).

## 해석 규칙 (정직성)

- **에뮬레이터 = 절대치 부풀림 → 상대 순위만 유효**. 절대치/체감은
  실기기 필요.
- **p90+ 는 2000ms 히스토그램 상한에 가려질 수 있음** → jank%/p50
  을 신뢰 지표로.
- **RUNS=2 는 표본부족**(분산≥엔진격차) — 변별엔 ≥5, 단일/2-run
  순위 단정 금지.
- ZeroList③ 합류 시 같은 chrome-free 루트로 동일 비교.
