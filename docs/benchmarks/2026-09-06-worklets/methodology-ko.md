# UI 워클릿 템플릿 실험 방법

## 무엇을 옮겼나

기존 ZigPool은 네이티브가 스크롤 위치와 재활용할 슬롯을 결정한 뒤, RN JS 스레드에 `onRecycle`을 보낸다. JS가 React 셀을 다시 렌더하고, 실제 내용과 같은 매핑을 네이티브에 커밋한다.

이번 PoC는 React가 만든 고정 슬롯과 뷰 구조를 유지하면서, **요청 수신 → 데이터 선택 → 문자열·색상 계산 → 네이티브 속성 갱신**을 UI 워클릿으로 처리한다. 네이티브 풀의 기존 배치 경로는 그대로 사용한다. GPU API 변경은 없다. 별도의 백그라운드 계산 스레드가 아니라 **UI 스레드의 별도 JS 런타임**을 사용하므로, 무거운 계산을 과하게 옮기면 스크롤 자체를 막을 수 있다.

| 비교 대상 | 요청을 받는 곳 | 셀 갱신 | 공통점과 차이 |
|---|---|---|---|
| 기존 ZigPool | RN JS | React 재렌더, RN Text | 현재 일반 React 셀을 쓰는 기준선 |
| JS 수신 템플릿 | RN JS를 거쳐 UI | UI 워클릿, 전용 네이티브 텍스트 | UI 수신 템플릿과 동일한 JSX·데이터·풀·연산 |
| UI 수신 템플릿 | UI 워클릿 직접 수신 | UI 워클릿, 전용 네이티브 텍스트 | JS 수신을 우회하는 효과를 구분하는 대상 |

JS 수신 템플릿도 내용 계산은 UI에서 한다. 따라서 두 템플릿 간 비교가 **요청 수신 경로의 효과**이고, 기존 ZigPool과의 차이에는 React 재렌더 제거와 텍스트 컴포넌트 변경도 포함된다. 기존 ZigPool 대비 수치를 모두 워클릿 수신 효과라고 해석하면 안 된다.

## React 문법과 제약

JSX, View, Image, 고정된 자식 구조는 유지한다. 텍스트는 `TemplateText`로 표현하고, 바뀌는 값은 `useDerivedValue`와 `useAnimatedProps`로 연결한다. 일반 `renderItem`을 다른 스레드에 그대로 실행하는 기능은 아니다.

```tsx
const title = useDerivedValue(() => item.value.title);
<TemplateText value={title} initial={initial.title} kind="title" />
```

- 앱 전용 Solo 측정 PoC로, 공개 라이브러리 API와 기본 엔진은 바꾸지 않았다. 인앱 Run의 React 렌더 횟수 기반 유효성 판정과는 호환되지 않는다.
- 고정 높이의 `simple`, `heavy`만 지원한다. 동적 높이, 임의 React 훅·조건부 자식, 데이터 삽입·삭제·정렬의 원자성, 접근성 제품 품질, 프로그램 스크롤 API는 이번 검증 범위 밖이다.
- 10만 건의 실제 `items`를 shared value로 전달한다. 데이터 전체의 추가 런타임 표현과 메모리 비용을 감수하는 단순한 구현이다. 페이지 단위 전달이나 메모리 최적화는 적용하지 않았다.
- heavy 셀은 두 템플릿 모두 이미지 1개, 문자열 3개, 색상 뷰 64개, 항목별 제곱근 연산 4,000회를 사용한다. 기존 heavy 셀과 동일한 데이터와 연산식을 사용한다.
- 템플릿의 문자열은 Android TextView, iOS UILabel로 표시한다. 기존 RN Text와 글줄 배치·텍스트 처리 비용은 완전히 같지 않다. 두 템플릿끼리는 같은 구현이다.
- 초기 TextInput 방식은 정지 후 옛 문자열이 돌아오는 오류가 있어 폐기했다. iOS 실패 로그 일부를 `ios-textinput-failed-sample.txt`에 보관했다. 이 방식의 수치는 최종 비교에 포함하지 않는다.

## 실행 조건과 계측

