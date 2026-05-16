#pragma once

#include <ZerolistSpecJSI.h>

#include <memory>
#include <string>

namespace facebook::react {

class ZerolistImpl
  : public NativeZerolistCxxSpec<ZerolistImpl> {
public:
  ZerolistImpl(std::shared_ptr<CallInvoker> jsInvoker);

  double multiply(jsi::Runtime& rt, double a, double b);

  // PoC 1단계: JS Int32Array 의 ArrayBuffer 를 zero-copy 로 받아
  // Zig SIMD 엔진으로 합산한 결과를 반환한다.
  double sumInt32(jsi::Runtime& rt, jsi::Object buffer);

  // Zig 엔진/타깃 정보 문자열.
  std::string engineInfo(jsi::Runtime& rt);

  // 검증용: 네이티브 stderr 로 출력.
  void nativeLog(jsi::Runtime& rt, std::string message);

  // Phase A: 가변 높이(Float32) → 누적 오프셋. zero-copy.
  void buildOffsets(jsi::Runtime& rt, jsi::Object heights, double n,
                    jsi::Object out);

  // Phase A: k 개 scrollOffset 의 가시범위 인덱스 합(체크섬). zero-copy.
  double visibleChecksum(jsi::Runtime& rt, jsi::Object offsets, double n,
                         double viewport, jsi::Object scrolls, double k);
};

}
