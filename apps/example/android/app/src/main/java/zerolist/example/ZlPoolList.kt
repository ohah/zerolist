package zerolist.example

import android.util.Log
import android.view.MotionEvent
import android.view.VelocityTracker
import android.view.ViewConfiguration
import android.widget.FrameLayout
import android.widget.OverScroller
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.ViewGroupManager
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.viewmanagers.ZlPoolListManagerDelegate
import com.facebook.react.viewmanagers.ZlPoolListManagerInterface
import java.nio.ByteBuffer
import java.nio.DoubleBuffer

// ZeroList③ N2: 네이티브 스크롤 + Zig 가 매 프레임 풀 슬롯 위치 구동.
// JS 는 풀 슬롯(JSX, collapsable=false, position:absolute)을 1회 렌더.
// 스크롤 제스처/플링·가시범위·배치 전부 네이티브(UI 스레드, JS 0):
//   offsets = buildUniformOffsets(zero-copy direct buffer),
//   매 프레임 slot.translationY = offsets[slotIndex] - scrollY,
//   ZlEngine.visibleRange 로 [first,last) 산출(N3 리사이클의 입력).
// N2 = 리사이클 없음: 슬롯 i 는 데이터 인덱스 i 고정(POOL 넘으면 빔).
class ZlPoolListView(ctx: ThemedReactContext) : FrameLayout(ctx) {
  private var count = 0
  private var rowPxF = 0f
  private var builtCount = -1
  private var builtRowPxF = -1f
  private var offsets: ByteBuffer? = null
  private var offD: DoubleBuffer? = null
  private var scrollY = 0
  private val scroller = OverScroller(ctx)
  private var tracker: VelocityTracker? = null
  private val touchSlop = ViewConfiguration.get(ctx).scaledTouchSlop
  private var lastY = 0f
  private var dragging = false
  private var checks = 0

  fun setCount(value: Int) {
    count = value
    buildOffsets()
  }

  fun setRowHeight(dp: Int) {
    rowPxF = dpF(resources.displayMetrics, dp.toFloat())
    buildOffsets()
  }

  // count·rowHeight 둘 다 도착하면 1회 빌드(가드로 중복 방지).
  private fun buildOffsets() {
    if (count <= 0 || rowPxF <= 0f) return
    if (builtCount == count && builtRowPxF == rowPxF) return
    val o = buildUniformOffsets(count, rowPxF)
    offsets = o
    offD = o.asDoubleBuffer()
    builtCount = count
    builtRowPxF = rowPxF
    scrollY = 0
    checks = 0
    requestLayout()
  }

  private fun maxScroll(): Int {
    val d = offD ?: return 0
    return maxOf(0, (d.get(count) - height).toInt())
  }

  private fun setScroll(y: Int) {
    val clamped = y.coerceIn(0, maxScroll())
    if (clamped == scrollY) return
    scrollY = clamped
    reposition()
  }

  // 매 프레임 네이티브 배치(JS 0). 슬롯 i → offsets[i] - scrollY.
  // visibleRange(N3 리사이클 입력)는 진단 표본만 — checks 가드 안에서만
  // 호출해 진단 후 매 프레임 낭비 JNI 를 막는다.
  private fun reposition() {
    val d = offD ?: return
    for (i in 0 until childCount) {
      getChildAt(i).translationY = (d.get(i) - scrollY).toFloat()
    }
    if (checks < PARITY_SAMPLES) {
      checks++
      val packed = ZlEngine.visibleRange(
        offsets!!, count, scrollY.toDouble(), height.toDouble(),
      )
      Log.i(
        "ZlPool",
        "scrollY=$scrollY zig=[${ZlEngine.firstOf(packed)},${
          ZlEngine.lastOf(packed)
        }) children=$childCount maxY=${maxScroll()}",
      )
    }
  }

  override fun onLayout(c: Boolean, l: Int, t: Int, r: Int, b: Int) {
    super.onLayout(c, l, t, r, b)
    reposition()
  }

  override fun onInterceptTouchEvent(e: MotionEvent): Boolean {
    when (e.action) {
      MotionEvent.ACTION_DOWN -> {
        lastY = e.y
        dragging = false
        scroller.forceFinished(true)
      }
      MotionEvent.ACTION_MOVE ->
        if (kotlin.math.abs(e.y - lastY) > touchSlop) dragging = true
    }
    return dragging
  }

  private fun endGesture(fling: Boolean) {
    if (fling) {
      tracker?.computeCurrentVelocity(1000)
      scroller.fling(
        0, scrollY, 0, -(tracker?.yVelocity ?: 0f).toInt(),
        0, 0, 0, maxScroll(),
      )
      postInvalidateOnAnimation()
    }
    tracker?.recycle()
    tracker = null
    dragging = false
  }

  override fun onTouchEvent(e: MotionEvent): Boolean {
    val vt = tracker ?: VelocityTracker.obtain().also { tracker = it }
    vt.addMovement(e)
    when (e.action) {
      MotionEvent.ACTION_DOWN -> lastY = e.y
      MotionEvent.ACTION_MOVE -> {
        setScroll(scrollY + (lastY - e.y).toInt())
        lastY = e.y
      }
      MotionEvent.ACTION_UP -> endGesture(fling = true)
      MotionEvent.ACTION_CANCEL -> endGesture(fling = false)
    }
    return true
  }

  override fun computeScroll() {
    if (scroller.computeScrollOffset()) {
      setScroll(scroller.currY)
      postInvalidateOnAnimation()
    }
  }

  override fun onDetachedFromWindow() {
    scroller.forceFinished(true)
    tracker?.recycle()
    tracker = null
    super.onDetachedFromWindow()
  }

  companion object {
    private const val PARITY_SAMPLES = 8
  }
}

class ZlPoolListManager :
  ViewGroupManager<ZlPoolListView>(),
  ZlPoolListManagerInterface<ZlPoolListView> {

  private val delegate = ZlPoolListManagerDelegate(this)

  override fun getName() = "ZlPoolList"

  override fun createViewInstance(ctx: ThemedReactContext) =
    ZlPoolListView(ctx)

  override fun getDelegate(): ViewManagerDelegate<ZlPoolListView> = delegate

  override fun setCount(view: ZlPoolListView, value: Int) {
    view.setCount(value)
  }

  override fun setRowHeight(view: ZlPoolListView, value: Int) {
    view.setRowHeight(value)
  }
}
