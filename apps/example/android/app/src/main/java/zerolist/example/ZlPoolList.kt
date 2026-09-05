package zerolist.example

import android.util.Log
import android.view.View
import android.view.ViewGroup
import android.view.ViewTreeObserver
import android.widget.TextView
import kotlin.math.roundToInt
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

// React가 내용과 함께 확정한 매핑으로 배치한다. legacyRecycling은 비교용이다.
class ZlPoolListView(ctx: ThemedReactContext) : FrameLayout(ctx) {
  // Solo-only ablation, intentionally not a usable list. Default path unchanged.
  private val freezePosition = ctx.currentActivity?.intent?.getStringExtra("diagnostic") == "freeze-position"
  private val traceEnabled = ctx.currentActivity?.intent?.getBooleanExtra("trace", false) == true
  private val bindingTrace = ctx.currentActivity?.intent?.getStringExtra("diagnostic") == "trace-binding"
  private val tracedRequests = mutableMapOf<String, Int>()
  private var tracedCommitVersion = -1
  private var tracedPlacedVersion = -1
  private fun bindingLog(phase: String, v: Int) {
    if (bindingTrace) Log.i("ZlBinding", "phase=$phase version=$v wall=${System.currentTimeMillis()} nano=${System.nanoTime()}")
  }
  private var positionsInitialized = false
  private var committed = intArrayOf()
  private var overscan = 5
  private var legacyRecycling = false
  private var audit = false
  private var version = 0
  private var auditFrame = 0
  private val beforeDraw = ViewTreeObserver.OnPreDrawListener {
    if (!legacyRecycling && (!freezePosition || !positionsInitialized)) { placeCommitted(); positionsInitialized=true }
    if (bindingTrace && tracedCommitVersion != tracedPlacedVersion) {
      tracedPlacedVersion = tracedCommitVersion
      bindingLog("placed", tracedPlacedVersion)
    }
    if (audit) auditSlots()
    true
  }
  fun setCommittedBinds(value: String?) { if (bindingTrace) { tracedCommitVersion = tracedRequests[value] ?: -1; bindingLog("native_commit", tracedCommitVersion) }; committed = value.orEmpty().split(',').mapNotNull { it.toIntOrNull() }.toIntArray(); invalidate() }
  fun setOverscan(value: Int) { overscan = value.coerceAtLeast(0); lastWindowStart = -1; invalidate() }
  fun setLegacyRecycling(value: Boolean) { legacyRecycling = value; lastWindowStart = -1; invalidate() }
  fun setAudit(value: Boolean) { audit = value }
  override fun onAttachedToWindow() { super.onAttachedToWindow(); viewTreeObserver.addOnPreDrawListener(beforeDraw) }

