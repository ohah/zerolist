#include "ZerolistImpl.h"

#include "zerolist_engine.h"

#include <cstdio>

#if defined(__ANDROID__)
#include <android/log.h>
#endif

namespace facebook::react {

// ArrayBuffer 또는 TypedArray(.buffer) 에서 jsi::ArrayBuffer 를 꺼낸다.
// data(rt) 는 JS 힙 백킹 메모리를 그대로 가리킨다(zero-copy).
static jsi::ArrayBuffer asArrayBuffer(jsi::Runtime& rt, jsi::Object& obj) {
  if (obj.isArrayBuffer(rt)) {
    return obj.getArrayBuffer(rt);
  }
  if (obj.hasProperty(rt, "buffer")) {
    auto inner = obj.getProperty(rt, "buffer");
    if (inner.isObject() && inner.asObject(rt).isArrayBuffer(rt)) {
      return inner.asObject(rt).getArrayBuffer(rt);
    }
  }
  throw jsi::JSError(rt, "ArrayBuffer 또는 TypedArray 가 필요합니다");
}

ZerolistImpl::ZerolistImpl(
  std::shared_ptr<CallInvoker> jsInvoker
)
  : NativeZerolistCxxSpec(std::move(jsInvoker)) {}

double ZerolistImpl::multiply(
  jsi::Runtime& rt,
  double a,
  double b
) {
  return a * b;
}

double ZerolistImpl::sumInt32(
  jsi::Runtime& rt,
  jsi::Object buffer
) {
  jsi::ArrayBuffer ab = asArrayBuffer(rt, buffer);

  // data(rt) 는 JS 힙 백킹 메모리를 그대로 가리킨다 — 복사 없이
  // 포인터만 Zig 로 넘기는 게 zero-copy 의 핵심.
  uint8_t* data = ab.data(rt);
  size_t byteLength = ab.size(rt);
  size_t elemCount = byteLength / sizeof(int32_t);

  int64_t sum = zl_sum_i32(reinterpret_cast<const int32_t*>(data), elemCount);
  return static_cast<double>(sum);
}

std::string ZerolistImpl::engineInfo(jsi::Runtime& rt) {
  uint8_t buf[128];
  size_t n = zl_engine_info(buf, sizeof(buf));
  return std::string(reinterpret_cast<char*>(buf), n);
}

void ZerolistImpl::nativeLog(jsi::Runtime& rt, std::string message) {
#if defined(__ANDROID__)
  __android_log_print(ANDROID_LOG_INFO, "ZeroList-PoC", "%s", message.c_str());
#else
  fprintf(stderr, "[ZeroList-PoC] %s\n", message.c_str());
  fflush(stderr);
#endif
}

void ZerolistImpl::buildOffsets(
  jsi::Runtime& rt,
  jsi::Object heights,
  double n,
  jsi::Object out
) {
  jsi::ArrayBuffer hb = asArrayBuffer(rt, heights);
  jsi::ArrayBuffer ob = asArrayBuffer(rt, out);
  zl_build_offsets(
    reinterpret_cast<const float*>(hb.data(rt)),
    static_cast<size_t>(n),
    reinterpret_cast<double*>(ob.data(rt)));
}

double ZerolistImpl::visibleChecksum(
  jsi::Runtime& rt,
  jsi::Object offsets,
  double n,
  double viewport,
  jsi::Object scrolls,
  double k
) {
  jsi::ArrayBuffer offb = asArrayBuffer(rt, offsets);
  jsi::ArrayBuffer scb = asArrayBuffer(rt, scrolls);
  int64_t sum = zl_visible_ranges_checksum(
    reinterpret_cast<const double*>(offb.data(rt)),
    static_cast<size_t>(n),
    viewport,
    reinterpret_cast<const double*>(scb.data(rt)),
    static_cast<size_t>(k));
  return static_cast<double>(sum);
}

}
