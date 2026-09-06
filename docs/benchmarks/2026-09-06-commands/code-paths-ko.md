# 명령으로 바꿔도 남는 처리 경로

이번에 설치·빌드한 RN 0.87.1과 Reanimated 4.6.0 소스를 읽어 확인했다. 아래는 **코드 경로의 확인**이며 각 단계의 대기 시간을 계측한 결과는 아니다.

## Android

1. 워클릿의 `dispatchCommand`는 Reanimated의 `ReanimatedModuleProxy::dispatchCommand`에서 RN Scheduler delegate로 전달된다.
2. RN의 `FabricUIManagerBinding::schedulerDidDispatchCommand` → `FabricMountingManager::dispatchCommand` → Java `FabricUIManager.dispatchCommand`를 거친다.
3. Java 쪽은 `MountItemDispatcher.addViewCommandMountItem`으로 명령을 큐에 넣는다. 기능 플래그에 따라 명령 큐 또는 일반 마운트 큐를 쓴다.
4. 큐가 처리될 때 예제 뷰 매니저의 `updateContent` / `updateHue`가 실제 TextView와 장식 뷰를 바꾼다. 이후 화면 그리기는 여전히 Android의 기존 경로다.

따라서 속성 갱신에 필요한 작업 일부를 줄일 수 있어도 **명령 호출 순간 네이티브 반영과 표시까지 모두 끝난다고 볼 수 없다.** 명령 버전에도 큐 대기 가능성이 남는다. 이번 비교에서 큐에 머무른 시간 자체를 직접 분리 측정한 것은 아니므로, 지연의 몇 %가 이 큐 때문이라고 단정하지 않는다.

## iOS

RN의 `RCTSurfacePresenter`는 명령을 `RCTMountingManager`로 전달한다. `dispatchCommand`는 이미 메인 큐라면 동기 호출하고, 아니면 메인 큐로 보낸다. Android와 동일한 명령 큐라고 일반화할 수 없다. UILabel 변경 이후 레이아웃·그리기·화면 표시 비용은 여전히 남는다.

## 기존 속성 경로와 공통 비용

Reanimated의 `performOperations`는 animated props 갱신을 모아 처리하며 빌드 기능 플래그에 따라 동기 갱신과 커밋 경로가 달라진다. 이번 변경은 글자·장식 값 전달만 비교했다. 배경색과 풀 배치 갱신, 행 계산, UI 데이터 보관, TextView/UILabel 그리기와 OS 화면 합성은 없애지 않았다.

세 경로 모두 이미 UI 워클릿에서 내용을 준비하므로 명령 버전만 JS 점유를 새로 피하게 되는 것도 아니다. **전체 비용 가운데 바꾼 부분이 작을 수 있다는 가설**과 측정 차이가 작다는 결과는 부합하지만, 그것만으로 병목 하나를 확정할 수는 없다.

## 확인한 파일

- `apps/example/node_modules/react-native-reanimated/Common/cpp/reanimated/NativeModules/ReanimatedModuleProxy.cpp`: `performOperations`, `dispatchCommand`
- `node_modules/react-native/ReactAndroid/src/main/jni/react/fabric/FabricUIManagerBinding.cpp`: `schedulerDidDispatchCommand`
- `node_modules/react-native/ReactAndroid/src/main/jni/react/fabric/FabricMountingManager.cpp`: `dispatchCommand`
- `node_modules/react-native/ReactAndroid/src/main/java/com/facebook/react/fabric/FabricUIManager.java`: 문자열 `dispatchCommand`
- `node_modules/react-native/ReactAndroid/src/main/java/com/facebook/react/fabric/mounting/MountItemDispatcher.kt`: `addViewCommandMountItem`
- `node_modules/react-native/React/Fabric/RCTSurfacePresenter.mm`: `schedulerDidDispatchCommand`
- `node_modules/react-native/React/Fabric/Mounting/RCTMountingManager.mm`: `dispatchCommand`

원본 파일의 해시는 [코드 경로 증거](code-paths.json)에 보존했다.
