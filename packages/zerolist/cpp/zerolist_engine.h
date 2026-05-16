#pragma once
// Zig 엔진의 C ABI 선언. C++ JSI 브리지는 이 헤더만 보고
// libzerolist_engine.a 와 링크된다 (C-Wrapper 분리 전략).

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Int32 버퍼를 SIMD 로 합산. ptr 은 JS ArrayBuffer 백킹 메모리(zero-copy).
int64_t zl_sum_i32(const int32_t *ptr, size_t len);

// Phase A: 가변 높이(f32) → 누적 오프셋(f64, 길이 n+1).
void zl_build_offsets(const float *heights, size_t n, double *out);

// Phase A: k 개 scrollOffset(f64) 의 가시범위 인덱스 합(체크섬).
int64_t zl_visible_ranges_checksum(const double *offsets, size_t n,
                                   double viewport, const double *scrolls,
                                   size_t k);

// 엔진/타깃 정보를 buf 에 채우고 길이를 반환.
size_t zl_engine_info(uint8_t *buf, size_t cap);

#ifdef __cplusplus
}
#endif