RN 0.87.1, Reanimated 4.6.0, Worklets 0.12.1을 고정했다. Android arm64 Release 에뮬레이터와 iOS arm64 Release 시뮬레이터에서 같은 앱 바이너리로 세 엔진을 비교한다. 10만 건, heavy 고정 높이, 한쪽 여유 5행으로 통일했다. 한 실행은 초기 대기 3초, 준비 스와이프 12회, 정량 스와이프 18회로 구성한다. 같은 반복 번호에서 엔진 순서를 섞으며, 플랫폼은 직렬 실행하고 반대쪽 앱은 종료한다.

- **화면 검사:** JS 160ms 점유/40ms 여유. 실제 네이티브 제목, 행 식별자, 화면 위치가 일치하는지와 공백·겹침을 검사한다. 기대값을 접근성 라벨에 써서 통과시키지 않는다. 제목 외 본문·합계·색상의 전 프레임 자동 검증은 하지 않으며, 해당 부분은 별도 화면 확인이다.
- **비용 검사:** 화면 검사를 끄고 평상시와 JS 160ms 점유 조건을 따로 측정한다. CPU는 앱 프로세스 전체의 CPU 시간/벽시계 시간으로, 코어 하나를 100%로 본다. Android는 PSS, iOS는 RSS이며 서로 같은 메모리 지표가 아니다. 종료 시점 사용량이며 시작 시 최고 메모리나 장시간 누수 검사는 아니다.
- **프레임:** Android gfxinfo의 지연 프레임과 iOS CADisplayLink의 지연 콜백을 구분한다. iOS 콜백 지연을 실제 화면 표시 누락 비율이라고 부르지 않는다. UI와 JS 양쪽 렌더링이 포함되는 CPU를 JS CPU만으로 해석하지 않는다.
- **내용 갱신 유효성:** 템플릿은 React render 횟수가 0인 것이 정상이다. 화면 검사의 실제 제목/위치 일치와 스크롤 진행으로 검증한다. 비용 측정은 별도 화면 검사와 함께 해석하며, 0 render를 갱신 실패나 무비용의 증거로 쓰지 않는다. `callbacks=0`도 앱의 재활용 처리 함수 카운터다. Reanimated의 더미 이벤트 리스너와 RN 내부 이벤트 전달까지 없어졌다는 뜻은 아니다. 화면 갱신이 그 JS 처리 완료를 기다리지 않는다는 것이 검증 대상이다.
- **호스트 부하:** 각 실행 전후 프로세스 이름·CPU와 load average를 기록한다. 외부 작업과 호스트 스케줄링 영향을 완전히 통제하지 못했으므로, 비용 수치는 탐색 결과다. 실물 저사양 태블릿의 성능이나 범용 우위를 확정하지 않는다.

공백 면적은 이동 중 각 관측 프레임의 공백에서 2px/pt 오차 허용량을 뺀 비율이다. 잘못된 제목의 비율과는 별개다. 공백 지속 시간은 첫 공백 관측부터 첫 정상 관측까지이며 실제 표시 시간의 정밀 측정은 아니다. 실행별 평균을 다시 평균하며, 최악값은 전체 실행 중 최댓값이다.

`record.py`, `run_group.py`, `run_matrix.py`로 재실행할 수 있다. `run_diagnostics.py`는 단계별 추적, simple 셀, 1만 건 대조를 각 1회씩 추가한다. simple 셀은 높이가 달라 풀 크기도 달라지며, 보조 검사는 주 비교 3회 평균에 섞지 않는다. 기존 결과 경로를 덮어쓰지 않는다. 원시 로그의 `*-measured.log`가 실제 정량 구간이다. 녹화는 정량 측정 종료 후 별도 실행하며 동시 실행 영상이나 프레임 동기 비교가 아니다.

## 참고한 공식 자료

- [Reanimated 호환성 표](https://docs.swmansion.com/react-native-reanimated/docs/guides/compatibility/)
- [UI 이벤트 처리 useEvent](https://docs.swmansion.com/react-native-reanimated/docs/advanced/useEvent/)
- [네이티브 속성 갱신 useAnimatedProps](https://docs.swmansion.com/react-native-reanimated/docs/core/useAnimatedProps/)
- [Margelo WishList](https://github.com/margelo/react-native-wishlist): 보관된 PoC의 템플릿 발상을 참고했다. 해당 패키지를 설치하거나 코드를 가져온 구현은 아니다.
