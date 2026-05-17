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

// ZeroList③ #25: 네이티브 스레드 Zig 가 JSX 셀 풀을 구동(프레임당
// JS 0). 네이티브가 slot↔dataIndex(ring) 의 단일 권위. 매 프레임
// slot s 를 offsets[ring(s,windowStart)]-scrollY 에 자기배치(child
// 순서 무관). windowStart 가 바뀔 때만 binding csv 를 JS 에 하달
// (onRecycle{binds}) → JS 는 그대로 적용(자체 ring 파생 X = #24
// desync 제거). PoC 한계: 위치는 네이티브가 항상 정합하나, 내용은
// JS state 가 ~1 이벤트지연이라 빠른 플링 중 새 위치에 직전 행이
// 잠깐 보일 수 있다(at-rest 는 정합 — #24 영구겹침 해소).
class ZlPoolListView(ctx: ThemedReactContext) : FrameLayout(ctx) {
  private var count = 0
  private var rowPxF = 0f
  private var builtCount = -1
  private var builtRowPxF = -1f
  private var offsets: ByteBuffer? = null
  private var offD: DoubleBuffer? = null
  private var scrollY = 0
  // csv 는 windowStart·n 의 순수 함수 → 이 둘이 안 바뀐 프레임엔
  // 문자열 빌드/emit 를 전부 스킵(translationY 만 갱신).
  private var lastWindowStart = -1
  private var lastN = -1
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
    lastWindowStart = -1
    lastN = -1
    checks = 0
    requestLayout()
  }

  // #25 단일 권위 매핑(reference.ringIndex 와 비트수준 동일 계약):
  // windowStart 1 변할 때 정확히 1 슬롯만 데이터 인덱스 변경.
  private fun ring(slot: Int, w: Int, pool: Int): Int =
    w + (((slot - w) % pool) + pool) % pool

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

  // 매 프레임(JS 0): Zig 로 가시 first → windowStart. 네이티브가
  // binding[s]=ring(s) 의 단일 권위 — 슬롯 s 를 offsets[binding[s]]-
  // scrollY 에 자기배치(committed binding 으로; 매 프레임 새 windowStart
  // 로 앞서가지 않음). binding csv 가 바뀔 때만 그 csv 를 JS 에 하달
  // → JS 는 그대로 적용(자체 파생 X). slot-index 고정 → 재정렬 없음.
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
    // 위치는 매 프레임 갱신(scrollY 추적). bind 는 windowStart 의
    // 순수 함수라 ring 으로 자기배치.
    for (s in 0 until n) {
      getChildAt(s).translationY =
        (d.get(ring(s, windowStart, n)) - scrollY).toFloat()
    }
    // csv·emit 는 windowStart/n 이 바뀐 프레임에만(불변 프레임
    // 문자열 빌드/dispatch 낭비 제거).
    if (windowStart == lastWindowStart && n == lastN) return
    lastWindowStart = windowStart
    lastN = n
    val sb = StringBuilder(n * 5)
    for (s in 0 until n) {
      if (s > 0) sb.append(',')
      sb.append(ring(s, windowStart, n))
    }
    val binds = sb.toString()
    emitRecycle(binds)
    if (checks < RECYCLE_LOG_SAMPLES) {
      checks++
      Log.i("ZlPool", "recycle scrollY=$scrollY binds=$binds")
    }
  }

  // codegen 은 C++ ZlPoolListEventEmitter 도 생성하나, 이 PoC 는
  // Java/Kotlin ViewManager + EventDispatcher 경로를 쓴다(별 경로, 무충돌).
  private fun emitRecycle(binds: String) {
    val rc = context as? ReactContext ?: return
    val surfaceId = UIManagerHelper.getSurfaceId(rc)
    UIManagerHelper
      .getEventDispatcher(rc, surfaceId)
      ?.dispatchEvent(RecycleEvent(surfaceId, id, binds))
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
    private val binds: String,
  ) : Event<RecycleEvent>(surfaceId, viewId) {
    override fun getEventName() = "topRecycle"
    override fun getEventData(): WritableMap =
      Arguments.createMap().apply { putString("binds", binds) }
  }

  companion object {
    private const val RECYCLE_LOG_SAMPLES = 8
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
