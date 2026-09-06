# ZeroList

React Native 리스트 라이브러리입니다. 공개 컴포넌트는 `ZeroList` 하나이며, 내부에 네이티브 셀 풀과 ScrollView 기반 호환 경로를 포함합니다. 아직 모든 FlatList 기능의 동등성이나 보편적인 성능 우위를 보장하는 단계는 아닙니다.

## 사용 예시

이 모노레포의 예제 앱은 `@ohah/zerolist`를 워크스페이스 의존성으로 사용합니다.

```tsx
import { ZeroList } from '@ohah/zerolist';
import { Text } from 'react-native';

<ZeroList
  data={items}
  keyExtractor={(item) => String(item.id)}
  renderItem={({ item }) => <Text style={{ height: 100 }}>{item.title}</Text>}
  getItemLayout={(_, index) => ({ length: 100, offset: index * 100, index })}
/>;
```

`data`, `renderItem`, `keyExtractor`, `extraData`와 스크롤 ref를 사용합니다. 사용자가 ZigPool이라는 별도 컴포넌트나 엔진 옵션을 선택하지 않습니다.

## 내부 동작과 현재 범위

- **네이티브 풀:** Android/iOS에서 `getItemLayout`으로 모든 항목의 동일한 양의 정수 높이·연속 좌표가 확인되고 지원하는 속성만 사용한 세로 리스트에 적용합니다. Zig의 가시 범위 계산과 네이티브 슬롯 배치가 동작합니다.
- **호환 경로:** 동적·비균일 높이, 헤더·푸터·구분자, 가로·다중 열, 가시성 콜백, 풀에 연결하지 않은 ScrollView 속성, 웹은 기존 가상화 구현을 사용합니다. `estimatedItemSize`만으로 고정 높이를 가정하지 않습니다.
- **상태:** 준비 창에 남아 있는 항목은 키를 기준으로 슬롯과 React 상태를 보존합니다. 슬롯이 다른 항목을 맡으면 내부 React 트리를 새로 생성해 이전 항목의 상태가 새 항목에 전달되지 않게 합니다. 창 밖으로 제거된 항목의 로컬 상태를 무기한 보관하지 않습니다.

따라서 이전 ZigPool 실험의 전체 React 셀 재사용과 비용이 같지는 않습니다. 기능을 추가해 내부 경로가 전환되면 기존 트리가 다시 생성될 수 있습니다. 데이터의 화면 위치 유지와 FlatList 전체 동작의 완전한 호환성은 아직 추가 작업이 필요합니다.

네이티브 구현과 codegen은 라이브러리 패키지에 포함했습니다. 예제 앱의 별도 ViewManager 등록에 의존하지 않습니다. Android/iOS 앱 빌드는 로컬에서 검증하며, 앱 빌드 CI는 두지 않습니다.

## 검증 자료

- [Android 배치 개선과 호스트 부하 재확인](docs/benchmarks/2026-09-06-android-focus/README.md)

- [통합 구현과 지원 범위](docs/benchmarks/2026-09-06-unified/implementation-ko.md)
- [통합 후 정상 부하 비교](docs/benchmarks/2026-09-06-unified/README.md)
- [이전 비교의 공정성 점검](docs/benchmarks/2026-09-06-fairness/README.md)

## 기여와 라이선스

[기여 안내](CONTRIBUTING.md) · [행동 강령](CODE_OF_CONDUCT.md) · [MIT 라이선스](LICENSE)
