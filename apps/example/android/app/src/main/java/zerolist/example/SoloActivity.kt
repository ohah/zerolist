package zerolist.example

import com.zerolist.ZlPoolListView

import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.SystemClock
import android.view.FrameMetrics
import android.view.MotionEvent
import android.view.Window
import android.util.Log
import com.facebook.react.ReactActivity
import com.facebook.react.ReactActivityDelegate
import com.facebook.react.defaults.DefaultNewArchitectureEntryPoint.fabricEnabled
import com.facebook.react.defaults.DefaultReactActivityDelegate

// chrome-free 측정용 ReactActivity — "ZLSolo" RN 컴포넌트(단일 엔진만)
// 를 풀스크린으로 띄운다. engine/count/cell 은 adb am start 의 intent
// extra → getLaunchOptions → initialProps 로 전달.
// 예: am start -n PKG/.SoloActivity --es engine flatlist --ei count 20000
class SoloActivity : ReactActivity() {
  // Diagnostic only: preserve drawing cadence across short gaps between gestures.
  // Extra frames consume work/power; this is not enabled in normal operation.
  private var keepAliveUntil = 0L
  private var keepAlivePosted = false
  private val keepAliveFrame = object : Runnable {
    override fun run() {
      if (SystemClock.uptimeMillis() < keepAliveUntil) {
        window.decorView.invalidate()
        window.decorView.postOnAnimation(this)
      } else {
        keepAlivePosted = false
      }
    }
  }
  private var commonProbe: CommonListProbe? = null
  private var motionTarget: android.view.View? = null
  private var motionListener: android.view.ViewTreeObserver.OnPreDrawListener? = null
  private fun findMotionTarget(view: android.view.View): android.view.View? {
    if (view is ZlPoolListView || view is android.widget.ScrollView) return view
    if (view is android.view.ViewGroup) for (i in 0 until view.childCount) findMotionTarget(view.getChildAt(i))?.let { return it }
    return null
  }
  private var frameThread: HandlerThread? = null
  private var frameListener: Window.OnFrameMetricsAvailableListener? = null

  override fun onCreate(savedInstanceState: Bundle?) {
    val startupNs = if (intent.getStringExtra("diagnostic") == "trace-startup") System.nanoTime() else null
    if (startupNs != null) Log.i("ZlStartup", "phase=native_start wall=${System.currentTimeMillis()}")
    super.onCreate(savedInstanceState)
    if (intent.getBooleanExtra("commonAudit", false)) commonProbe = CommonListProbe(window.decorView, intent.getIntExtra("count", 100000), startupNs)
    if (intent.getBooleanExtra("motionTrace", false)) {
      val listener = android.view.ViewTreeObserver.OnPreDrawListener {
        val target = motionTarget ?: findMotionTarget(window.decorView).also { motionTarget = it }
        val y = if (target is ZlPoolListView) target.diagnosticScrollOffset() else target?.scrollY ?: -1
        Log.i("ZlMotion", "phase=predraw nano=${System.nanoTime()} y=$y")
        true
      }
      motionListener = listener
      window.decorView.viewTreeObserver.addOnPreDrawListener(listener)
    }
    if (intent.getBooleanExtra("trace", false)) {
      val thread = HandlerThread("ZLFrameMetrics").also { it.start() }
      frameThread = thread
      val listener = Window.OnFrameMetricsAvailableListener { _, frame, dropped ->
        fun m(id: Int) = frame.getMetric(id)
        Log.i("ZlFrame", "frame intended=${m(FrameMetrics.INTENDED_VSYNC_TIMESTAMP)} vsync=${m(FrameMetrics.VSYNC_TIMESTAMP)} total=${m(FrameMetrics.TOTAL_DURATION)} deadline=${m(FrameMetrics.DEADLINE)} gpu=${m(FrameMetrics.GPU_DURATION)} input=${m(FrameMetrics.INPUT_HANDLING_DURATION)} layout=${m(FrameMetrics.LAYOUT_MEASURE_DURATION)} unknown=${m(FrameMetrics.UNKNOWN_DELAY_DURATION)} draw=${m(FrameMetrics.DRAW_DURATION)} sync=${m(FrameMetrics.SYNC_DURATION)} command=${m(FrameMetrics.COMMAND_ISSUE_DURATION)} swap=${m(FrameMetrics.SWAP_BUFFERS_DURATION)} first=${m(FrameMetrics.FIRST_DRAW_FRAME)} dropped=$dropped")
      }
      frameListener = listener
      window.addOnFrameMetricsAvailableListener(listener, Handler(thread.looper))
    }
  }

  override fun dispatchTouchEvent(event: MotionEvent): Boolean {
    if (intent.getBooleanExtra("keepAlive", false)) {
      keepAliveUntil = SystemClock.uptimeMillis() + 250
      if (!keepAlivePosted) {
        keepAlivePosted = true
        window.decorView.postOnAnimation(keepAliveFrame)
      }
    }
    if (intent.getBooleanExtra("trace", false) &&
        (event.actionMasked == MotionEvent.ACTION_DOWN || event.actionMasked == MotionEvent.ACTION_UP)) {
      Log.i("ZlFrame", "touch action=${event.actionMasked} nano=${System.nanoTime()}")
    }
    return super.dispatchTouchEvent(event)
  }

  override fun onDestroy() {
    motionListener?.let { window.decorView.viewTreeObserver.removeOnPreDrawListener(it) }
    window.decorView.removeCallbacks(keepAliveFrame)
    frameListener?.let { window.removeOnFrameMetricsAvailableListener(it) }
    frameThread?.quitSafely()
    commonProbe?.close()
    super.onDestroy()
  }

  override fun getMainComponentName(): String = "ZLSolo"

  override fun createReactActivityDelegate(): ReactActivityDelegate =
    object : DefaultReactActivityDelegate(this, mainComponentName, fabricEnabled) {
      override fun getLaunchOptions(): Bundle =
        Bundle().apply {
          putInt("bufferRows", intent.getIntExtra("bufferRows", -1))
          putBoolean("commonAudit", intent.getBooleanExtra("commonAudit", false))
          putInt("jsBlockMs", intent.getIntExtra("jsBlockMs", 0))
          putString("preparation", intent.getStringExtra("preparation") ?: "baseline")
          putBoolean("preparationTrace", intent.getBooleanExtra("preparationTrace", false))
          putString("engine", intent.getStringExtra("engine") ?: "flatlist")
          putInt("count", intent.getIntExtra("count", 20_000))
          putString("cell", intent.getStringExtra("cell") ?: "complex")
          putBoolean("legacyRecycling", intent.getBooleanExtra("legacyRecycling", false))
          putBoolean("audit", intent.getBooleanExtra("audit", false))
          putInt("bindingDelayMs", intent.getIntExtra("bindingDelayMs", 0))
          putString("diagnostic", intent.getStringExtra("diagnostic") ?: "normal")
        }
    }
}
