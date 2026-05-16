import { TurboModuleRegistry, type TurboModule } from 'react-native';

// 파라미터 `Object` 는 TypedArray 를 뜻한다. Turbo Module codegen 에
// TypedArray 타입이 없어 `Object` 로 받고 C++ 에서 ArrayBuffer 로 푼다.
// 타입 안전한 표면은 zerolist.native.tsx 래퍼가 제공한다.
export interface Spec extends TurboModule {
  multiply(a: number, b: number): number;

  // Int32Array 백킹 메모리를 zero-copy 로 받아 Zig 로 합산.
  sumInt32(buffer: Object): number;

  engineInfo(): string;

  nativeLog(message: string): void;

  // heights: Float32Array, out: Float64Array(n+1) — 누적값 정밀도 때문에 f64.
  buildOffsets(heights: Object, n: number, out: Object): void;

  // offsets/scrolls: Float64Array. k 개 scrollOffset 의 가시범위 인덱스 합.
  visibleChecksum(
    offsets: Object,
    n: number,
    viewport: number,
    scrolls: Object,
    k: number
  ): number;
}

export default TurboModuleRegistry.getEnforcing<Spec>('Zerolist');
