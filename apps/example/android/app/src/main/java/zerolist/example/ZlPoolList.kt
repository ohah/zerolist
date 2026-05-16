package zerolist.example

import android.util.Log
import android.view.MotionEvent
import android.view.VelocityTracker
import android.view.ViewConfiguration
import android.widget.FrameLayout
import android.widget.OverScroller
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.ReactContext
import com.facebook.react.bridge.WritableMap
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.UIManagerHelper
import com.facebook.react.uimanager.ViewGroupManager
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.uimanager.events.Event
import com.facebook.react.viewmanagers.ZlPoolListManagerDelegate
import com.facebook.react.viewmanagers.ZlPoolListManagerInterface
import java.nio.ByteBuffer
import java.nio.DoubleBuffer

// ZeroList③ N3: 네이티브 스레드 Zig 가 JSX 셀 풀을 구동(프레임당 JS 0).
// JS 는 POOL 개 슬롯(JSX, collapsable=false, position:absolute)을 렌더.
// 네이티브가 스크롤/플링 + Zig visibleRange 로 windowStart 산출 후 매
// 프레임 slot s 를 offsets[windowStart+s]-scrollY 에 배치. windowStart
// 가 바뀔 때(경계 횡단)만 onRecycle{start} 1회 발신 → JS 가 슬롯 s
// 내용을 data[start+s] 로 교체(프레임 ≫ 리사이클 빈도).
// PoC 한계: 위치는 네이티브가 즉시, 내용은 JS 비동기 갱신 → 경계
// 횡단 직후 수 프레임 동안 슬롯이 새 위치에 옛 내용을 보일 수 있다.
class ZlPoolListView(ctx: ThemedReactContext) : FrameLayout(ctx) {
  private var count = 0
  private var rowPxF = 0f
  private var builtCount = -1
  private var builtRowPxF = -1f
  private var offsets: ByteBuffer? = null
  private var offD: DoubleBuffer? = null
  private var scrollY = 0
  private var lastStart = -1
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

  private fun buildOffsets() {
    if (count <= 0 || rowPxF <= 0f) return
    if (builtCount == count && builtRowPxF == rowPxF) return
    val o = buildUniformOffsets(count, rowPxF)
    offsets = o
    offD = o.asDoubleBuffer()
    builtCount = count
    builtRowPxF = rowPxF
    scrollY = 0
    lastStart = -1
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

  // 매 프레임(JS 0): Zig 로 가시 first → windowStart, 슬롯 s 를
  // offsets[windowStart+s]-scrollY 에 배치. windowStart 변경 시에만
  // onRecycle 발신(JS 가 슬롯 내용 교체).
  private fun reposition() {
    val d = offD ?: return
    val n = childCount
    if (n == 0) return
    val packed = ZlEngine.visibleRange(
      offsets!!, count, scrollY.toDouble(), height.toDouble(),
    )
    val first = ZlEngine.firstOf(packed)
    // 풀이 데이터 끝을 넘지 않도록 clamp(뷰포트 ≤ 풀 가정).
    val windowStart = first.coerceIn(0, maxOf(0, count - n))
    for (s in 0 until n) {
      getChildAt(s).translationY = (d.get(windowStart + s) - scrollY).toFloat()
    }
    if (windowStart != lastStart) {
      lastStart = windowStart
      emitRecycle(windowStart)
    }
    if (checks < PARITY_SAMPLES) {
      checks++
      Log.i(
        "ZlPool",
        "scrollY=$scrollY start=$windowStart zig=[$first,${
          ZlEngine.lastOf(packed)
        }) pool=$n",
      )
    }
  }

  // codegen 은 C++ ZlPoolListEventEmitter 도 생성하나, 이 PoC 는
  // Java/Kotlin ViewManager + EventDispatcher 경로를 쓴다(별 경로, 무충돌).
  private fun emitRecycle(start: Int) {
    val rc = context as? ReactContext ?: return
    val surfaceId = UIManagerHelper.getSurfaceId(rc)
    UIManagerHelper
      .getEventDispatcher(rc, surfaceId)
      ?.dispatchEvent(RecycleEvent(surfaceId, id, start))
    Log.i("ZlPool", "recycle start=$start")
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

  private class RecycleEvent(
    surfaceId: Int,
    viewId: Int,
    private val start: Int,
  ) : Event<RecycleEvent>(surfaceId, viewId) {
    override fun getEventName() = "topRecycle"
    override fun getEventData(): WritableMap =
      Arguments.createMap().apply { putInt("start", start) }
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

  override fun getExportedCustomDirectEventTypeConstants():
    MutableMap<String, Any> =
    mutableMapOf(
      "topRecycle" to mapOf("registrationName" to "onRecycle"),
    )
}
