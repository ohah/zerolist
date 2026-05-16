// ZeroList JNI 브리지 — Kotlin(네이티브 스레드) → Zig 엔진.
// direct ByteBuffer 주소를 그대로 Zig 로 넘긴다(per-frame 복사·JS 0).
#include <jni.h>
#include "zerolist_engine.h"

extern "C" {

// 가변 높이(Float32 direct buffer) → 누적 오프셋(Float64 direct buffer).
// 1회성(데이터 준비). per-frame 아님.
JNIEXPORT void JNICALL
Java_zerolist_example_ZlEngine_buildOffsets(JNIEnv *env, jclass,
                                            jobject heights, jint n,
                                            jobject out) {
  auto *h = static_cast<const float *>(env->GetDirectBufferAddress(heights));
  auto *o = static_cast<double *>(env->GetDirectBufferAddress(out));
  if (h && o) zl_build_offsets(h, static_cast<size_t>(n), o);
}

// 한 scrollY 의 가시 index 범위 [first,last) 를 Zig 로 계산.
// 스크롤마다 네이티브 스레드에서 호출(JS 0회). (first<<32)|last 반환.
JNIEXPORT jlong JNICALL
Java_zerolist_example_ZlEngine_visibleRange(JNIEnv *env, jclass,
                                            jobject offsets, jint n,
                                            jdouble scrollY,
                                            jdouble viewport) {
  auto *o = static_cast<const double *>(env->GetDirectBufferAddress(offsets));
  if (!o) return 0;
  int32_t first = 0, last = 0;
  zl_visible_range(o, static_cast<size_t>(n), scrollY, viewport, &first,
                   &last);
  // first/last 는 [0,n] 범위(zl_visible_range 보장)라 음수 불가.
  // 양쪽 모두 uint32 로 캐스팅해 부호확장 없이 jlong 에 비트팩.
  return (static_cast<jlong>(static_cast<uint32_t>(first)) << 32) |
         static_cast<jlong>(static_cast<uint32_t>(last));
}

} // extern "C"