  private fun placeCommitted() {
    val d = offD ?: return
    for (s in 0 until childCount) {
      val child = getChildAt(s)
      val index = committed.getOrNull(s) ?: -1
      child.visibility = if (index in 0 until count) View.VISIBLE else View.INVISIBLE
      if (index in 0 until count) child.translationY = (d.get(index) - scrollY).toFloat()
    }
  }
  private fun titleIndex(view: View): Int? {
    if (view is TextView) Regex("^#(\\d+)").find(view.text.toString())?.let { return it.groupValues[1].toInt() }
    if (view is ViewGroup) for (i in 0 until view.childCount) titleIndex(view.getChildAt(i))?.let { return it }
    return null
  }
  private fun auditSlots() {
    if (rowPxF <= 0 || height <= 0) return
    var wrong = 0; var visible = 0
    val spans = mutableListOf<Pair<Float, Float>>()
    for (s in 0 until childCount) {
      val child = getChildAt(s)
      val top = child.top + child.translationY
      val bottom = top + child.height
      if (child.visibility != View.VISIBLE || bottom <= 0 || top >= height) continue
      visible++
      val expected = ((top + scrollY) / rowPxF).roundToInt()
      if (titleIndex(child) != expected) wrong++
      spans.add(maxOf(0f, top) to minOf(height.toFloat(), bottom))
    }
    var end = 0f; var covered = 0f; var overlap = 0f
    for ((a,b) in spans.sortedBy { it.first }) { overlap += maxOf(0f, minOf(end,b)-a); covered += maxOf(0f,b-maxOf(end,a)); end=maxOf(end,b) }
    Log.i("ZlAudit", "frame=${++auditFrame} y=$scrollY wrong=$wrong visible=$visible blank=${(height-covered).roundToInt()} overlap=${overlap.roundToInt()} version=$version")
  }
  // 스크롤 표시가 프레임 재개에 미치는 영향을 분리하는 진단 옵션. 기본은 끈다.
  private val showScrollIndicator = ctx.currentActivity?.intent?.getBooleanExtra("scrollIndicator", false) == true
  init { isVerticalScrollBarEnabled = showScrollIndicator; if (showScrollIndicator) setWillNotDraw(false) }
  override fun computeVerticalScrollRange(): Int = offD?.get(count)?.toInt() ?: 0
  override fun computeVerticalScrollOffset(): Int = scrollY
  override fun computeVerticalScrollExtent(): Int = height
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
    positionsInitialized = false
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
    if (!legacyRecycling) invalidate()
    if (showScrollIndicator) awakenScrollBars()
  }

  // 가시 범위와 양방향 여유 범위를 요청한다. 새 요청으로 즉시 이동하지 않고
  // React가 내용을 반영한 committed 매핑을 그리기 직전에 적용한다.
  private fun reposition() {
    if (traceEnabled) android.os.Trace.beginSection("ZL.reposition")
    try { repositionImpl() } finally {
      if (traceEnabled) android.os.Trace.endSection()
    }
  }

  private fun repositionImpl() {
    val d = offD ?: return
    val n = childCount
    if (n == 0) return
    val packed = ZlEngine.visibleRange(
      offsets!!, count, scrollY.toDouble(), height.toDouble(),
    )
    val first = ZlEngine.firstOf(packed)
    // 풀이 데이터 끝을 넘지 않도록 clamp(뷰포트 ≤ 풀 가정).
    val windowStart = (first - overscan).coerceIn(0, maxOf(0, count - n))
    // 위치는 매 프레임 갱신(scrollY 추적). bind 는 windowStart 의
    // 순수 함수라 ring 으로 자기배치.
    if (legacyRecycling && (!freezePosition || !positionsInitialized)) {
      for (s in 0 until n) {
        getChildAt(s).translationY =
          (d.get(ring(s, windowStart, n)) - scrollY).toFloat()
      }
      positionsInitialized = true
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
    version++
    if (bindingTrace) {
      if (tracedRequests.size > 512) tracedRequests.clear()
      tracedRequests[binds] = version
      bindingLog("request", version)
    }
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
      ?.dispatchEvent(RecycleEvent(surfaceId, id, binds, version))
  }

  override fun onLayout(c: Boolean, l: Int, t: Int, r: Int, b: Int) {
    super.onLayout(c, l, t, r, b)
    if (rowPxF > 0) for (slot in 0 until childCount) getChildAt(slot).layout(0, 0, width, rowPxF.roundToInt())
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
    viewTreeObserver.removeOnPreDrawListener(beforeDraw)
    super.onDetachedFromWindow()
  }

  private class RecycleEvent(
    surfaceId: Int,
    viewId: Int,
    private val binds: String,
    private val version: Int,
  ) : Event<RecycleEvent>(surfaceId, viewId) {
    override fun getEventName() = "topRecycle"
    override fun getEventData(): WritableMap =
      Arguments.createMap().apply { putString("binds", binds); putInt("version", version) }
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

  override fun setCommittedBinds(view: ZlPoolListView, value: String?) { view.setCommittedBinds(value) }
  override fun setOverscan(view: ZlPoolListView, value: Int) { view.setOverscan(value) }
  override fun setLegacyRecycling(view: ZlPoolListView, value: Boolean) { view.setLegacyRecycling(value) }
  override fun setAudit(view: ZlPoolListView, value: Boolean) { view.setAudit(value) }

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
