//! ZeroList Zig 엔진.
//!
//! JS의 ArrayBuffer 를 복사 없이(zero-copy) 그대로 받아 연산한다.
//! comptime 으로 타깃을 분기해 iOS/Android 단일 소스로 빌드한다.
//! 주의: SIMD(@Vector)는 zl_sum_i32 에만 해당. 가상화 경로
//! (zl_build_offsets / zl_visible_ranges_checksum)는 스칼라다.

const std = @import("std");
const builtin = @import("builtin");

// 정적 라이브러리로 RN(iOS/Android)에 링크되므로, 스택 트레이스를
// 캡처하는 기본 panic 핸들러(std.debug.SelfInfo → dyld 심볼 의존)를
// 끌어오지 않도록 최소 핸들러로 교체한다.
pub const panic = std.debug.FullPanic(struct {
    fn handler(_: []const u8, _: ?usize) noreturn {
        @trap();
    }
}.handler);

/// Int32 버퍼를 SIMD 로 합산한다.
/// ptr: JS Int32Array 의 백킹 메모리 주소 (zero-copy)
/// len: 요소 개수 (바이트 아님)
/// i32 들의 합을 i64 누산기에 모아 오버플로를 방지한다.
export fn zl_sum_i32(ptr: [*]const i32, len: usize) i64 {
    const lanes = 8;
    const I32V = @Vector(lanes, i32);
    const I64V = @Vector(lanes, i64);

    var acc: I64V = @splat(0);
    var i: usize = 0;
    while (i + lanes <= len) : (i += lanes) {
        const chunk: I32V = ptr[i..][0..lanes].*;
        const wide: I64V = @intCast(chunk);
        acc += wide;
    }

    var total: i64 = @reduce(.Add, acc);
    while (i < len) : (i += 1) { // 벡터 폭의 배수가 아닌 꼬리
        total += ptr[i];
    }
    return total;
}

// 가상화 연산 — JS 레퍼런스(src/reference.ts)와 비트수준까지
// 동일한 알고리즘이어야 벤치 비교가 공정하다.

/// 가변 높이(f32) → 누적 오프셋(f64). out 길이는 n+1, out[0]=0,
/// out[i] = heights[0..i] 합 (= item i 의 top y).
/// 누적값은 대용량(>~1.6M 행)에서 f32 정수 정확 한계를 넘으므로
/// 반드시 f64 로 누적·저장한다. JS 의 순차 합(f64)과 비트수준까지
/// 일치시키기 위해 SIMD 재결합 대신 스칼라 순차 누적을 쓴다
/// (build 는 1회성 O(N), 핫패스는 scan).
export fn zl_build_offsets(heights: [*]const f32, n: usize, out: [*]f64) void {
    out[0] = 0;
    var acc: f64 = 0;
    var i: usize = 0;
    while (i < n) : (i += 1) {
        acc += heights[i];
        out[i + 1] = acc;
    }
}

/// offsets(오름차순 f64, 길이 n+1)에서 offsets[idx] <= value 를
/// 만족하는 최대 idx (∈ [0, n]). 이진탐색.
inline fn upperIndex(offsets: [*]const f64, n: usize, value: f64) i32 {
    var lo: usize = 0;
    var hi: usize = n; // 탐색 공간 [0, n]
    while (lo < hi) {
        const mid = lo + (hi - lo + 1) / 2; // mid >= 1 보장
        if (offsets[mid] <= value) {
            lo = mid;
        } else {
            hi = mid - 1;
        }
    }
    return @intCast(lo);
}

/// k 개 scrollOffset 의 [first,last] 가시범위 인덱스 합을 체크섬으로
/// 반환한다(거대 배열 마샬링 회피 + JS 와 일치 검증용).
/// offsets/scrolls 는 zero-copy Float64Array 백킹 메모리.
export fn zl_visible_ranges_checksum(
    offsets: [*]const f64,
    n: usize,
    viewport: f64,
    scrolls: [*]const f64,
    k: usize,
) i64 {
    var sum: i64 = 0;
    var q: usize = 0;
    while (q < k) : (q += 1) {
        const s = scrolls[q];
        const first = upperIndex(offsets, n, s);
        const last = upperIndex(offsets, n, s + viewport);
        sum += first;
        sum += last;
    }
    return sum;
}

/// 엔진/타깃 정보 문자열을 buf 에 채우고 길이를 반환한다.
/// comptime 으로 빌드된 아키텍처/OS 를 박아 넣어 통로가 어느
/// 타깃에서 도는지 런타임에서 바로 확인한다.
export fn zl_engine_info(buf: [*]u8, cap: usize) usize {
    const msg = "ZeroList Zig " ++ builtin.zig_version_string ++
        " [" ++ @tagName(builtin.cpu.arch) ++ "-" ++ @tagName(builtin.os.tag) ++
        "-" ++ @tagName(builtin.abi) ++ "]";
    const n = @min(cap, msg.len);
    @memcpy(buf[0..n], msg[0..n]);
    return n;
}
