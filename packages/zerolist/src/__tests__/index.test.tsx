import { describe, it, expect, jest } from '@jest/globals';

// index 는 ./zerolist(native TurboModule 래퍼)도 재노출한다. 테스트
// 환경엔 네이티브 바이너리가 없어 getEnforcing 이 throw → 모킹.
jest.mock('../NativeZerolist', () => ({ default: {} }));

import * as pkg from '../index';

// 공개 API 표면이 의도대로 노출되는지(드롭인 소비자 계약).
describe('@ohah/zerolist 공개 표면', () => {
  it('ZeroList 컴포넌트 export (forwardRef exotic)', () => {
    expect(pkg.ZeroList).toBeTruthy();
    expect(['object', 'function']).toContain(typeof pkg.ZeroList);
  });
  it('가상화 엔진 함수 export', () => {
    for (const k of [
      'buildOffsets',
      'computeWindow',
      'computeViewableItems',
      'diffViewable',
      'isEndReached',
      'isViewable',
      'defaultKeyExtractor',
      'groupIntoRows',
      'visibleRange',
    ] as const)
      expect(typeof pkg[k]).toBe('function');
  });
  it('jsRef 레퍼런스 네임스페이스 export', () => {
    expect(typeof pkg.jsRef.buildOffsets).toBe('function');
    expect(typeof pkg.jsRef.upperIndex).toBe('function');
  });
});
