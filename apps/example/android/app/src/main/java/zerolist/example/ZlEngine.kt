package zerolist.example

import java.nio.ByteBuffer

// ZeroList 네이티브 진입점 — Zig 엔진을 JNI 로 호출.
// 버퍼는 direct ByteBuffer(네이티브 주소 그대로 Zig 로, 복사 없음).
object ZlEngine {
  init {
    System.loadLibrary("zlbridge")
  }

  /** 가변 높이(f32) → 누적 오프셋(f64). 1회성 데이터 준비. */
  external fun buildOffsets(heights: ByteBuffer, n: Int, out: ByteBuffer)

  /** scrollY 의 가시 index 범위를 (first<<32)|last 로 비트팩해 반환.
   *  스크롤마다 네이티브 스레드에서 호출 — 프레임당 JS 0회.
   *  언팩은 firstOf/lastOf 로(비트 레이아웃 정의는 여기 한 곳). */
  external fun visibleRange(
    offsets: ByteBuffer,
    n: Int,
    scrollY: Double,
    viewport: Double,
  ): Long

  /** visibleRange 반환값의 first index. */
  fun firstOf(packed: Long): Int = (packed ushr 32).toInt()

  /** visibleRange 반환값의 last index(exclusive). */
  fun lastOf(packed: Long): Int = packed.toInt()
}
